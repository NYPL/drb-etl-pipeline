# Digital Research Books ETL Pipeline

![ETL_Pipeline_Tests](https://github.com/NYPL/drb-etl-pipeline/workflows/ETL_Pipeline_Tests/badge.svg)

A containerized python application for importing data from multiple source projects and transforming this data into a unified format that can be accessed via an API (which powers [Digital Research Books Beta](http://digital-research-books-beta.nypl.org/)). The application runs a set of individual processes that can be orchestrated with AWS ECS, Kubernetes, or run as standalone processes.

The overall goal of this project is to provide access to the universe of open source and public domain monographs through a single portal, making it much easier for researchers, students, and others to discover obscure works and newly digitized materials that they may otherwise be unaware of.

## Process Overview

This ETL pipeline operates in several phases to progressively enhance the data that is received from the source projects. This allows us to both normalize data from a wide range of sources (which naturally exists in numerous formats) and to enhance this data in an additive way, presenting the resulting records to users.

The objective is to produce a database of "FRBRized". In these records each source record is represented as an `Item` (something that can actually be read online), which are grouped into `Edition`s (e.g. the 1917 edition of X), which are in turn grouped into `Work`s, (e.g. Moby Dick, or, The Whale). Through this a user can search for and find a single `Work` record and see all editions of that `Work` and all of its options for reading online.

The first step of this work is to gather all source records into the "Dublin Core Data Warehouse (DCDW)". This is a simple data store (currently a flat file in a PostgreSQL database) that normalizes data (from CSVs, MARC records, XML documents and more) into a simple Dublin Core representation. This representation uses the flexibility of DC to allow comparison from these different files while tolerating different formats and missing fields, as all DC fields are optional we can create valid DC records regardless of the source. Using some additional formatting rules (description TK) within each field, we additionally do not lose fidelity from these records.

Once stored in the DCDW these records are used to generate "clustered" work records in the FRBRized BIBFRAME model desrcibed above. This is done by using the source DCDW records as "seed" records to fetch additional metadata from the OCLC catalog, utilizing the OCLC Classify service to initially FRBRize these records and retrieve additional MARC records for the work.

Using these retrieved records, and matched records from the DCDW as a corpus, these records are passed into a relatively simple Machine Learning algorithm to identify which records represent single editions and produce a the data model which is stored in a PostgreSQL database and indexed in ElasticSearch.

## Running the Pipeline

This application is built as a monorepo, which can be built as a single Docker container. This container can be run to execute different processes, which either execute discrete tasks or start a persistent service (such as a Flask API instance). The monorepo structure allows for a high degree of code reuse and makes extending existing services/adding new services easier as they can be based on existing patterns. Many of the modules include abstract base classes that define the mandatory methods for each service.

### Local Development

Locally these services can be run in two modes:

1) As a local docker image, which replicates the deployed version of any component process. This allows for confidence that locally developed code will function properly in the QA and production environments.
2) As individual services on the host machine with local PostgreSQL and ElasticSearch instances. This is the primary mode for developing new services as it allows for instantaneous debugging without the need to rebuild or restart a virtual environment or container image

#### Dependencies and Installation

Local development requires that the following services be available. They do not need to be running locally, but for development purposes this is probably easiest. These should be installed by whatever means is easiest (on macOS this is generally `brew`, or your package manager of choice). These dependencies are:
- PostgreSQL@10
- ElasticSearch@6.8
- RabbitMQ
- Redis

This is a Python application and requires Python >= 3.6. It is recommended that a virtual environment be set up for the application (again use the virtual environment tool of your choice).

The steps to install the application are:

1. Install dependencies, including Python >= 3.6, if not already installed
2. Set up virtual environment
3. Clone this repository
3. Run `pip install -r requirements.txt` from the root directory
4. Configure environment variables per instructions below
5. Run `DevelopmentSetupProcess` per instructions below

#### Running services on host machine

All services share a single entry point in `main.py` file. This script dynamically imports available processes from the `processes` directory and executes the selected process. This script accepts the following arguments (these can also be displayed by running `python main.py --help`)

- `--process` The name of the process to execute. This should be the name of the process class
- `--environment` The environment in which to execute the process. This controls which set of environment variables are loaded from the `config` directory, and should be set to `local` for local development
- `--ingestType` Applicable for processes that fetch records from external sources. Generally three settings are available (see individual processes for their own settings): `daily`, `complete` and `custom`
- `--inputFile` Used with the `custom` ingest setting provides a local file of records to import
- `--startDate` Also used with the `custom` ingest setting, sets a start point for a period to query or ingest records
- `--limit` Limits the total number of rows imported in a single process
- `--offset` Skips the first `n` rows of an import process
- `--singleRecord` Accepts a single record identifier for the current process and imports that record only. Setting this will ignore `ingestType`, `limit` and `offset`.

To set up a local environment there is a special process to initialize a database and search cluster. To set this up run `python main.py --process DevelopmentSetupProcess` which will run a short import process and populate the database with some sample data.

To run the API locally run `python main.py --process APIProcess` which will allow you to query the API at `localhost:5000`

The currently available processes are:

- `DevelopmentSetupProcess` Initialize a testing/development database
- `APIProcess` run the DRB API
- `HathiTrustProcess` Run an import job on HathiTrust records
- `CatalogProcess` Retrieve all OCLC Catalog records for identifiers in the queue
- `ClassifyProcess` Classify (FRBRize) records newly imported into the DCDW
- `ClusterProcess` Group records that have been FRBRized into editions via a Machine Learning algorithm
- `S3Process` Fetch files (e.g. ePubs, cover images, etc.) associated with Item and Edition records and store them in AWS s3
- `NYPLProcess` Fetch files from the NYPL catalog (specifically Bib records) and import them
- `GutenbergProcess` Fetch updated files from Project Gutenberg and import them
- `MUSEProcess` Fetch open access books from Project MUSE and import them
- `DOABProcess` Fetch open access books from the Directory of Open Access Books
- `CoverProcess` Fetch covers for edition records

#### Building and running a process in Docker

To run these processes as a containerized process you must have Docker Desktop installed.

Building the container is a standard process as the container provides an `ENTRYPOINT` that accepts all arguments that can be passed to `main.py`, which control the specific process invoked.

To build the container run the following command from the project root: `docker build -t drb-etl-pipeline .`

This will place an image `drb-etl-pipeline:latest` in your local docker instance. To run a process with the containerized application (in this instance the Flask API) execute the following command: `docker run drb-etl-pipeline -p APIProcess -e YOUR_ENV_FILE`. The `ENTRYPOINT` will accept the same arguments as invoking the process via the CLI.

When running a Docker image locally that interacts with other resources running on `localhost` it is necessary to supply a special URL to access them. Due to this it is generally helpful to define a unique `config` file for local docker testing. You may not wish to commit this file to git as it may contain secrets.

### Managing secrets

To keep sensitive settings out of git, some secrets configuration must be done to run the cluster. To set up for running on your local machine, copy the `config/example.yaml` file and provide the necessary configuration (ask a colleague if you need some of the keys required there). Then provide the name of this file as the `--environment` argument when you run scripts.

Any file that contains sensitive details should not be committed to git. These values can be loaded via the AWS Parameter Store or AWS ECS. Speak to a NYPL engineer for access to these secrets and information on configuring your local setup to use them.

## Deployment

This application is deployed via Github Actions to an ECS cluster. Opening a PR will give a temporary testing/QA environment (the IP address for the environment is added as a comment to the PR), which is torn down on merge. Once merged into QA changes are deployed to [the DRB QA Instance](http://drb-api-qa.nypl.org)

Production deployments are to be made when releases are cut against `main`. 

## TODO

- Improve this README
- ~~Add following data ingest processes:~~
  - ~~NYPL Catalog~~
  - ~~Project Gutenberg~~
  - ~~DOAB~~
  - ~~Project MUSE~~
  - ~~MET Exhibition Catalogs~~
- ~~Add centralized logging process~~
- Add commenting/documentation strings
- ~~Generate C4 diagrams for application~~
- ~~Integrate ePub processor into standard processing flow~~
- ~~Add cover fetching process~~
- Create test suite, including:
  - ~~Unit tests for all components~~
  - Functional tests for each process
  - Integration tests for the full cluster

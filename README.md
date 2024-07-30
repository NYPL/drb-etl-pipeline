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
  - Note that v10 is deprecated.
- ElasticSearch@7.10 
  - Note you may need to follow the [macOS Homebrew install guide](https://www.elastic.co/guide/en/elasticsearch/reference/7.17/brew.html#brew).
- RabbitMQ
- Redis
- XCode Command Line Tools

This is a Python application and requires Python >= 3.6. It is recommended that a virtual environment be set up for the application (again use the virtual environment tool of your choice).  There are several options, but most developers use [venv](https://docs.python.org/3/library/venv.html) or [virtualenv](https://virtualenv.pypa.io/en/latest/installation.html#).

The steps to install the application are:

1. Install dependencies, including Python >= 3.6, if not already installed
2. Set up virtual environment
3. Clone this repository
4. Run `pip install -r requirements.txt` from the root directory.  If you run into the error ```pip: command not found``` while installing the dependencies, you may need to alias python3 and pip3 to python and pip, respectively. 
5. Configure environment variables per instructions below
6. Run `DevelopmentSetupProcess` per instructions below

#### Running services on host machine

It's required to have Docker/Docker Desktop installed locally for setting up a local development environment in this section. Further details on using Docker with this codebase is given in the next section.

All services share a single entry point in `main.py` file. This script dynamically imports available processes from the `processes` directory and executes the selected process. This script accepts the following arguments (these can also be displayed by running `python main.py --help`)

- `--process` The name of the process to execute. This should be the name of the process class
- `--environment` The environment in which to execute the process. This controls which set of environment variables are loaded from the `config` directory, and should be set to `local` for local development
- `--ingestType` Applicable for processes that fetch records from external sources. Generally three settings are available (see individual processes for their own settings): `daily`, `complete` and `custom`
- `--inputFile` Used with the `custom` ingest setting provides a local file of records to import
- `--startDate` Also used with the `custom` ingest setting, sets a start point for a period to query or ingest records
- `--limit` Limits the total number of rows imported in a single process
- `--offset` Skips the first `n` rows of an import process
- `--singleRecord` Accepts a single record identifier for the current process and imports that record only. Setting this will ignore `ingestType`, `limit` and `offset`.

To set up a local environment there is a special process to initialize a database and search cluster which is the `DevelopmentSetupProcess`. However, it's recommended to run the `DevelopmentSetupProcess` and `APIProcess` at the same time to build the most efficient local environment. Before running a command, it's required to set these config variables in the sample-compose.yaml file:

`HATHI_API_KEY`:
`HATHI_API_SECRET`:
`OCLC_API_KEY`:

You can find the values to these variables from the HathiTrust website (https://babel.hathitrust.org/cgi/kgs/request) and OCLC website (https://www.oclc.org/developer/api/keys.en.html) or ask other developers for assistance on attaining these values. Also, the `local-compose.yaml` file referenced in the `docker-compose.yml` file includes other sensitive data such as NYPL API and AWS credentials. If you need these credentials or the whole local-compose.yaml file then you must ask one of the backend developers for this info.

With the configurations set, one of these commands should be run: `make up` or `docker compose up`. These commands will run the docker-compose file in the codebase and this is why it's required to have Docker/Docker Desktop installed locally. After running one of the commands, a short import process will occur and populate the database with some sample data alongside running the API locally. This will allow you to query the API at `localhost:5050` and query the ESC at `localhost:9200`.

The docker compose file uses the sample-compose.yaml file in the `config` directory and additional configurations and dependencies can be added to the file to build upon your local environment.

To run the processes individually the command should be in this format: `python main.py --process APIProcess`.

The currently available processes (with the exception of the UofSC and ChicagoISAC processes) are:

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
- `METProcess` Fetch open access books from The MET Watson Digital Collections and import them
- `DOABProcess` Fetch open access books from the Directory of Open Access Books and import them
- `LOCProcess` Fetch open access and digitized books from the Library of Congress and import them
- `UofMProcess` Fetch open access books from the Univerity of Michigan and import them
- `CoverProcess` Fetch covers for edition records

### Database Migration
The database migration tool Alembic is utilized in this codebase for the Postgresql database. The first step 
is to run this command `alembic revision -m "<revision name>"` which will create a new migration version in the `migrations/versions` directory. Aftwerwards, the `loadEnvFile` method parameters in the `migrations/env.py` file determine which config credentials the database migration will run on. The command to run the database migration is `alembic upgrade head` to run the most recent migration created or `alembic upgrade <name of version migration>` to upgrade to a specific version. To revert the migration, the command `alembic downgrade -1` will undo the last migration upgrade and the command `alembic downgrade <name of version migration>` will revert the database to a specific version. It's highly recommended to run this migration before merging in branches concerning updates to database migration.


#### Appendix Link Flags (All flags are booleans)
- `reader` Added to 'application/webpub+json' links to indicate if a book will have a Read Online function on the frontend
- `embed` Indicates if a book will be using a third party web reader like Hathitrust's web reader on the frontend
- `download` Added to pdf/epub links to indicate if a book is downloadable on the frontend
- `catalog` Indicates if a book is a part of a catalog which may not be readable online, but can be accessed with other means like requesting online 
- `nypl_login` Indicates if a book is a requestable book on the frontend for NYPL patrons
- `fulfill_limited_access` Indicates if a Limited Access book has been encrypted and can be read by NYPL patrons

#### Building and running a process in Docker

To run these processes as a containerized process you must have Docker Desktop installed.

Building the container is a standard process as the container provides an `ENTRYPOINT` that accepts all arguments that can be passed to `main.py`, which control the specific process invoked.

To build the container run the following command from the project root: `docker build -t drb-etl-pipeline .`

This will place an image `drb-etl-pipeline:latest` in your local docker instance. To run a process with the containerized application (in this instance the Flask API) execute the following command: `docker run drb-etl-pipeline -p APIProcess -e YOUR_ENV_FILE`. The `ENTRYPOINT` will accept the same arguments as invoking the process via the CLI.

When running a Docker image locally that interacts with other resources running on `localhost` it is necessary to supply a special URL to access them. Due to this it is generally helpful to define a unique `config` file for local docker testing. You may not wish to commit this file to git as it may contain secrets.

### Testing

To run the unit tests, run `make unit`.

To run the integration tests, run `make integration`.

### Managing secrets

To keep sensitive settings out of git, some secrets configuration must be done to run the cluster. To set up for running on your local machine, copy the `config/example.yaml` file and provide the necessary configuration (ask a colleague if you need some of the keys required there). Then provide the name of this file as the `--environment` argument when you run scripts.

Any file that contains sensitive details should not be committed to git. These values can be loaded via the AWS Parameter Store or AWS ECS. Speak to a NYPL engineer for access to these secrets and information on configuring your local setup to use them.

## Deployment

This application is deployed via Github Actions to an ECS cluster. Once merged into QA changes are deployed to [the DRB QA Instance](http://drb-api-qa.nypl.org)

Production deployments are to be made when releases are cut against `main`.

### Release Process

We use git tags to tag releases and github's release feature to deploy.  The steps are as follows:

  1. Decide on a new version number (assume 0.12.0 for the following steps)
  2. Make sure your local `main` branch is up to date
  3. Update the `CHANGELOG.md` 'unreleased version' header with the current date and new version number, e.g. '2023-04-03 -- v0.12.0'
  4. Commit your change and push straight to `main`: `git push origin main`
  5. Create a new tag and name it after the new version number: `git tag -a v0.12.0`
  6. Push your tag to github: `git push origin v0.12.0`
  7. In github, navigate to the 'Releases' tab and click on 'Draft a new release'
  8. Choose your new tag from the dropdown, set `main` as the target, and name your release after the new version number
     ('v0.12.0')
  9. Add a quick 1-2 sentence summary, make sure 'Set as the latest release' is enabled and hit 'Publish release'
  10. Check the repo's `Actions` tab to observe the progress of the deployment to production
    - Note that the deployment job merely kicks off an ECS service update. To fully verify success, you'll need to check the
      `Deployments` tab for the relevant service / cluster in the ECS console.
  11. Send a quick message to `#researchnow_aka_sfr` in Slack to notify folks of the newest release

And you're done!

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
- Update dependencies

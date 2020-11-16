# Digital Research Books ETL Pipeline

A containerized python application for importing data from multiple source projects and transforming this data into a unified format that can be accessed via an API (which powers [Digital Research Books Beta](http://digital-research-books-beta.nypl.org/)). This service is designed to be run as a Kubernetes cluster, but can be deployed in any containerized environment.

The overall goal of this project is to provide access to the universe of open source and public domain monographs through a single portal, making it much easier for researchers, students, and others to discover obscure works and newly digitized materials that they may otherwise be unaware of.

## Process Overview

This ETL pipeline operates in several phases to progressively enhance the data that is received from the source projects. This allows us to both normalize data from a wide range of sources (which naturally existis in numerous formats) and to enhance this data in an additive way, presenting the resulting records to users.

The objective is to produce a database of "FRBRized". In these records each source record is represented as an `Item` (something that can actually be read online), which are grouped into `Edition`s (e.g. the 1917 edition of X), which are in turn grouped into `Work`s, (e.g. Moby Dick, or, The Whale). Through this a user can search for and find a single `Work` record and see all editions of that `Work` and all of its options for reading online.

The first step of this work is to gather all source records into the "Dublin Core Data Warehouse (DCDW)". This is a simple data store (currently a flat file in a PostgreSQL database) that normalizes data (from CSVs, MARC records, XML documents and more) into a simple Dublin Core representation. This representation uses the flexibility of DC to allow comparison from these different files while tolerating different formats and missing fields, as all DC fields are optional we can create valid DC records regardless of the source. Using some additional formatting rules (description TK) within each field, we additionally do not lose fidelity from these records.

Once stored in the DCDW these records are used to generate "clustered" work records in the FRBRized BIBFRAME model desrcibed above. This is done by using the source DCDW records as "seed" records to fetch additional metadata from the OCLC catalog, utilizing the OCLC Classify service to initially FRBRize these records and retrieve additional MARC records for the work.

Using these retrieved records, and matched records from the DCDW as a corpus, these records are passed into a relatively simple Machine Learning algorithm to identify which records represent single editions and produce a the data model which is stored in a PostgreSQL database and indexed in ElasticSearch.

## Running the Pipeline

This pipeline is configured to be deployed as a Kubernetes cluster, wich all of the necessary processes being included in a single container image, which is then run in different modes to provide the necessary services. This allows for a high degree of code reuse and makes extending existing services/adding new services easier as they can largely be based on existing patterns.

### Local Development

Locally these services can be run in two modes:

1) As a local Kubernetes cluster with temporary postgres and elastic instances. This mode is useful for end-to-end testing and validating new processes
2) As individual services on the host machine with local postgres and elastic instances. This is the primary mode for developing new services as it allows for instantaneous debugging without the need to rebuild or restart a virtual environment or container image

#### Running services on host machine

All services share a single entry point in `dcdw/main.py` file. This script dynamically imports available processes from the `dcdw/processes` directory and executes the selected process. This script accepts the following arguments (these can also be displayed by running `python main.py --help`)

- `--process` The name of the process to execute. This should be the name of the process class
- `--environment` The environment in which to execute the process. This controls which set of environment variables are loaded from the `config` directory, and should be set to `local` for local development
- `--ingestType` Applicable for processes that fetch records from external sources. Generally three settings are available (see individual processes for their own settings): `daily`, `complete` and `custom`
- `--inputFile` Used with the `custom` ingest setting provides a local file of records to import
- `--startDate` Also used with the `custom` ingest setting, sets a start point for a period to query or ingest records

To set up a local environment there is a special process (which is also run when creating a local Kubernetes cluster) to initialize a database and search cluster. To set this up run `python main.py --process DevelopmentSetupProcess` which will run a short import process and populate the database with some sample data.

To run the API locall run `python main.py --process APIProcess` which will allow you to query the API at `localhost:5000`

The currently available processes are:

- `DevelopmentSetupProcess` Initialize a testing/development database
- `APIProcess` run the DRB API
- `HathiTrustProcess` Run an import job on HathiTrust records
- `CatalogProcess` Retrieve all OCLC Catalog records for identifiers in the queue
- `ClassifyProcess` Classify (FRBRize) records newly imported into the DCDW
- `ClusterProcess` Group records that have been FRBRized into editions via a Machine Learning algorithm
- `EpubProcess` Fetch ePub files associated with Item records and store them in AWS s3

#### Starting a local Kubernetes cluster

To run these processes in a local cluster (to simulate a production environment or to test interaction between processes), a local Kubernetes host can be used. This project has used `minikube` so far, but other options exist depending on your platform. This should install the kubernetes CLI client, but if not, `kubectl` will also need to be available

Prior to starting a cluster a few steps must be taken. First, if you are developing locally and want to test changes you've made within the container you'll have to build the container in your local docker repository and configure your local cluster to use local docker images. Second, you may have to configure the cluster host to expose ports to allow API access. If you are using `minikube` you must use a `vm` as a host to allow this functionality (see their documentation for more details).

Once configured the cluster can be initialized by running `kubectl apply -f manifests/development.yaml` which will provision everything necessary and expose the API. To access the API use `kubectl get ingress` which should display an IP address which can be used to access the API.

### Managing secrets

To keep sensitive settings out of git, some secrets configuration must be done to run the cluster. To set up for running on your local machine, copy the `dcdw/config/example.yaml` file and provide the necessary configuration (ask a colleague if you need some of the keys required there). Then provide the name of this file as the `--environment` argument when you run scripts.

To set up a Kubernetes cluster with these secrets copy the `manifests/secrets-example.yaml` file and provide the necessary details. Then run `kubectl apply -f manifests/secrets-ENV.yaml` file for the proper environment, which ensures that containers in the cluster have access to the proper environment variables.

## Deployment

This application can be deployed to any kubernetes cluster with the provided `production.yaml` manifest. However, in production the application does have additional dependencies, specifically external PostgreSQL and ElasticSearch database/index. This is to easy the work of maintaining persistent data instances in production, which is possible within kubernetes but is more complex, especially with the need to maintain and validate backups. These must be configured and placed in the production config file.

## TODO

- Improve this README
- Add following data ingest processes:
  - NYPL Catalog
  - Project Gutenberg
  - DOAB
  - Project MUSE
  - MET Exhibition Catalogs
- Add centralized logging process
- Add commenting/documentation strings
- Generate C4 diagrams for application
- Integrate ePub processor into standard processing flow
- Add cover fetching process
- Create test suite, including:
  - Unit tests for all components
  - Functional tests for each process
  - Integration tests for the full cluster

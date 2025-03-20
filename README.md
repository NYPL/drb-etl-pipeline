# Digital Research Books ETL Pipeline

![ETL_Pipeline_Tests](https://github.com/NYPL/drb-etl-pipeline/workflows/ETL_Pipeline_Tests/badge.svg)

A containerized python application for importing data from multiple source projects and transforming this data into a unified format that can be accessed via an API (which powers [Digital Research Books Beta](http://digital-research-books-beta.nypl.org/)).

## Process Overview

This ETL pipeline transforms data from various sources into a unified "FRBRized" format where:

- `Item`: Something that can be read online (e.g. a specific digital copy)
- `Edition`: A specific published version (e.g. the 1917 edition)
- `Work`: The abstract creative work (e.g. "Moby Dick")

The pipeline:

1. Imports source records into a Dublin Core Data Warehouse (DCDW)
2. Uses OCLC services to enhance and FRBRize the records
3. Groups records into editions using machine learning
4. Makes the data available through an API

## API Endpoints

The DRB API is available at:

- Production: [https://digital-research-books-api.nypl.org/](https://digital-research-books-api.nypl.org/)
- QA: [https://drb-api-qa.nypl.org/](https://drb-api-qa.nypl.org/)

Both endpoints provide Swagger documentation at `/apidocs/`.

## Quickstart Guide

This guide provides step-by-step instructions to get the DRB ETL pipeline running locally. The application uses a hybrid approach where core services (databases, elasticsearch, etc.) run in Docker containers, while the ETL processes themselves can be run either through Docker or directly with Python for more flexibility during development.

### Prerequisites

- Python 3.9 (specified in `.pythonversion`)
- Docker Desktop
- AWS access to the `nypl-digital-dev` account (submit ServiceNow request to DevOps)
- Access to required AWS parameter store secrets - ask a team member

### Setup Steps

1. Clone the repository:

   ```bash
   git clone git@github.com:NYPL/drb-etl-pipeline.git
   cd drb-etl-pipeline
   ```

2. Create and activate a Python virtual environment:

   ```bash
   # Create virtual environment
   python3.9 -m venv venv

   # Activate it (Mac/Linux)
   source venv/bin/activate

   # Or on Windows
   .\venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Configure secrets:

   - Create `config/local-secrets.yaml` with the following (get the link to AWS parameter store from a team member):
     ```yaml
     AWS_SECRET: xxx
     AWS_ACCESS: xxx
     ```

5. Start core services in Docker:

   ```bash
   docker compose up
   ```

   This will start PostgreSQL, Elasticsearch, RabbitMQ, Redis, and the API service.

   Verify the API is running by visiting: http://127.0.0.1:5050/apidocs/

6. Initialize the local development environment:

   ```bash
   python main.py -p LocalDevelopmentSetupProcess -e local
   ```

7. Restart Docker services:

   ```bash
   docker compose up
   ```

8. Seed the database with initial data:
   ```bash
   python main.py -p SeedLocalDataProcess -e local -i daily
   ```

### Verifying Your Setup

To verify your database setup and view the data:

1. Install PGAdmin4 (optional but recommended for database visualization)
2. Add a new server in PGAdmin4 with these settings:

   - Hostname/address: localhost
   - Port: 5432
   - Maintenance database: drb_test_db
   - Username: postgres
   - Password: localpsql

3. Test with a simple query:
   ```sql
   SELECT * FROM works;
   ```

### Understanding the Architecture

The application uses a hybrid approach for local development:

1. **Docker Services**: Core infrastructure (databases, search, message queue) runs in Docker containers via `docker-compose.yml`. This provides a consistent environment and eliminates the need to install these services locally.

2. **ETL Processes**: The actual ETL processes (defined in `processes/__init__.py`) can be run in two ways:
   - Through Docker for production-like environments
   - Directly with Python for local development (`python main.py -p ProcessName -e local`)

This setup allows developers to:

- Maintain a stable core infrastructure through Docker
- Quickly iterate on individual processes without rebuilding containers
- Run specific parts of the pipeline as needed during development

Common processes you might need to run locally:

```bash
# Run the API
python main.py -p APIProcess -e local

# Import HathiTrust records
python main.py -p HathiTrustProcess -e local -i daily

# Run the clustering process
python main.py -p ClusterProcess -e local
```

### Process Flags

When running any process using `python main.py`, the following flags are available:

- `--process`/`-p`: Name of the process to execute (e.g. `APIProcess`, `HathiTrustProcess`)
- `--environment`/`-e`: Environment to run in (`local`, `qa`, `production`). Controls which config file is loaded from the `config` directory
- `--ingestType`/`-i`: For data ingestion processes:
  - `daily`: Regular incremental import
  - `complete`: Full import
  - `custom`: Import from custom source
- `--inputFile`/`-f`: Path to input file when using `custom` ingest type
- `--startDate`/`-s`: Start date for custom period imports
- `--limit`/`-l`: Limit number of records processed
- `--offset`/`-o`: Skip first N records
- `--singleRecord`/`-r`: Process single record by ID (ignores `ingestType`, `limit`, and `offset`)
- `--source`/`-src`: Run against records from a specific source
- `options`: Additional arguments passed as a list

Example commands:

```bash
# Run API in local environment
python main.py -p APIProcess -e local

# Import specific HathiTrust record
python main.py -p HathiTrustProcess -e local -r record_id_123

# Run custom import with limit
python main.py -p NYPLProcess -e local -i custom -f my_records.csv -l 100
```

You can also view all available flags by running:

```bash
python main.py --help
```

## Available Processes

The main processes available in this pipeline are:

Core Setup:

- `LocalDevelopmentSetupProcess`: Initialize development database
- `SeedLocalDataProcess`: Import sample data
- `APIProcess`: Run the DRB API

Data Ingestion:

- `HathiTrustProcess`: Import from HathiTrust
- `NYPLProcess`: Import from NYPL catalog
- `GutenbergProcess`: Import from Project Gutenberg
- `MUSEProcess`: Import from Project MUSE
- `METProcess`: Import from MET Watson Digital Collections
- `DOABProcess`: Import from Directory of Open Access Books
- `LOCProcess`: Import from Library of Congress
- `PublisherBacklistProcess`: Import from Publisher Backlist Project

Processing:

- `CatalogProcess`: Retrieve OCLC Catalog records
- `ClassifyProcess`: FRBRize records
- `ClusterProcess`: Group records into editions
- `S3Process`: Fetch associated files (ePubs, covers)
- `CoverProcess`: Fetch edition covers

## Testing

```bash
# Run unit tests
make unit

# Run integration tests
make integration

# Run functional tests (requires running Docker environment)
make functional
```

## Deployment

This application deploys via Github Actions to AWS ECS:

- QA changes deploy automatically to [DRB QA Instance](http://drb-api-qa.nypl.org)
- Production deploys via releases cut against `main`

### Release Process

1. Create new version branch (e.g. `v0.12.0`)
2. Create PR titled "Release v0.12.0"
3. After approval, squash and merge to main
4. Create Github release:
   - Tag: v0.12.0
   - Target: main
   - Generate notes: `cat <(git log <first-commit>..HEAD --pretty=format:"%h - %s (%an, %ad)" --date=short)`
5. Notify team in #researchnow_aka_sfr Slack channel
6. Monitor deployment in Github Actions and ECS console

## Analytics

Analytics projects are in the [analytics](analytics) folder:

- [University Press Backlist Project](analytics/upress_reporting): Generates Counter 5 reports
  ```bash
  # Example commands
  python3 analytics/upress_reporting/runner.py --start 2024-03-01 --end 2024-03-30
  python3 analytics/upress_reporting/runner.py --year 2025 --quarter Q1
  ```

## Link Flags

Boolean flags used in the API:

- `reader`: Book has Read Online function
- `embed`: Uses third party web reader
- `download`: Book is downloadable
- `catalog`: Book is requestable but not readable online
- `nypl_login`: Requestable by NYPL patrons
- `limited_access`: Limited Access book for NYPL patrons

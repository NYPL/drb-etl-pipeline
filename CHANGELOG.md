# CHANGELOG

## Unreleased version -- v0.13.2
## Added
- Added auxiliary functions to build queries for OCLC search endpoints
- Removed aggregation result print statement
- Created local.yaml file to setup environment variables when running processes locally
- Implemented OCLC other editions call
- Added functionality for locally generating Counter 5 downloads reports to analytics folder
- Readded enter and exit functions to API DB client
- Updated DevelopmentSetUpProcess with database migration method
- Refactored info API
- Refactored links API and added error handling
- Refactored works and editions APIs and added error handling
- Generalized data aggregation within analytics folder
- Updated README release steps
- Added local S3 docker container via localstack
- Added error handling to citation API
- Implemented Counter 5 reporting for view counts
- Added error handling to GET collection endpoints
- Added error handling for utils API
- Added error handling to search API
- Refactored analytics report code
- Added mapping from IP address to country code

## Fixed
- Changed HATHI_DATAFILES outdated link in development, example, and local yaml files 
- Resolved the errors when running the FulfillProcess on a daily and complete ingest time
- Changed HATHI_DATAFILES outdated link in development, example, and local yaml files
- Fixed edition API ID param

## 2024-08-06 -- v0.13.1
## Added
- New analytics folder for University Press project code. Contains methodology for generating Counter 5 reports
- New script to update current UofM manifests with fulfill endpoints to replace pdf/epub urls
- Updated README with appendix and additions to avaliable processes
- New process to add fulfill urls to Limited Access manifests and update fulfill_limited_access flags to True
- Updated README and added more information to installation steps
- Added Rights status to UofM mapping and Rights conditionals to UofM process
- Deprecated datetime.utcnow() method
- Added new field (publisher_project_source) to the records and items data models
- Ran database migration to add publisher_project_source field to records and items tables
- Filled out publisher_project_source field for UofM books
- Added editionID validation to editions API
- Updated README with steps on retrieving local-compose.yaml file and credentials
- Added more logging to proxy API
- Implement call to Worldcat to retrieve OCLC number
- Refactor OCLC Catalog Manager
- Added make integration command
- Upgrade RabbitMQ Docker image to 3.13
- Updated README with steps on running the processes locally

## Fixed
- Resolved the format of fulfill endpoints in UofM manifests
- Added additional logging to the editions endpoint to debug
- Renamed Docker API container name to drb_local_api
- Renamed hosts for services in sample-compose file from docker bucket names to localhost

## 2024-03-21 -- v0.13.0
## Added
- New script to add nypl_login flag to Links objects
- Added nypl_login flags to NYPL and University of Michigan mapping and process
- New APIUtils method to generate a presigned url for S3 actions
- New /fulfill endpoint with ability to check for NYPL login in Bearer authorization header
- Fulfill endpoint returns pre-signed URLs for objects in private buckets when user is logged in
- Change default development port to 5050 due to macOS Monterey and higher occupying port 5000 by default
- Added new University of Michigan process and mapping for ingestion
- New directory for test JSON files that will be ingested
- New script to delete UMP Manifest links from links table
## Fixed
- NYPL records not being added due to SQLAlchemy error
- Bardo CCE API and Hathi DataFiles URL updated
- Deleted Tugboat configuration as Tugboat is no longer used and no longer builds
- Adjusted sorting for item source and media type priority
- Fixed 500 error with search endpoint for filtering by format by adjusting item sorting

## 2023-09-05 version -- v0.12.3
## Removed
- The "*" character is escaped from queries passed to ElasticSearch, limiting wildcard searches
## Fixed
- High volume of wildcard searches should no longer create unrecoverable queues/timeouts

## 2023-08-31 version -- v0.12.2
### Added
- Script to count and return ids of PD Univ of Cali Books from Hathitrust
- Script to delete problem work records from PSQL and ESC
### Fixed
- Publisher location and webpub manifest links for ISAC records
- Upgrade sqlalchemy to fix prod bug

## 2023-07-20 -- v0.12.1
### Added
- Script to delete current duplicate authors/contributors in the PSQL database
- Web scraper script for the Chicago ISAC catalog of publications
- Mapping and process for Chicago ISAC catalog of publications
- Unit tests for Chicago ISAC catalog mapping and process
- Added mapping for Library of Congress collections
- Added process for Library of Congress collections
- Automatic Ingestion for Library of Congress collections
### Fixed
- Modify agentParser method to reduce number of future duplicate agents
- Install `wheel` with pip to fix fasttext build
- Clean web scraped metadata from Chicago ISAC catalog of publications
- Pinned python requirements.txt versions
- Modified conditionals for clustering manager and root url for classification manager
- Eager load collections to avoid queries in loops
- Wrap dev setup DB statements in `sqlalchemy.text`

## 2023-04-03 -- v0.12.0
### Added
- New endpoint to replace collection JSON objects in the API response
- New endpoint to update specific parts of collection JSON objects in the API response
- New endpoint to delete specific editions/works from collection JSON objects in the API response
- Publication rights data object to fetchCollection API response
- Identifier value to publication links of fetchCollection API response
- Add new DB entities for automatic collections
- Add support for 'Most Recent' automatic collection
- Supported ES backed automatic collections
- Add ability to create automatic collections
- Updated OCLC Classify manager with new API key and header
### Fixed
- Close DB sessions after collection reads

## 2023-02-02 -- v0.11.2
### Added
- inCollection property to the work and edition API responses
- Sort and PerPage parameters for collection/uuid endpoint in swagger file
- Updated .gitignore to ignore vim generated `.swp` files and `ctags` file
### Fixed
- drb_local_devSetUp Docker container exiting out due to ES authentication error
- Handle `ConnectTimeout` from OCLC Classify API
- Updated newrelic instrumentation to encompass all background jobs
- Bumped to python 3.9 for CI testing to match production
- Set DEFAULT_COVER_URL for docker environments

## 2022-12-22 -- v0.11.1
### Added
- Format filter parameters for work and edition detail pages
- Updated GET Request for finding single work or edition with filter parameter
### Fixed
- Identifier search for identifiers with special characters work now

## 2022-11-28 -- v0.11.0
### Added
- Docker Compose file to set up local dev environment
- Updated README steps for setting up local dev environment
- Updated search endpoint to add 'identifier' as a keyword
- Identifier type and value as query terms in APIUtils class
- Multi-host configuration for ES connections
- Script to reindex ES records into new ES cluster
- Logstash file for reindexing ES works for new cluster
- Updated links array for collectionFetch endpoint with Read Online link
- Replaced sklearn dependency with scikit-learn dependency
### Fixed
- Updated unit tests for developmentSetup process
- Removed front end configurations from tugboat
- Slack incoming webhook now passes in regression tests
- Improved CI/CD process with all regression tests passing succesfully
- Score for jaro_winkler search changed from 0.9 to 0.85 in agentParser method
- Specified version 0.20.4 of python-levenshtein in requirements file

## 2022-09-07 -- v0.10.6
### Added
- Government document search filter
- Unit tests for government document filter and aggregation
- Script to delete ESC works that don't correspond with works in the PSQL database
- Maintenance script for routine database maintenance processes
### Fixed
- Increased processing speed of govDocES script

## 2022-07-21 -- v0.10.5
### Added
- New script to update past IntechOpen records with new HTML links
- Exposed entire authors object to the edition details page
- Two new scripts to update NYPL catalogs links in Record and Link table
- Updated NYPL mapping and formats in APIUtils with new catalog link
- Script to update past works in ES with the proper boolean value in their is_government_document field
### Fixed
- Added improved error handling around unexpected `media_type` values
- Improve handling of NYPL Catalog records without EDD links
- Future government document works in ES now have 'True' boolean value in their is_government_document field
- Standardized API endpoint to remove trailing slash from `collection` and `search` endpoints

## 2022-06-09 -- v0.10.4
### Added
- Updated format/filter mappings in APIUtils class
- Work title and author info to edition endpoint
- Added intechopen parser
- Updated tests for DOAB Link Manager
### Fixed
- Work title and authors info only show up in edition details endpoint now
- Editions and utils tests updated and fixed
- All toc object url links in ProjectMuse manifests have a query parameter now
- Update DOAB single record import to reflect new OAI-PMH structure
- Deleted extra urls in toc object of Muse manifests
- Read Online links for books from IntechOpen website


## 2022-05-19 -- v0.10.3
### Added
- MagicMock for test_createSearch method in test_api_es.py file
- Getter and setter method for record model
- Script to extract edition number from edition statement for the edition field
- Script to update future records with edition number in the has_version field
- Date created and date modified values visible in API Response for work and search endpoint
- New returnHathiDateFormat method in hathiTrust process module
### Fixed
- ES8 API only counting up to 10,000 search results
- Add bulk retry functionality for ES writes/deletes
- Edition field for some editions now filled
- HathiTrust data import with new date formats
- Hotfix for setter method of record model

## 2022-04-26 -- v0.10.2
### Added
- Python Agent for New Relic Instrumentation
- Infrastructure Agent for New Relic Instrumentation
### Fixed
- Adjusted NR instrumentation for devSetUp and migration process

## 2022-04-12 -- v0.10.1
### Added
- Query parameter to manifest ProjectMuse url links
- Updated muse manager to add query parameter for future muse records
- Updated test_muse_mangager script with query paramater change
### Fixed
- JSON Decoder error for interstitial pages script
- ES 8.x+ timeout configuration and OPDS2 integration
- Simplified constructWebpubManifest script in muse manager

## 2022-04-04 -- v0.10.0
### Added
- Method in sfrRecord manager to check for reasonable publication dates for editions
- Tests for publicationDateCheck method in sfrRecord manager
- Bulk ElasticSearch indexing
- Blueprint for a citation generator
- MLA Citation rules to citation generator
- ElasticSearch 7.10+ language per-field indexing & searching
### Fixed
- Classify Performance improvements
- Improved stability during clustering processes
- Improved development process script
- Improved unit tests for citation generator
- Removed uuid array
- Modified MLA citation rules
- Deduplicated MLA citation generator
- Replaced polyglot with fasttext for language detection

## 2022-01-25 -- v0.9.6
### Fixed
- Improved handling of Project MUSE records
- Merged SFR-1415 branch with old branch
- Tugboat deployment for SFR-1415 branch commmit
- Formatting for pubDateCheck tests methods
- Importing datetime objects in test_sfrRecord manager

## 2021-11-22 -- v0.9.5
### Added
- Tugboat deployments for feature branches
### Fixed
- Improved redirect handling in proxy endpoint

## 2021-10-28 -- v0.9.4
### Fixed
- Updated order of links for new reader

## 2021-10-04 -- v0.9.3
### Added
- ElasticSearch query highlighting

## 2021-10-04 -- v0.9.2
### Added
- Detect file types in s3 process and specify during storage process
- `readerVersion` parameter for `/search`, `/work` and `/edition` endpoints to control media types returned
### Fixed
- Improve clustering stability by improving individual error handling
- Handle relative links from redirects in proxy endpoint
- Add `embed` flag for HTML links
- Extended settings for `utils/proxy` epndoint to be more flexible
- Resolve issue with display of links when filtering by format
- Release stability via distinct production tag

## 2021-09-09 -- v0.9.1
### Fixed
- Improved InternetArchive link parsing
- Improved (more aggressive) clustering

## 2021-08-19 -- v0.9.0
### Added
- Collections model for storing arbitrary collections of editions/works
- /collection endpoints for the creation, retrival and deletion of collection records
- /collection/list epndoint to list all collections in database
- Add Basic Authentication for managing collections
- Update swagger documentation to use current http(s) scheme

## 2021-08-03 -- v0.8.0
### Added
- New endpoint `utils/proxy` to allow for proxying of resources to webreader
- `conformsTo` parameter for Webpub Manifests for identifying PDF resources

## 2021-07-21 -- v0.7.1
### Fixed
- Extended wait time during OCLC Catalog process
- Handled timeout error in ElasticSearch save operation during clustering
- Restricted record types read by the clustering process
- Set max run time for cover process to 12 hours (for API limit purposes)

## 2021-07-12 -- v0.7.0
### Added
- Creation of Webpub Manifests for all ingested ePub files

## 2021-07-01 -- v0.6.6
### Fixed
- Default sorting options
- Added Redis client to `utils/languages` endpoint to resolve error

## 2021-06-24 -- v0.6.5
### Fixed
- Handling of empty result sets from ElasticSearch

## 2021-06-23 -- v0.6.4
### Added
- Added deep paging options for result sets larger than 10,000 records
### Fixed
- Improved ElasticSearch connection in local client
- Fixed VIAF/LCNAF parsing in clustering step

## 2021-06-15 -- v0.6.3
### Fixed
- Order edition records in ascending date order in work detail pages
- Replace author search blocklist with allowlist

## 2021-06-08 -- v0.6.2
### Fixed
- Correct reversed boolean logic with `showAll` filter
- Improve search query parsing for multi-field search and commas
- Replaced author blocklist with allowlist for search queries

## 2021-06-07 -- v0.6.1
### Fixed
- Loading bug for edition detail pages
- Apply `showAll` filter when present in edition detail API requests

## 2021-06-02 -- v0.6.0
### Fixed
- Handling of records without titles in clustering process
- Don't split queries on commas within quotation marks
- Correct path for sorting on `publication_date` in ElasticSearch
- Temporarily block the display of webpub manifests in the API response
- Filter non-matching links when format filter is applied
- Parsing of some Gutenberg and DOAB ePub files on ingest
- Handle missing Gutenberg cover edge case
- Regression in filtering language aggregation buckets
- Enforce Google Books PDF download exclusion
- Add Slack notifications for automation regression tests
- Regression in filtering language aggregation buckets
- Enforce Google Books PDF download exclusion

## 2021-05-11 -- v0.5.7
### Added
- MET Publication Ingest Process
- Per-branch QA deployments on feature branches
### Fixed
- Escape special characters in search queries
- Handle colons in the body of search queries
- Add deadlock handling in `ClusterProcess`
- Scheduled tests-regression.yaml to run every Monday 12 AM EST
- Renamed tests.yaml as "tests-unit.yaml"
- Remove changelog job from tests-regression.yaml
- Fix allure-test command to include correct path
- Remove lingering sessions after query completion


## 2021-04-15 -- v0.5.6
### Added
- Added `date_created` and `date_modified` indexes to the `records` table
- Scheduled tests.yaml to run every Monday 12 AM EST
## Fixed
- Ensure that multiple publishers are read from Records
- Add `work_uuid` to edition responses
- Fix typo in work UUID fetching
- Format `publication_date` in Link endpoint response
- Remove `verify=False` from GET requests
- Handle malformed author and identifiers in DOAB process
- Improved Classification process performance


## 2021-04-12 -- v0.5.5
### Fixed
- Added deadlock handling to batch commit method
- Skip record from classify that have already been processed
- Handle closed channel in rabbitMQ manager
- Move Record status update to standard batch query and prevent stale data
- Handle `None` values in array of author names
- Update DOAB ingest process to consume OAI_DC records

## 2021-04-09 -- v0.5.4
### Fixed
- Typo in edition detail parsing method
- Handle errors in connection to RabbitMQ server on message get and acknowledge
- Handle None values in Record array fields
- Handle expired session error in Edition detail request

## 2021-04-08 --v0.5.3
### Fixed
- Included instance records in edition detail response
- Improved database query performance in the search context

## 2021-04-07 -- v0.5.2
### Fixed
- Convert PDF Manifest class to standard Readium Webpub format
- Handle deadlock errors in PostgreSQL
- Return 400 Bad Request error for invalid query parameters
- Catch edge case error in Google Books cover fetcher

## 2021-04-06 -- v0.5.1
### Added
- Format crosswalk for API filtering and related 400 Invalid request error
### Fixed
- Ensure that covers are present in API responses
- Add `edition_count` to API response
- Handle additional `|` characters in subject headings

## 2021-04-05 -- v0.5.0
### Added
- OPDS2 endpoints and structure
- Graceful handling of 404 errors and 500 database errors
### Fixed
- Handling of ISO-639-2/b language codes
- Insertion of blank values into `rights_date` column
- Handling of `{}` in record identifiers
- Parsing of publication objects to simple year representations in API response
- Preservation of search result sort order after database query
- Resolve bug in single work fetch response
- Handle mis-indexed work issue 500 error

## 2021-03-29 -- v0.4.3
### Fixed
- Extended API handling of multiple query parameters
- Resolved bug in search API response that omitted `formats` facet
- Lowered OCLC Query Limit to match actual 24-limit (400,000)
- Resolved bug with rights data not being stored/processed properly
- Updated paging response to more useful format
- Improve parsing of entity, subject and title data

## 2021-03-25 -- v0.4.2
### Added
- Swagger documentation
### Fixed
- Handle identifiers with commas in record queries and import processes
- Minor bug in handling keyword queries

## 2021-03-19 -- v0.4.1
### Added
- OCLC API Rate Limit Check in Classify Process
- Improved clustering process with more accurate date and title checking
### Fixed
- Update QA Config file
- Removed unecessary SQL queries from record building process
- Updated Queries to be compatible with SQLAlchemy 1.4

## 2021-03-16 -- v0.4.0
### Added
- Link Details endpoint
- Redis cache check for cover process
- Added Ingest Analytics process for output to Smartsheet
- Added GHA deployment step to ECS
### Fixed
- HathiTrust cover process error handling
- Clustering process on very large groups of records
- UTF-8 error in language parsing module
- Unexpected number of elements in date parsing during clustering process

## 2021-03-05 -- v0.3.0
### Added
- Language and Total Record count API endpoints
- Stand-alone Edition detail API endpoint
### Fixed
- Updated API responses to include unique ids for edition, item and link objects
- Added `mediaType` field to link response objects
- Race conditions in OCLC Classify fetching process
- Missing CASCADE constraints on several database tables
- Missing indexes on several database tables
- Fix processing of single record works at the clustering stage

## 2021-02-23 -- v0.2.3
### Fixed
- Update RabbitMQ client to work with credentials, virtual hosts and non-default exchanges
- Update environment variable loading in some managers to handle irrelevant env vars
- Update Gutenberg process to allow invocation without offset and limit settings
- Resolve memory consumption issues in the NYPL, HathiTrust, DOAB and MUSE processes

## 2021-02-09 -- v0.2.2
### Added
- Cover fetcher process from HathiTrust, OpenLibrary, Google Books and Conent Cafe
### Fixed
- Standardized timeout values and handling of related errors in DOAB
- Better handle HTTP redirect `Location` values
- Fix paths to ePub files in s3 (allow for uppercase characters)
- Add handling for DOI paths in DeGruyter DOAB records
- Updated API to serve app on port 80 to work with ECS environment
- Improve logging to reflect debug/info/warning statements in ECS console
- Update ElasticSearch manager to avoid bug in urllib3 with AWS VPC URL
- Update OCLCCatalog link parsing process to exclude invalid links

## 2021-02-01 -- v0.2.1
### Added
- Endpoint at `/` to verify API status
### Fixed
- Update README with progress
- Refactored environment variable configuration to be more understandable
- Fixed bug that could cause collisions in redis cache
- DOAB ePub file ingest error handling and checking
- Fixed handling of `showAll` and standardized for all endpoints
- Removed any snake_case parameters from API

## 2021-01-28 -- v0.2.0
### Added
- Process for ingesting records from the Directory of Open Access Books (DOAB)
- Option for importing single records from ingest sources
- md5 check for records stored in AWS s3
### Fixed
- Added custom error handling at the mapping level for malformed source records
- File chunk size for file streaming to AWS s3
- Token expiration bug in NYPL API manager
- Added `application/epub+xml` media type for ePub XML files to Gutenberg process

## 2021-01-14 -- v0.1.0
### Added
- Mapping for parsing `MARC` records
- Manager for generating PDF manifest files (in JSON-LD)
- Process for ingesting records from Project MUSE
### Fixed
- Fix timeout issues with RabbitMQ during long running processes
- Handle odd record formatting in NYPL MARC records

## 2021-01-06 -- v0.0.5
### Added
- Added multiprocessing to S3FileProcess
- `limit` and `offset` as optional arguments to the main process
- "Exploded" versions of ePub files in S3
### Fixed
- Add ability to define default role for agents in ElasticSearch manager
- Clean up dates as they are processed to remove duplicate values
- Fix regression in API with ElasticSearch aggregation
- Improved error handling in HathiTrust processor

## 2020-12-28 -- v0.0.4
### Added
- Improved Clustering to use Edition data more accurately (e.g. only when present)
- NYPL filter to identify public domain works
- Paging for OCLC Classify to fetch all associated editions
### Fixed
- Resolved bug with `has_part` strings from the `OCLCProcess`
- Resolved several bugs with parsing and clustering of NYPL data
- Removed index on the `Editions.dcdw_uuid` as is it is not used and was too large in some cases
- Resolved DCDW update bug in `ClusterProcess`
- Resolved error in `S3Manager` pertaining to the s3 response object
- Added additional edge case handling in the `SFRRecordManager
- NYPL and HathiTrust date boundary calculation for daily runs
- Author merging in PostgreSQL
- Make PostgreSQL ids available for Elasticserach
- Add rights statements to items
- Add flush call to clustering process to ensure that record ids are present
- Add jaro_winkler algorithm for fuzzy matching author names within work records

## 2020-12-21 -- v0.0.3
### Added
- Ingest process for Project Gutenberg records
- YAML file for QA ECS environment
### Fixed
- Made s3 ingest process more generic to handle cover images

## 2020-12-10 -- v0.0.2
### Added
- Ingest process for NYPL research records
### Fixed
- Classification Service update cycle
- Removed bug affecting persistence of large batches of records
- Improved manner in which records are marked as "classified"

## 2020-11-20 -- v0.0.1
### Added
- Initial Commit of ETL Pipeline


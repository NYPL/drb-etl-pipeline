# CHANGELOG

## unreleased -- v0.2.2
### Fixed
- Standardized timeout values and handling of related errors in DOAB
- Better handle HTTP redirect `Location` values
- Fix paths to ePub files in s3 (allow for uppercase characters)
- Add handling for DOI paths in DeGruyter DOAB records
- Updated API to serve app on port 80 to work with ECS environment
- Improve logging to reflect debug/info/warning statements in ECS console
- Update ElasticSearch manager to avoid bug in urllib3 with AWS VPC URL

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


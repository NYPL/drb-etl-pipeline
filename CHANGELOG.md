# CHANGELOG

## 2020-11-20 -- v0.0.1
### Added
- Initial Commit of ETL Pipeline

## 2020-12-10 -- v0.0.2
### Added
- Ingest process for NYPL research records
### Fixed
- Classification Service update cycle
- Removed bug affecting persistence of large batches of records
- Improved manner in which records are marked as "classified"

## 2020-12-21 -- v0.0.3
### Added
- Ingest process for Project Gutenberg records
- YAML file for QA ECS environment
### Fixed
- Made s3 ingest process more generic to handle cover images

## Unreleased -- v0.0.4
### Added
- Improved Clustering to use Edition data more accurately (e.g. only when present)
- NYPL filter to identify public domain works
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

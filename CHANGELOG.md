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
- NYPL filter to identify public domain works
- Paging for OCLC Classify to fetch all associated editions
### Fixed
- NYPL and HathiTrust date boundary calculation for daily runs
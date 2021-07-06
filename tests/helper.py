import os


class TestHelpers:
    ENV_VARS = {
        'POSTGRES_HOST': 'test_psql_host',
        'POSTGRES_PORT': 'test_psql_port',
        'POSTGRES_USER': 'test_psql_user',
        'POSTGRES_PSWD': 'test_psql_pswd',
        'POSTGRES_NAME': 'test_psql_name',
        'POSTGRES_ADMIN_USER': 'test_psql_admin',
        'POSTGRES_ADMIN_PSWD': 'test_psql_admin_pswd',
        'REDIS_HOST': 'test_redis_host',
        'REDIS_PORT': 'test_redis_port',
        'ELASTICSEARCH_INDEX': 'test_es_index',
        'ELASTICSEARCH_HOST': 'test_es_host',
        'ELASTICSEARCH_PORT': 'test_es_port',
        'ELASTICSEARCH_TIMEOUT': 'test_es_timeout',
        'RABBIT_HOST': 'test_rbmq_host',
        'RABBIT_PORT': 'test_rbmq_port',
        'RABBIT_VIRTUAL_HOST': 'test_rbmq_vhost',
        'RABBIT_EXCHANGE': 'test_exchange',
        'RABBIT_USER': 'test_rbmq_user',
        'RABBIT_PSWD': 'test_rbmq_pswd',
        'OCLC_ROUTING_KEY': 'test_oclc_key',
        'OCLC_QUEUE': 'test_oclc_queue',
        'FILE_ROUTING_KEY': 'test_file_key',
        'FILE_QUEUE': 'test_file_queue',
        'HATHI_DATAFILES': 'test_hathi_url',
        'OCLC_API_KEY': 'test_oclc_key',
        'AWS_ACCESS': 'test_aws_key',
        'AWS_SECRET': 'test_aws_secret',
        'AWS_REGION': 'test_aws_region',
        'FILE_BUCKET': 'test_aws_bucket',
        'NYPL_BIB_HOST': 'test_bib_host',
        'NYPL_BIB_PORT': 'test_bib_port',
        'NYPL_BIB_NAME': 'test_bib_name',
        'NYPL_BIB_USER': 'test_bib_user',
        'NYPL_BIB_PSWD': 'test_bib_pswd',
        'NYPL_LOCATIONS_BY_CODE': 'test_location_url',
        'NYPL_API_CLIENT_ID': 'test_api_client',
        'NYPL_API_CLIENT_SECRET': 'test_api_secret',
        'NYPL_API_CLIENT_TOKEN_URL': 'test_api_token_url',
        'GITHUB_API_KEY': 'test_github_key',
        'GITHUB_API_ROOT': 'test_github_url',
        'BARDO_CCE_API': 'test_cce_url',
        'MUSE_MARC_URL': 'test_muse_url',
        'MUSE_CSV_URL': 'test_muse_csv',
        'DOAB_OAI_URL': 'test_doab_url',
        'SMARTSHEET_API_TOKEN': 'test_smartsheet_token',
        'SMARTSHEET_SHEET_ID': '1000',
        'WEBPUB_CONVERSION_URL': 'test_conversion_url'
    }

    @classmethod
    def setEnvVars(cls):
        for key, value in cls.ENV_VARS.items():
            os.environ[key] = value

    @classmethod
    def clearEnvVars(cls):
        for key in cls.ENV_VARS.keys():
            os.environ[key] = ''

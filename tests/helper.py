import os


class TestHelpers:
    ENV_VARS = {
        'DB_HOST': 'test_psql_host',
        'DB_PORT': 'test_psql_port',
        'DB_USER': 'test_psql_user',
        'DB_PSWD': 'test_psql_pswd',
        'DB_NAME': 'test_psql_name',
        'ADMIN_USER': 'test_psql_admin',
        'ADMIN_PSWD': 'test_psql_admin_pswd',
        'REDIS_HOST': 'test_redis_host',
        'REDIS_PORT': 'test_redis_port',
        'ES_INDEX': 'test_es_index',
        'ES_HOST': 'test_es_host',
        'ES_PORT': 'test_es_port',
        'ES_TIMEOUT': 'test_es_timeout',
        'RABBIT_HOST': 'test_rbmq_host',
        'RABBIT_PORT': 'test_rbmq_port',
        'OCLC_QUEUE': 'test_oclc_queue',
        'FILE_QUEUE': 'test_file_queue',
        'HATHI_DATAFILES': 'test_hathi_url',
        'OCLC_API_KEY': 'test_oclc_key',
        'AWS_ACCESS': 'test_aws_key',
        'AWS_SECRET': 'test_aws_secret',
        'AWS_REGION': 'test_aws_region',
        'FILE_BUCKET': 'test_aws_bucket',
        'BIB_HOST': 'test_bib_host',
        'BIB_PORT': 'test_bib_port',
        'BIB_NAME': 'test_bib_name',
        'BIB_USER': 'test_bib_user',
        'BIB_PSWD': 'test_bib_pswd',
        'NYPL_LOCATIONS_BY_CODE': 'test_location_url',
        'API_CLIENT_ID': 'test_api_client',
        'API_CLIENT_SECRET': 'test_api_secret',
        'API_CLIENT_TOKEN_URL': 'test_api_token_url',
        'GITHUB_API_KEY': 'test_github_key',
        'GITHUB_API_ROOT': 'test_github_url',
        'BARDO_CCE_API': 'test_cce_url'
    }

    @classmethod
    def setEnvVars(cls):
        for key, value in cls.ENV_VARS.items():
            os.environ[key] = value

    @classmethod
    def clearEnvVars(cls):
        for key in cls.ENV_VARS.keys():
            os.environ[key] = ''

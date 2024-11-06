import boto3

PATH_TO_ENV_VAR = {
    ''
}

class SecretsService:
    def __init__(self, region_name='us-east-1', stage='qa'):
        self.stage = stage
        self.prefix = f'drb/{self.stage}'
        self.ssm_client = boto3.client('ssm', region_name=region_name)
    
    def get_secrets(self, with_decryption=True):
        parameters = {}
        next_token = None
        
    
        parameters = self.ssm_client.get_parameters_by_path(
            Path=self.prefix,
            Recursive=True,
            WithDecryption=with_decryption,
            NextToken=next_token
        )

    def get_paths_to_env_variables(self):
        return {
            f'{self.prefix}/postgres/user': 'POSTGRES_USER',
            f'{self.prefix}/posgres/pswd': 'POSTGRES_PSWD',
            f'{self.prefix}/postges/nypl-user': 'NYPL_BIB_USER',
            f'{self.prefix}/postges/nypl-pswd': 'NYPL_BIB_PSWD',
            f'{self.prefix}/rabbit-pswd': 'RABBIT_PSWD',
            f'{self.prefix}/rabbit-user': 'RABBIT_USER',
            f'{self.prefix}/oclc-search-secret': 'OCLC_CLIENT_SECRET',
            f'{self.prefix}/oclc-search-clientid': 'OCLC_CLIENT_ID',
            f'{self.prefix}/oclc-metadata-clientid': 'OCLC_METADATA_ID',
            f'{self.prefix}/oclc-metadata-secret': 'OCLC_METADATA_SECRET',
            f'{self.prefix}/oclc-key': 'OCLC_API_KEY',
            f'{self.prefix}/nypl-api/public-key': 'NYPL_API_CLIENT_PUBLIC_KEY',
            f'{self.prefix}/nypl-api/client-secret': 'NYPL_API_CLIENT_SECRET',
            f'{self.prefix}/nypl-api/client-id': 'NYPL_API_CLIENT_ID',
            f'{self.prefix}/hathitrust/api-secret': 'HATHI_API_SECRET',
            f'{self.prefix}/hathitrust/api-key': 'HATHI_API_KEY',
            f'{self.prefix}/google-books/api-key': 'GOOGLE_BOOKS_KEY',
            f'{self.prefix}/elasticsearch/user': 'ELASTICSEARCH_USER',
            f'{self.prefix}/elasticsearch/pswd': 'ELASTICSEARCH_PSWD',
            f'{self.prefix}/contentcafe/user': 'CONTENT_CAFE_USER',
            f'{self.prefix}/contentcafe/pswd': 'CONTENT_CAFE_PWD',
        }



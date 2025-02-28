from datetime import datetime
from lxml import etree
import os
import re
import requests
import yaml
import time
from typing import Optional, Generator

from constants.get_constants import get_constants
from mappings.gutenberg import GutenbergMapping
from .source_service import SourceService
from logger import create_log

logger = create_log(__name__)


class GutenbergService(SourceService):
    GUTENBERG_NAMESPACES = {
        'dcam': 'http://purl.org/dc/dcam/',
        'dcterms': 'http://purl.org/dc/terms/',
        'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
        'cc': 'http://web.resource.org/cc/',
        'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
        'pgterms': 'http://www.gutenberg.org/2009/pgterms/'
    }

    def __init__(self):
        self.github_api_key = os.environ.get('GITHUB_API_KEY')
        self.github_api_root = 'https://api.github.com/graphql'

        self.constants = get_constants()

        yaml.add_multi_constructor('!', GutenbergService.default_ctor)

    def get_records(
        self,
        full_import: bool=False,
        start_timestamp: Optional[datetime]=None,
        offset: Optional[int]=None,
        limit: Optional[int]=None
    ) -> Generator[GutenbergMapping, None, None]:
        current_position = 0
        page_size = 100

        has_next_page = True
        cursor = None

        while has_next_page:
            repository_data, has_next_page, cursor = self.get_repositories(
                order='ASC' if start_timestamp is None else 'DESC',
                sort_field='CREATED_AT' if start_timestamp is None else 'PUSHED_AT',
                page_size=page_size,
                start_time=start_timestamp,
                cursor=cursor
            )

            current_position += page_size
            if offset and current_position <= offset: 
                continue

            data_files = self.get_data_files_for_respositories(respository_data=repository_data)

            for (rdf_file, yaml_file) in data_files:
                gutenberg_record = GutenbergMapping(rdf_file, self.GUTENBERG_NAMESPACES, self.constants, yaml_file)
                gutenberg_record.applyMapping()

                yield gutenberg_record

            if current_position >= limit: 
                break

    def get_repositories(self, 
        order: str='DESC', 
        sort_field: str='PUSHED_AT', 
        page_size: int=100,
        cursor: Optional[str]=None,
        start_time: Optional[datetime]=None
    ) -> tuple:
        query_order_clauses = f'direction:{order}, field:{sort_field}'
        query_order = 'orderBy:{{{}}}'.format(query_order_clauses)
        query_page_size = f'first:{page_size}'
        query_cursor = 'after:\"{}\"'.format(cursor) if cursor is not None else None
        query_clauses = ', '.join(list(filter(None, [query_order, query_page_size, query_cursor])))
        repository_query = """\
            {{\
                organization(login:\"GITenberg\") {{\
                    repositories({clauses}) {{\
                        pageInfo {{endCursor, hasNextPage}}\
                        nodes {{id, name, pushedAt}}\
                    }}\
                }}\
            }}\
        """.format(clauses=query_clauses)

        repository_response = self.query_graphql(repository_query)
        
        repositories = repository_response.get('data', {}).get('organization', {}).get('repositories', {})
        page_info = repositories.get('pageInfo', {})
        nodes = repositories.get('nodes', [])
        next_page = page_info.get('hasNextPage', False)
        cursor = page_info.get('endCursor', None)

        repository_data = (
            [repo for repo in nodes if datetime.strptime(repo.get('pushedAt'), '%Y-%m-%dT%H:%M:%SZ') > start_time]
            if start_time is not None
            else [repo for repo in nodes]
        )

        return (repository_data, next_page if len(repository_data) > 0 else False, cursor)

    def get_data_files_for_respositories(self, respository_data: list) -> list:
        data_files = []

        for repo in respository_data:
            repo_id = re.search(r'_([0-9]+)$', repo.get('name'))

            if not repo_id: 
                continue

            work_id = repo_id.group(1)
            data_file = self.get_repository_data_files(work_id, repo)

            if data_file:
                data_files.append(data_file)

        return data_files

    def get_repository_data_files(self, work_id: str, repo) -> Optional[tuple]:
        rdf_query = """\
            {{\
                repository(owner:"GITenberg", name:"{name}"){{\
                    rdf: object(expression:"{master}"){{id, ... on Blob {{text}}}}\
                    yaml: object(expression:"master:metadata.yaml"){{id, ... on Blob {{text}}}}\
                }}\
            }}\
        """.format(name=repo.get('name'), master=f'master:pg{work_id}.rdf')

        rdf_response = self.query_graphql(rdf_query)
        
        repository = rdf_response.get('data', {}).get('repository', {})
        rdf_data = repository.get('rdf', {})
        yaml_data = repository.get('yaml', {})

        if rdf_data is None or yaml_data is None:
            return (None, None)
        
        rdf_text = rdf_data.get('text') if rdf_data else None
        yaml_text = yaml_data.get('text') if yaml_data else None

        if rdf_text is None or yaml_data is None:
            return (None, None)
        
        try:
            return (self.parse_rdf(rdfText=rdf_text), self.parse_yaml(yamlText=yaml_text))
        except (TypeError, etree.XMLSyntaxError):
            logger.error(f'Unable to load metadata files for work {work_id}')
            return None

    def parse_rdf(self, rdfText):
        return etree.fromstring(rdfText.encode('utf-8'))

    def parse_yaml(self, yamlText):
        return yaml.full_load(yamlText)

    def query_graphql(self, query):
        try:
            header = { 'Authorization': f'bearer {self.github_api_key}' }
            
            graphql_response = requests.post(self.github_api_root, json={'query': query}, headers=header)

            self.check_rate_limit(graphql_response=graphql_response)
            
            if graphql_response.status_code == 200:
                return graphql_response.json()
            
            raise Exception(f'Unable to execute Gutenberg GraphQL query {query} - status {graphql_response.status_code}')
        except Exception as e:
            logger.exception(f'Failed to query Gutenberg GraphQL API with query {query}')
            raise e
        
    def check_rate_limit(self, graphql_response):
        if int(graphql_response.headers.get('X-RateLimit-Remaining')) == 0:
            reset_at = int(graphql_response.headers.get('X-RateLimit-Reset'))
            wait_duration = max(0, reset_at - int(time.time()))

            if os.environ.get('ENVIRONMENT') in ['qa', 'production']:
                logger.info(f'Waiting {wait_duration} seconds to continue Gutenberg ingest')
                time.sleep(wait_duration)
            else:
                raise Exception('Exceeded GraphQL request limit')

    @staticmethod
    def default_ctor(loader, tag_suffix, node):
        return f'{tag_suffix}{node.value}'

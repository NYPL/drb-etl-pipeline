from datetime import datetime
from lxml import etree
import os
import re
import requests
import yaml

from logger import create_log

logger = create_log(__name__)


class GutenbergManager:
    def __init__(self, repoOrder, repoSortField, startTime, pageSize):
        self.repoOrder = repoOrder or 'DESC'
        self.repoSortField = repoSortField or 'PUSHED_AT'
        self.startTime = startTime or None
        self.pageSize = pageSize or 100
        self.githubAPIKey = os.environ['GITHUB_API_KEY']
        self.githubAPIRoot = 'https://api.github.com/graphql'

        self.cursor = None
        self.repos = []
        self.dataFiles = []

        yaml.add_multi_constructor('!', GutenbergManager.default_ctor)

    def fetchGithubRepoBatch(self):
        queryOrderClauses = 'direction:{}, field:{}'.format(self.repoOrder, self.repoSortField)
        queryOrderStr = 'orderBy:{{{}}}'.format(queryOrderClauses)
        queryPageSize = 'first:{}'.format(self.pageSize)
        queryCursor = 'after:\"{}\"'.format(self.cursor) if self.cursor else None

        queryClauses = ', '.join(list(filter(None, [queryOrderStr, queryPageSize, queryCursor])))

        githubQuery = """\
            {{\
                organization(login:\"GITenberg\") {{\
                    repositories({clauses}) {{\
                        pageInfo {{endCursor, hasNextPage}}\
                        nodes {{id, name, pushedAt}}\
                    }}\
                }}\
            }}\
        """.format(clauses=queryClauses)

        repositoryResponse = self.queryGraphQL(githubQuery)

        repositories = repositoryResponse.get('data', {}).get('organization', {}).get('repositories', {})
        page_info = repositories.get('pageInfo', {})
        nodes = repositories.get('nodes', [])
        next_page = page_info.get('hasNextPage', False)
        self.cursor = page_info.get('endCursor', None)

        if self.startTime:
            self.repos = list(filter(
                lambda x: datetime.strptime(x['pushedAt'], '%Y-%m-%dT%H:%M:%SZ') > self.startTime,
                nodes
            ))
        else:
            self.repos = [r for r in nodes]
        
        if len(self.repos) == 0: next_page = False

        return next_page

    def fetchMetadataFilesForBatch(self):
        for repo in self.repos:
            idMatch = re.search(r'_([0-9]+)$', repo['name'])

            if not idMatch: continue

            workID = idMatch.group(1)
            self.fetchFilesForRecord(workID, repo)

    def fetchFilesForRecord(self, workID, repo):
        rdfQuery = """\
            {{\
                repository(owner:"GITenberg", name:"{name}"){{\
                    rdf: object(expression:"{master}"){{id, ... on Blob {{text}}}}\
                    yaml: object(expression:"master:metadata.yaml"){{id, ... on Blob {{text}}}}\
                }}\
            }}\
        """.format(name=repo['name'], master='master:pg{}.rdf'.format(workID))

        rdfResponse = self.queryGraphQL(rdfQuery)
        repository = rdfResponse.get('data', {}).get('repository', {})
        rdf_data = repository.get('rdf', {})
        yaml_data = repository.get('yaml', {})

        if rdf_data is None or yaml_data is None:
            return
        
        rdf_text = rdf_data.get('text') if rdf_data else None
        yaml_text = yaml_data.get('text') if yaml_data else None

        if rdf_text is None or yaml_data is None:
            return
        
        try:
            self.dataFiles.append((self.parseRDF(rdfText=rdf_text), self.parseYAML(yamlText=yaml_text)))
        except (TypeError, etree.XMLSyntaxError):
            logger.error(f'Unable to load metadata files for work {workID}')

    def parseRDF(self, rdfText):
        return etree.fromstring(rdfText.encode('utf-8'))

    def parseYAML(self, yamlText):
        return yaml.full_load(yamlText)

    def resetBatch(self):
        self.repos = []
        self.dataFiles = []

    def queryGraphQL(self, query):
        try:
            authHeader = {'Authorization': 'bearer {}'.format(self.githubAPIKey)}
            graphReq = requests.post(self.githubAPIRoot, json={'query': query}, headers=authHeader)
            if graphReq.status_code == 200:
                return graphReq.json()
            else:
                raise GutenbergError('Unable to execute GraphQL query {}. Status {}'.format(query, graphReq.status_code))
        except Exception as e:
            logger.debug(f'Failed to query Gutenberg GraphQL API due to {e}')
            raise GutenbergError('Encountered unexpected error querying GraphQL')

    @staticmethod
    def default_ctor(loader, tag_suffix, node):
        return '{}{}'.format(tag_suffix, node.value)


class GutenbergError(Exception):
    def __init__(self, message):
        self.message = message

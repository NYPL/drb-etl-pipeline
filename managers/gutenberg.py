from datetime import datetime
from lxml import etree
import os
import re
import requests
import yaml

from app_logging import logger


class GutenbergManager:
    def __init__(self, repoOrder, repoSortField, startTime, pageSize):
        self.repoOrder = repoOrder or 'DESC'
        self.repoSortField = repoSortField or 'PUSHED_AT'
        self.startTime = startTime or None
        self.pageSize = pageSize or 100
        self.githubAPIKey = os.environ['GITHUB_API_KEY']
        self.githubAPIRoot = os.environ['GITHUB_API_ROOT']

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

        nextPage = repositoryResponse['data']['organization']['repositories']['pageInfo']['hasNextPage'] 
        self.cursor = repositoryResponse['data']['organization']['repositories']['pageInfo'].get('endCursor', None)

        if self.startTime:
            self.repos = list(filter(
                lambda x: datetime.strptime(x['pushedAt'], '%Y-%m-%dT%H:%M:%SZ') > self.startTime,
                repositoryResponse['data']['organization']['repositories']['nodes']
            ))
        else:
            self.repos = [r for r in repositoryResponse['data']['organization']['repositories']['nodes']]
        
        if len(self.repos) == 0: nextPage = False

        return nextPage

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

        try:
            self.dataFiles.append((
                self.parseRDF(rdfResponse['data']['repository']['rdf']['text']),
                self.parseYAML(rdfResponse['data']['repository']['yaml']['text'])
            ))
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

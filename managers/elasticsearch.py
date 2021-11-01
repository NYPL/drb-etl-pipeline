import os

from elasticsearch.client import IngestClient
from elasticsearch.exceptions import ConflictError
from elasticsearch_dsl import connections, Search, Index

from model import ESWork
from logger import createLog

logger = createLog(__name__)


class ElasticsearchManager:
    def __init__(self, index=None):
        self.index = index or os.environ.get('ELASTICSEARCH_INDEX', None)
        self.client = None

    def createElasticConnection(self, host=None, port=None):
        host = host or os.environ.get('ELASTICSEARCH_HOST', None)
        port = port or os.environ.get('ELASTICSEARCH_PORT', None)
        timeout = int(os.environ.get('ELASTICSEARCH_TIMEOUT', 5))

        self.client = connections.create_connection(
            hosts=['{}:{}'.format(host, port)],
            timeout=timeout,
            retry_on_timeout=True,
            max_retries=3
        )

    def createElasticSearchIngestPipeline(self):
        esIngestClient = IngestClient(self.client)

        self.constructLanguagePipeline(
            esIngestClient, 'title_language_detector', 'title', 'Work title language detection'
        )

        self.constructLanguagePipeline(
            esIngestClient, 'alt_title_language_detector', 'alt_titles', 'Work alt_title language detection'
        )

        self.constructLanguagePipeline(
            esIngestClient, 'edition_title_language_detector', 'title', 'Edition title language detection',
            prefix='_ingest._value'
        )

        self.constructLanguagePipeline(
            esIngestClient, 'edition_sub_title_language_detector', 'sub_title', 'Edition subtitle language detection',
            prefix='_ingest._value'
        )

        self.constructLanguagePipeline(
            esIngestClient, 'edition_alt_title_language_detector', 'alt_titles', 'Edition alttitle language detection',
            prefix='_ingest._value'
        )

        self.constructLanguagePipeline(
            esIngestClient, 'subject_heading_language_detector', 'heading', 'Work title language detection',
            prefix='_ingest._value'
        )

        esIngestClient.put_pipeline(
            id='language_detector',
            body={
                'description': 'Full language processing',
                'processors': [
                    {
                        'pipeline': {
                            'name': 'title_language_detector'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'alt_title_language_detector'
                        }
                    },
                    {
                        'foreach': {
                            'field': 'editions',
                            'processor': {
                                'pipeline': {
                                    'name': 'edition_title_language_detector'
                                }
                            }
                        }
                    },
                    {
                        'foreach': {
                            'field': 'editions',
                            'processor': {
                                'pipeline': {
                                    'name': 'edition_sub_title_language_detector'
                                }
                            }
                        }
                    },
                    {
                        'foreach': {
                            'field': 'editions',
                            'processor': {
                                'pipeline': {
                                    'name': 'edition_alt_title_language_detector'
                                }
                            }
                        }
                    },
                    {
                        'foreach': {
                            'field': 'subjects',
                            'processor': {
                                'pipeline': {
                                    'name': 'subject_heading_language_detector'
                                }
                            }
                        }
                    }
                ]
            }
        )

    def createElasticSearchIndex(self):
        esIndex = Index(self.index)
        if esIndex.exists() is False:
            ESWork.init()
        else:
            logger.info(
                'ElasticSearch index {} already exists'.format(self.index)
            )

    def deleteWorkRecords(self, uuids):
        for uuid in uuids:
            retries = 0

            while True:
                try:
                    logger.debug('Deleting work {}'.format(uuid))

                    workSearch = Search(index=self.index)\
                        .query('match', uuid=uuid)

                    workSearch.params(
                        refresh=True,
                        wait_for_active_shards='all'
                    )

                    workSearch.delete()

                    break
                except ConflictError as e:
                    if retries >= 2:
                        logger.error('Unable to delete work {}'.format(uuid))
                        raise e

                    logger.warning(
                        'Unable to delete work {}. Retrying'.format(uuid)
                    )

                    retries += 1

    @staticmethod
    def constructLanguagePipeline(client, id, field, description, prefix=''):
        pipelineBody = {
            'description': description,
            'processors': [
                {
                    'inference': {
                        'model_id': 'lang_ident_model_1',
                        'inference_config': {
                            'classification': {
                                'num_top_classes': 3
                            }
                        },
                        'field_map': {
                            '{}.{}'.format(prefix, field): 'text'
                        },
                        'target_field': '{}._ml.lang_ident'.format(prefix)
                    }
                },
                {
                    'rename': {
                        'field': '{}.{}'.format(prefix, field),
                        'target_field': '{}.{}.default'.format(prefix, field)
                    }
                },
                {
                    'rename': {
                        'field': '{}._ml.lang_ident.predicted_value'.format(prefix),
                        'target_field': '{}.{}.language'.format(prefix, field)
                    }
                },
                {
                    'set': {
                        'field': '{}.{}.{{{}.{}.language}}'.format(prefix, field, prefix, field),
                        'value': '{{{}.{}.default}}'.format(prefix, field),
                        'override': False
                    }
                }
            ]
        }

        client.put_pipeline(
            id=id,
            body=pipelineBody
        )

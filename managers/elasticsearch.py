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
        print(self.client.info())

    def createElasticSearchIngestPipeline(self):
        esIngestClient = IngestClient(self.client)

        esIngestClient.put_pipeline(
            id='title_language_detector',
            body={
                'description': 'Detect cataloging language of key fields',
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
                                'title': 'text'
                            },
                            'target_field': '_ml.lang_ident'
                        }
                    },
                    {
                        'rename': {
                            'field': 'title',
                            'target_field': 'title.default'
                        }
                    },
                    {
                        'rename': {
                            'field': '_ml.lang_ident.predicted_value',
                            'target_field': 'title.language'
                        }
                    },
                    {
                        'set': {
                            'field': 'title.{{title.language}}',
                            'value': '{{title.default}}',
                            'override': False
                        }
                    }
                ]
            }
        )

        esIngestClient.put_pipeline(
            id='edition_title_language_detector',
            body={
                'description': 'Detect cataloging language of key fields',
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
                                '_ingest._value.title': 'text'
                            },
                            'target_field': '_ingest._value._ml.lang_ident'
                        }
                    },
                    {
                        'rename': {
                            'field': '_ingest._value.title',
                            'target_field': '_ingest._value.title.default'
                        }
                    },
                    {
                        'rename': {
                            'field': '_ingest._value._ml.lang_ident.predicted_value',
                            'target_field': '_ingest._value.title.language'
                        }
                    },
                    {
                        'set': {
                            'field': '_ingest._value.title.{{_ingest._value.title.language}}',
                            'value': '{{_ingest._value.title.default}}',
                            'override': False
                        }
                    }
                ]
            }
        )

        esIngestClient.put_pipeline(
            id='subject_heading_language_detector',
            body={
                'description': 'Detect cataloging language of key fields',
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
                                '_ingest._value.heading': 'text'
                            },
                            'target_field': '_ingest._value._ml.lang_ident'
                        }
                    },
                    {
                        'rename': {
                            'field': '_ingest._value.heading',
                            'target_field': '_ingest._value.heading.default'
                        }
                    },
                    {
                        'rename': {
                            'field': '_ingest._value._ml.lang_ident.predicted_value',
                            'target_field': '_ingest._value.heading.language'
                        }
                    },
                    {
                        'set': {
                            'field': '_ingest._value.heading.{{_ingest._value.heading.language}}',
                            'value': '{{_ingest._value.heading.default}}',
                            'override': False
                        }
                    }
                ]
            }
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
                        'foreach': {
                            'field': 'editions',
                            'processor': {
                                'pipeline': {
                                    'name': 'edition_title_language_detector'
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

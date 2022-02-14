import os

from elasticsearch.client import IngestClient
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from elasticsearch_dsl import connections, Search, Index

from model import ESWork
from logger import createLog

logger = createLog(__name__)


class ElasticsearchManager:
    def __init__(self, index=None):
        self.index = index or os.environ.get('ELASTICSEARCH_INDEX', None)
        self.client = None

    def createElasticConnection(self, scheme=None, host=None, port=None, user=None, pswd=None):
        scheme = scheme or os.environ.get('ELASTICSEARCH_SCHEME', None)
        host = host or os.environ.get('ELASTICSEARCH_HOST', None)
        port = port or os.environ.get('ELASTICSEARCH_PORT', None)
        user = user or os.environ.get('ELASTICSEARCH_USER', None)
        pswd = pswd or os.environ.get('ELASTICSEARCH_PSWD', None)
        timeout = int(os.environ.get('ELASTICSEARCH_TIMEOUT', 5))

        creds = '{}:{}@'.format(user, pswd) if user and pswd else ''

        host = '{}://{}{}:{}'.format(scheme, creds, host, port)

        self.client = connections.create_connection(
            hosts=[host], timeout=timeout, retry_on_timeout=True, max_retries=3
        )

        self.es = Elasticsearch(hosts=[host])

    def createElasticSearchIngestPipeline(self):
        esIngestClient = IngestClient(self.client)

        self.constructLanguagePipeline(
            esIngestClient, 'title_language_detector', 'Work title language detection',
            field='title.'
        )

        self.constructLanguagePipeline(
            esIngestClient, 'alt_title_language_detector', 'Work alt_title language detection',
            prefix='_ingest._value.'
        )

        self.constructLanguagePipeline(
            esIngestClient, 'edition_title_language_detector', 'Edition title language detection',
            prefix='_ingest._value.',
            field='title.'
        )

        self.constructLanguagePipeline(
            esIngestClient, 'edition_sub_title_language_detector', 'Edition subtitle language detection',
            prefix='_ingest._value.',
            field='sub_title.'
        )

        self.constructLanguagePipeline(
            esIngestClient, 'subject_heading_language_detector', 'Subject heading language detection',
            prefix='_ingest._value.',
            field='heading.'
        )

        esIngestClient.put_pipeline(
            id='foreach_alt_title_language_detector',
            body={
                'description': 'loop for parsing alt_titles',
                'processors': [
                    {
                        'foreach': {
                            'field': 'alt_titles',
                            'processor': {
                                'pipeline': {
                                    'name': 'alt_title_language_detector',
                                }
                            }
                        }
                    }
                ]
            }
        )

        esIngestClient.put_pipeline(
            id='edition_language_detector',
            body={
                'description': 'loop for parsing edition fields',
                'processors': [
                    {
                        'pipeline': {
                            'name': 'edition_title_language_detector',
                            'ignore_failure': True
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'edition_sub_title_language_detector',
                            'ignore_failure': True
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
                            'name': 'title_language_detector',
                            'ignore_failure': True
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'foreach_alt_title_language_detector',
                            'ignore_failure': True
                        }
                    },
                    {
                        'foreach': {
                            'field': 'editions',
                            'processor': {
                                'pipeline': {
                                    'name': 'edition_language_detector',
                                    'ignore_failure': True
                                }
                            }
                        }
                    },
                    {
                        'foreach': {
                            'field': 'subjects',
                            'ignore_missing': True,
                            'processor': {
                                'pipeline': {
                                    'name': 'subject_heading_language_detector',
                                    'ignore_failure': True
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

    @staticmethod
    def constructLanguagePipeline(client, id, description, prefix='', field=''):
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
                            '{}{}default'.format(prefix, field): 'text'
                        },
                        'target_field': '{}_ml.lang_ident'.format(prefix),
                        'on_failure': [
                            {
                                'remove': {
                                    'field': '_ml'
                                }
                            }
                        ]
                    }
                },
                {
                    'rename': {
                        'field': '{}_ml.lang_ident.predicted_value'.format(prefix),
                        'target_field': '{}{}language'.format(prefix, field)
                    }
                },
                {
                    'set': {
                        'field': 'tmp_lang',
                        'value': '{{{{{}{}language}}}}'.format(prefix, field),
                        'override': True
                    }
                },
                {
                    'set': {
                        'field': 'tmp_score',
                        'value': '{{{{{}_ml.lang_ident.prediction_score}}}}'.format(prefix),
                        'override': True
                    }
                },
                {
                    'script': {
                        'lang': 'painless',
                        'source': 'ctx.supported = (["en", "de", "fr", "sp", "po", "nl", "it", "da", "ar", "zh", "el", "hi", "fa", "ja", "ru", "th"].contains(ctx.tmp_lang))'
                    }
                },
                {
                    'script': {
                        'lang': 'painless',
                        'source': 'ctx.threshold = Float.parseFloat(ctx.tmp_score) > 0.7'
                    }
                },
                {
                    'set': {
                        'if': 'ctx.supported && ctx.threshold',
                        'field': '{}{}{{{{{}{}language}}}}'.format(prefix, field, prefix, field),
                        'value': '{{{{{}{}default}}}}'.format(prefix, field),
                        'override': False
                    }
                },
                {
                    'remove': {
                        'field': [
                            '{}_ml'.format(prefix),
                            'tmp_lang',
                            'tmp_score',
                            'threshold',
                            'supported'
                        ]
                    }
                }
            ]
        }

        client.put_pipeline(
            id=id,
            body=pipelineBody
        )

    def saveWorkRecords(self, works):
        logger.info('Saving {} ES Work Records'.format(len(works)))

        saveRes = bulk(self.es, self._upsertGenerator(works), raise_on_error=False)
        logger.debug(saveRes)

        if saveRes[1]:
            for err in saveRes[1]:
                logger.error('Type: {}, Reason: {}'.format(
                    err['update']['error']['type'], err['update']['error']['reason']
                ))

    def _upsertGenerator(self, works):
        for work in works:
            logger.debug('Saving {}'.format(work))

            yield {
                '_op_type': 'update',
                '_index': self.index,
                '_id': work.uuid,
                '_type': '_doc',
                'pipeline': 'language_detector',
                'doc_as_upsert': True,
                'doc': work.to_dict()
            }

    def deleteWorkRecords(self, uuids):
        logger.info('Deleting {} ES Work Records'.format(len(uuids)))

        deleteRes = bulk(self.es, self._deleteGenerator(uuids), raise_on_error=False)
        logger.debug(deleteRes)

    def _deleteGenerator(self, uuids):
        for uuid in uuids:
            logger.debug('Deleting {}'.format(uuid))

            yield {
                '_op_type': 'delete',
                '_index': self.index,
                '_id': uuid,
                '_type': 'doc'
            }

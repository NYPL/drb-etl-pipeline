from elastic_transport import ConnectionTimeout
import pytest

from managers import ElasticsearchManager
from model import ESWork


class TestElasticsearchManager:
    @pytest.fixture
    def testInstance(self, mocker):
        mocker.patch.dict('os.environ', {
            'ELASTICSEARCH_INDEX': 'testES',
            'ELASTICSEARCH_HOST': 'host',
            'ELASTICSEARCH_PORT': 'port',
            'ELASTICSEARCH_TIMEOUT': '1000',
            'ELASTICSEARCH_SCHEME': 'http',
            'ELASTICSEARCH_USER': 'testUser',
            'ELASTICSEARCH_PSWD': 'testPswd'
        })

        return ElasticsearchManager()

    def test_initializer(self, testInstance):
        assert testInstance.index == 'testES'

    def test_createElasticConnection_success(self, testInstance, mocker):
        mockConnection = mocker.patch('managers.elasticsearch.connections')
        mockClient = mocker.patch('managers.elasticsearch.Elasticsearch')

        testInstance.createElasticConnection()

        mockConnection.create_connection.assert_called_once_with(
            hosts=['http://testUser:testPswd@host:port'],
            timeout=1000,
            retry_on_timeout=True,
            max_retries=3
        )

        mockClient.assert_called_once_with(
            hosts=['http://testUser:testPswd@host:port'],
            timeout=1000,
            retry_on_timeout=True,
            max_retries=3
        )

    def test_createELasticSearchIndex_execute(self, testInstance, mocker):
        testIndexCon = mocker.patch('managers.elasticsearch.Index')
        testIndex = mocker.MagicMock()
        testIndexCon.return_value = testIndex
        testIndex.exists.return_value = False
        
        mockInit = mocker.patch.object(ESWork, 'init')

        testInstance.createElasticSearchIndex()

        testIndexCon.assert_called_once_with('testES')
        testIndex.exists.assert_called_once()
        mockInit.assert_called_once()

    def test_createELasticSearchIndex_skip(self, testInstance, mocker):
        testIndexCon = mocker.patch('managers.elasticsearch.Index')
        testIndex = mocker.MagicMock()
        testIndexCon.return_value = testIndex
        testIndex.exists.return_value = True
        
        mockInit = mocker.patch.object(ESWork, 'init')

        testInstance.createElasticSearchIndex()

        testIndexCon.assert_called_once_with('testES')
        testIndex.exists.assert_called_once()
        mockInit.assert_not_called()

    def test_deleteWorkRecords(self, testInstance, mocker):
        testInstance.es = 'mockClient'
        mockBulk = mocker.patch('managers.elasticsearch.bulk')
        mockGen = mocker.patch.object(ElasticsearchManager, '_deleteGenerator')
        mockGen.return_value = 'generator'

        testInstance.deleteWorkRecords(['uuid1', 'uuid2', 'uuid3'])

        mockGen.assert_called_once_with(['uuid1', 'uuid2', 'uuid3'])
        mockBulk.assert_called_once_with(
            'mockClient', 'generator', raise_on_error=False
        )

    def test_deleteGenerator(self, testInstance):
        deleteStmts = [out for out in testInstance._deleteGenerator([1, 2, 3])]

        assert deleteStmts == [
            {'_op_type': 'delete', '_index': 'testES', '_id': 1},
            {'_op_type': 'delete', '_index': 'testES', '_id': 2},
            {'_op_type': 'delete', '_index': 'testES', '_id': 3},
        ]

    def test_saveWorkRecords_success(self, testInstance, mocker):
        testInstance.es = 'mockClient'
        mockBulk = mocker.patch('managers.elasticsearch.bulk')
        mockGen = mocker.patch.object(ElasticsearchManager, '_upsertGenerator')
        mockGen.return_value = 'generator'

        mockBulk.return_value = (2, [{'index': {'error': {'type': 'testing', 'reason': 'testing'}}}])

        testInstance.saveWorkRecords(['work1', 'work2', 'work3'])

        mockGen.assert_called_once_with(['work1', 'work2', 'work3'])
        mockBulk.assert_called_once_with('mockClient', 'generator', raise_on_error=False)

    def test_saveWorkRecords_retry_failure(self, testInstance, mocker):
        testInstance.es = 'mockClient'
        mockBulk = mocker.patch('managers.elasticsearch.bulk')
        mockGen = mocker.patch.object(ElasticsearchManager, '_upsertGenerator')
        mockGen.return_value = 'generator'

        mockBulk.side_effect = ConnectionTimeout('testing')

        workArray = [f'work{i}' for i in range(6)]

        testInstance.saveWorkRecords(workArray)

        mockGen.assert_has_calls([
            mocker.call(workArray),
            mocker.call(workArray[:3]),
            mocker.call(workArray[:1]),
            mocker.call(workArray[1:3]),
            mocker.call(workArray[3:]),
            mocker.call(workArray[3:4]),
            mocker.call(workArray[4:]),
        ])
        mockBulk.assert_has_calls(
            [mocker.call('mockClient', 'generator', raise_on_error=False)] * 7
        )

    def test_saveWorkRecords_retry_success(self, testInstance, mocker):
        testInstance.es = 'mockClient'
        mockBulk = mocker.patch('managers.elasticsearch.bulk')
        mockGen = mocker.patch.object(ElasticsearchManager, '_upsertGenerator')
        mockGen.return_value = 'generator'

        mockBulk.side_effect = [
            ConnectionTimeout('testing'),
            ('testing', False),
            ('testing', False)
        ]

        workArray = [f'work{i}' for i in range(5)]

        testInstance.saveWorkRecords(workArray)

        mockGen.assert_has_calls([
            mocker.call(workArray),
            mocker.call(workArray[:2]),
            mocker.call(workArray[2:])
        ])

        mockBulk.assert_has_calls(
            [mocker.call('mockClient', 'generator', raise_on_error=False)] * 3
        )

    def test_saveWorkRecords_retry_partial_failure(self, testInstance, mocker):
        testInstance.es = 'mockClient'
        mockBulk = mocker.patch('managers.elasticsearch.bulk')
        mockGen = mocker.patch.object(ElasticsearchManager, '_upsertGenerator')
        mockGen.return_value = 'generator'

        mockBulk.side_effect = [
            ConnectionTimeout('testing'),  # 0, 1, 2, 3, 4
            ('testing', False),  # 0, 1
            ConnectionTimeout('testing'),  # 2, 3, 4
            ConnectionTimeout('testing'),  # 2
            ('testing', False),  # 3, 4
        ]

        workArray = [f'work{i}' for i in range(5)]

        testInstance.saveWorkRecords(workArray)

        mockGen.assert_has_calls([
            mocker.call(workArray),
            mocker.call(workArray[:2]),
            mocker.call(workArray[2:]),
            mocker.call(workArray[2:3]),
            mocker.call(workArray[3:])
        ])

        mockBulk.assert_has_calls(
            [mocker.call('mockClient', 'generator', raise_on_error=False)] * 5
        )

    def test_upsertGenerator(self, testInstance, mocker):
        mockWork = mocker.MagicMock(uuid=1)
        mockWork.to_dict.return_value = 'mockWork'
        upsertStmts = [out for out in testInstance._upsertGenerator([mockWork])]

        assert upsertStmts == [
            {
                '_op_type': 'index',
                '_index': 'testES',
                '_id': 1,
                '_source': 'mockWork',
                'pipeline': 'language_detector'
            }
        ]

    def test_createElasticSearchIngestPipeline(self, testInstance, mocker):
        mockIngest = mocker.MagicMock()
        mockClient = mocker.patch('managers.elasticsearch.IngestClient')
        mockClient.return_value = mockIngest

        mockConstructor = mocker.patch.object(ElasticsearchManager, 'constructLanguagePipeline')

        testInstance.createElasticSearchIngestPipeline()

        mockClient.assert_called_once_with(None)

        mockConstructor.assert_has_calls([
            mocker.call(mockIngest, 'title_language_detector', 'Work title language detection', field='title.'),
            mocker.call(mockIngest, 'alt_title_language_detector', 'Work alt_title language detection', prefix='_ingest._value.'),
            mocker.call(mockIngest, 'edition_title_language_detector', 'Edition title language detection', prefix='_ingest._value.', field='title.'),
            mocker.call(mockIngest, 'edition_sub_title_language_detector', 'Edition subtitle language detection', prefix='_ingest._value.', field='sub_title.'),
            mocker.call(mockIngest, 'subject_heading_language_detector', 'Subject heading language detection', prefix='_ingest._value.', field='heading.')
        ])

        mockIngest.put_pipeline.assert_has_calls([
            mocker.call(
                id='foreach_alt_title_language_detector',
                body={
                    'description': 'loop for parsing alt_titles',
                    'processors': [
                        {
                            'foreach': {
                                'field': 'alt_titles',
                                'processor': {'pipeline': {'name': 'alt_title_language_detector'}}
                            }
                        }
                    ]
                }
            ),
            mocker.call(
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
            ),
            mocker.call(
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
        ])

    def test_constructLanguagePipeline(self, mocker):
        mockClient = mocker.MagicMock()

        ElasticsearchManager.constructLanguagePipeline(
            mockClient, 'testPipeline', 'Testing', 'prefix.', 'field.'
        )

        testBody = {
            'description': 'Testing',
            'processors': [
                {
                    'inference': {
                        'model_id': 'lang_ident_model_1',
                        'inference_config': {
                            'classification': {
                                'num_top_classes': 3
                            }
                        },
                        'field_map': {'prefix.field.default': 'text'},
                        'target_field': 'prefix._ml.lang_ident',
                        'on_failure': [
                            {
                                'remove': {
                                    'field': '_ml'
                                }
                            }
                        ]
                    },
                },
                {
                    'rename': {
                        'field': 'prefix._ml.lang_ident.predicted_value',
                        'target_field': 'prefix.field.language'
                    }
                },
                {
                    'set': {
                        'field': 'tmp_lang',
                        'value': '{{prefix.field.language}}',
                        'override': True
                    }
                },
                {
                    'set': {
                        'field': 'tmp_score',
                        'value': '{{prefix._ml.lang_ident.prediction_score}}',
                        'override': True
                    }
                },
                {
                    'script': {'lang': 'painless', 'source': 'ctx.supported = (["en", "de", "fr", "sp", "po", "nl", "it", "da", "ar", "zh", "el", "hi", "fa", "ja", "ru", "th"].contains(ctx.tmp_lang))'}
                },
                {
                    'script': {'lang': 'painless', 'source': 'ctx.threshold = Float.parseFloat(ctx.tmp_score) > 0.7'}
                },
                {
                    'set': {
                        'if': 'ctx.supported && ctx.threshold',
                        'field': 'prefix.field.{{prefix.field.language}}',
                        'value': '{{prefix.field.default}}',
                        'override': False
                    }
                },
                {
                    'remove': {
                        'field': ['prefix._ml', 'tmp_lang', 'tmp_score', 'threshold', 'supported']
                    }
                }
            ]
        }

        mockClient.put_pipeline.assert_called_once_with(
            id='testPipeline', body=testBody
        )

    def test_splitWorkBatch_even(self):
        firstHalf, secondHalf = ElasticsearchManager._splitWorkBatch([i for i in range(10)])

        assert firstHalf == [i for i in range(5)]
        assert secondHalf == [i for i in range(5, 10)]

    def test_splitWorkBatch_odd(self):
        firstHalf, secondHalf = ElasticsearchManager._splitWorkBatch([i for i in range(13)])

        assert firstHalf == [i for i in range(6)]
        assert secondHalf == [i for i in range(6, 13)]

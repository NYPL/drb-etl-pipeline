import pytest

from api.utils import APIUtils

class TestAPIUtils:
    @pytest.fixture
    def testAggregationResp(self):
        return {
            'editions': {
                'edition_filter_0': {
                    'key': 'lang_parent',
                    'buckets': [
                        {'key': 'Test1', 'editions_per_language': {'doc_count': 1}},
                        {'key': 'Test2', 'editions_per_language': {'doc_count': 3}}
                    ]
                }
            }
        }

    @pytest.fixture
    def testHitObject(self, mocker):
        mockHits = [mocker.MagicMock(), mocker.MagicMock(), mocker.MagicMock()] 
        mockHits[0].meta.sort = ('firstSort',)
        mockHits[-1].meta.sort = ('lastSort',)

        return mockHits

    @pytest.fixture
    def MockDBObject(self):
        class MockDB:
            def __init__(self, *args, **kwargs):
                self.attrs = []
                for key, value in kwargs.items():
                    self.attrs.append(key)
                    setattr(self, key, value)

            def __iter__(self):
                for attr in self.attrs:
                    yield attr, getattr(self, attr)

        return MockDB

    @pytest.fixture
    def testLink(self, MockDBObject):
        return MockDBObject(id='li1', media_type='application/test', url='testURI')

    @pytest.fixture
    def testItem(self, MockDBObject, testLink):
        return MockDBObject(id='it1', links=[testLink], physical_location={'name': 'test'})

    @pytest.fixture
    def testEdition(self, MockDBObject, testItem):
        return MockDBObject(id='ed1', items=[testItem])

    @pytest.fixture
    def testWork(self, MockDBObject, testEdition):
        return MockDBObject(uuid='testUUID', title='Test Title', editions=[testEdition])

    def test_normalizeQueryParams(self, mocker):
        mockParams = mocker.MagicMock()
        mockParams.to_dict.return_value = {'test1': 1, 'test2': 2}

        testParams = APIUtils.normalizeQueryParams(mockParams)

        assert testParams == {'test1': 1, 'test2': 2}

    def test_extractParamPairs(self):
        testPairs = APIUtils.extractParamPairs('test', {'test': ['test:value', 'bareValue']})

        assert testPairs[0] == ('test', 'value')
        assert testPairs[1] == ('test', 'bareValue')

    def test_formatAggregationResult(self, testAggregationResp):
        languageAggregations = APIUtils.formatAggregationResult(testAggregationResp)

        assert languageAggregations[0] == {'value': 'Test1', 'count': 1}
        assert languageAggregations[1] == {'value': 'Test2', 'count': 3}

    def test_formatPagingOptions(self, testHitObject):
        testPagingOptions = APIUtils.formatPagingOptions(testHitObject)

        assert testPagingOptions == {'prevPageSort': ['firstSort'], 'nextPageSort': ['lastSort']}

    def test_formatWorkOutput_single_work(self, mocker):
        mockFormat = mocker.patch.object(APIUtils, 'formatWork')
        mockFormat.return_value = 'formattedWork'

        outWork = APIUtils.formatWorkOutput('testWork')

        assert outWork == 'formattedWork'
        mockFormat.assert_called_once_with('testWork', None, True)

    def test_formatWorkOutput_multiple_works(self, mocker):
        mockFlatten = mocker.patch.object(APIUtils, 'flatten')
        mockFlatten.return_value = [1, 2, 3]
        mockFormat = mocker.patch.object(APIUtils, 'formatWork')
        mockFormat.side_effect = ['formattedWork1', 'formattedWork2']

        outWorks = APIUtils.formatWorkOutput(
            ['testWork1', 'testWork2'],
            [('test', 1), ('test', 2), ('test', 3)]
        )

        assert outWorks == ['formattedWork1', 'formattedWork2']
        mockFlatten.assert_called_once_with([1, 2, 3])
        mockFormat.assert_has_calls([
            mocker.call('testWork1', [1, 2, 3], True),
            mocker.call('testWork2', [1, 2, 3], True)
        ])

    def test_formatWork_showAll(self, testWork, mocker):
        mockFormatEdition = mocker.patch.object(APIUtils, 'formatEdition')
        mockFormatEdition.return_value = {'edition_id': 'ed1', 'items': ['it1']}

        testWorkDict = APIUtils.formatWork(testWork, ['ed1'], True)

        assert testWorkDict['uuid'] == 'testUUID'
        assert testWorkDict['title'] == 'Test Title'
        assert testWorkDict['editions'][0]['edition_id'] == 'ed1'
        assert testWorkDict['editions'][0]['items'][0] == 'it1'
        mockFormatEdition.assert_called_once()

    def test_formatWork_showAll_false(self, testWork, mocker):
        mockFormatEdition = mocker.patch.object(APIUtils, 'formatEdition')
        mockFormatEdition.return_value = {'edition_id': 'ed1', 'items': ['it1']}
        testWorkDict = APIUtils.formatWork(testWork, ['ed1'], False)

        assert testWorkDict['uuid'] == 'testUUID'
        assert testWorkDict['title'] == 'Test Title'
        assert len(testWorkDict['editions']) == 1

    def test_formatWork_blocked_edition(self, testWork):
        testWork.editions[0].items = []
        testWorkDict = APIUtils.formatWork(testWork, ['ed2'], True)

        assert testWorkDict['uuid'] == 'testUUID'
        assert testWorkDict['title'] == 'Test Title'
        assert len(testWorkDict['editions']) == 0

    def test_formatEditionOputput(self, mocker):
        mockFormatEdition = mocker.patch.object(APIUtils, 'formatEdition')
        mockFormatEdition.return_value = 'testEdition'

        assert APIUtils.formatEditionOutput(1, True) == 'testEdition'

    def test_formatEdition(self, testEdition):
        formattedEdition = APIUtils.formatEdition(testEdition)

        assert formattedEdition['edition_id'] == 'ed1'
        assert formattedEdition['items'][0]['item_id'] == 'it1'
        assert formattedEdition['items'][0]['location'] == 'test'
        assert formattedEdition['items'][0]['links'][0]['link_id'] == 'li1'
        assert formattedEdition['items'][0]['links'][0]['mediaType'] == 'application/test'
        assert formattedEdition['items'][0]['links'][0]['url'] == 'testURI'

    def test_formatLinkOutput(self, testLink, testWork, testEdition, testItem):
        testEdition.work = testWork
        testItem.edition = testEdition
        testLink.items = [testItem]

        testLink = APIUtils.formatLinkOutput(testLink)

        assert testLink['link_id'] == 'li1'
        assert testLink['work']['uuid'] == 'testUUID'
        assert testLink['work']['edition']['edition_id'] == 'ed1'
        assert testLink['work']['edition']['item']['item_id'] == 'it1'

    def test_formatLanguages_no_counts(self, mocker):
        mockAggs = mocker.MagicMock()
        mockAggs.languages.languages.buckets = [mocker.MagicMock(key='bLang'), mocker.MagicMock(key='aLang')]

        assert APIUtils.formatLanguages(mockAggs) == [{'language': 'aLang'}, {'language': 'bLang'}]

    def test_formatLanguages_counts(self, mocker):
        mockAggs = mocker.MagicMock()
        mockAggs.languages.languages.buckets = [
            mocker.MagicMock(key='bLang', work_totals=mocker.MagicMock(doc_count=10)),
            mocker.MagicMock(key='cLang', work_totals=mocker.MagicMock(doc_count=30)),
            mocker.MagicMock(key='aLang', work_totals=mocker.MagicMock(doc_count=20))
        ]

        assert APIUtils.formatLanguages(mockAggs, True) == [
            {'language': 'cLang', 'work_total': 30},
            {'language': 'aLang', 'work_total': 20},
            {'language': 'bLang', 'work_total': 10}
        ]

    def test_formatTotals(self):
        assert APIUtils.formatTotals([('test', 3), ('other', 6)]) == {'test': 3, 'other': 6}

    def test_flatten_already_flat(self):
        flatArray = [i for i in APIUtils.flatten([1, 2, 3, 4, 5])]

        assert flatArray == [1, 2, 3, 4, 5]

    def test_flatten_nested(self):
        flatArray = [i for i in APIUtils.flatten([[1, 2], 3, [4, [5]]])]

        assert flatArray == [1, 2, 3, 4, 5]

    def test_formatResponseObject(self, mocker):
        mockDatetime = mocker.patch('api.utils.datetime')
        mockDatetime.utcnow.return_value = 'presentTimestamp'
        mockJsonify = mocker.patch('api.utils.jsonify')
        mockJsonify.return_value = 'jsonBlock'

        testResponse = APIUtils.formatResponseObject(200, 'test', 'testData')

        assert testResponse[0] == 'jsonBlock'
        assert testResponse[1] == 200
        mockDatetime.utcnow.assert_called_once
        mockJsonify.assert_called_once_with({
            'status': 200, 'timestamp': 'presentTimestamp', 'responseType': 'test', 'data': 'testData'
        })

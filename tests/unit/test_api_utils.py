from hashlib import scrypt
import pytest

from api.utils import APIUtils


class TestAPIUtils:
    @pytest.fixture
    def testAggregationResp(self):
        return {
            'editions': {
                'edition_filter_0': {
                    'languages': {
                        'buckets': [
                            {'key': 'Lang1', 'editions_per': {'doc_count': 1}},
                            {'key': 'Lang2', 'editions_per': {'doc_count': 3}}
                        ]
                    },
                    'formats': {
                        'buckets': [
                            {
                                'key': 'Format1',
                                'editions_per': {'doc_count': 5}
                            }
                        ]
                    }
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
    def MockDBObject(self, mocker):
        class MockDB:
            def __init__(self, *args, **kwargs):
                self.attrs = []
                for key, value in kwargs.items():
                    self.attrs.append(key)
                    setattr(self, key, value)

            def __iter__(self):
                for attr in self.attrs:
                    value = getattr(self, attr)

                    if isinstance(value, mocker.MagicMock):
                        value = dict(value)
                    elif isinstance(value, list):
                        value = [dict(v) for v in value]

                    yield attr, value

        return MockDB

    @pytest.fixture
    def testRecord(self, MockDBObject):
        return MockDBObject(
            id='rec1',
            title='Test Record',
            spatial='Test Place',
            extent='Test Extent',
            abstract='Test Summary',
            table_of_contents='Test TOC',
            authors=['auth1', 'auth2', 'auth3'],
            contributors=['contrib1', 'contrib2'],
            publisher=['pub1'],
            dates=['date1', 'date2'],
            languages=['lang1'],
            identifiers=['id1', 'id2', 'id3'],
            has_part=['1|url1|', '2|url2|', '3|url3|']
        )

    @pytest.fixture
    def testLink(self, MockDBObject):
        return MockDBObject(
            id='li1', media_type='application/test', url='testURI'
        )

    @pytest.fixture
    def testWebpubLink(self, MockDBObject):
        return MockDBObject(
            id='li2', media_type='application/webpub+json', url='testURI'
        )

    @pytest.fixture
    def testRights(self, MockDBObject):
        return MockDBObject(
            id='ri1',
            source='test',
            license='testLicense',
            rights_statement='testStatement'
        )

    @pytest.fixture
    def testItem(self, MockDBObject, testLink, testRights):
        return MockDBObject(
            id='it1',
            links=[testLink],
            rights=[testRights],
            physical_location={'name': 'test'}
        )

    @pytest.fixture
    def testWebpubItem(self, MockDBObject, testWebpubLink):
        return MockDBObject(
            id='it2', links=[testWebpubLink], rights=[], physical_location={}
        )

    @pytest.fixture
    def testEdition(self, MockDBObject, testItem, mocker):
        return MockDBObject(
            id='ed1',
            work=mocker.MagicMock(uuid='uuid1'),
            publication_date=mocker.MagicMock(year=2000),
            items=[testItem],
            links=[mocker.MagicMock(
                id='co1', media_type='image/png', url='testCover'
            )]
        )

    @pytest.fixture
    def testWork(self, MockDBObject, testEdition):
        return MockDBObject(
            uuid='testUUID', title='Test Title', editions=[testEdition]
        )

    def test_normalizeQueryParams(self, mocker):
        mockParams = mocker.MagicMock()
        mockParams.to_dict.return_value = {'test1': 1, 'test2': 2}

        testParams = APIUtils.normalizeQueryParams(mockParams)

        assert testParams == {'test1': 1, 'test2': 2}

    def test_extractParamPairs(self):
        testPairs = APIUtils.extractParamPairs(
            'test', {'test': ['title:value', 'bareValue']}
        )

        assert testPairs[0] == ('title', 'value')
        assert testPairs[1] == ('test', 'bareValue')

    def test_extractParamPairs_comma_delimited(self):
        testPairs = APIUtils.extractParamPairs(
            'test', {'test': ['title:value,subject:value']}
        )

        assert testPairs[0] == ('title', 'value')
        assert testPairs[1] == ('subject', 'value')

    def test_extractParamPairs_comma_delimited_quotes(self):
        testPairs = APIUtils.extractParamPairs(
            'test', {'test': ['title:value,author:"Test, Author",other']}
        )

        assert testPairs[0] == ('title', 'value')
        assert testPairs[1] == ('author', '"Test, Author",other')

    def test_extractParamPairs_semantic_semicolon(self):
        testPairs = APIUtils.extractParamPairs(
            'test', {'test': ['title:A Book: A Title']}
        )

        assert testPairs[0] == ('title', 'A Book: A Title')

    def test_extractParamPairs_semicolon_no_field(self):
        testPairs = APIUtils.extractParamPairs(
            'test', {'test': ['A Book: A Title']}
        )

        assert testPairs[0] == ('test', 'A Book: A Title')

    def test_extractParamPairs_dangling_quotation(self):
        testPairs = APIUtils.extractParamPairs(
            'test', {'test': ['"A Title']}
        )

        assert testPairs[0] == ('test', 'A Title')

    def test_extractParamPairs_dangling_quotation_multiple(self):
        testPairs = APIUtils.extractParamPairs(
            'test', {'test': ['"A Title",keyword:"other']}
        )

        assert testPairs[0] == ('test', '"A Title"')
        assert testPairs[1] == ('keyword', 'other')

    def test_formatAggregationResult(self, testAggregationResp):
        testAggregations = APIUtils.formatAggregationResult(
            testAggregationResp
        )

        assert testAggregations['languages'][0] ==\
            {'value': 'Lang1', 'count': 1}
        assert testAggregations['languages'][1] ==\
            {'value': 'Lang2', 'count': 3}
        assert testAggregations['formats'][0] ==\
            {'value': 'Format1', 'count': 5}

    def test_formatPagingOptions_previous_null(self):
        testPagingOptions = APIUtils.formatPagingOptions(1, 10, 50)

        assert testPagingOptions == {
            'recordsPerPage': 10,
            'firstPage': 1,
            'previousPage': None,
            'currentPage': 1,
            'nextPage': 2,
            'lastPage': 5
        }

    def test_formatPagingOptions_next_null(self):
        testPagingOptions = APIUtils.formatPagingOptions(6, 10, 55)

        assert testPagingOptions == {
            'recordsPerPage': 10,
            'firstPage': 1,
            'previousPage': 5,
            'currentPage': 6,
            'nextPage': None,
            'lastPage': 6
        }

    def test_formatWorkOutput_single_work(self, mocker):
        mockFormat = mocker.patch.object(APIUtils, 'formatWork')
        mockFormat.return_value = {
            'uuid': 1,
            'editions': [
                {'id': 'ed1', 'publication_date': None},
                {'id': 'ed2', 'publication_date': 2000},
                {'id': 'ed3', 'publication_date': 1900}
            ]
        }

        outWork = APIUtils.formatWorkOutput('testWork', None)

        assert outWork['uuid'] == 1
        assert outWork['editions'][0]['id'] == 'ed3'
        assert outWork['editions'][2]['id'] == 'ed1'
        mockFormat.assert_called_once_with('testWork', None, True, reader=None)

    def test_formatWorkOutput_multiple_works(self, mocker):
        mockFormat = mocker.patch.object(APIUtils, 'formatWork')
        mockFormat.side_effect = ['formattedWork1', 'formattedWork2']

        testWorks = [
            mocker.MagicMock(uuid='uuid1'), mocker.MagicMock(uuid='uuid2')
        ]

        outWorks = APIUtils.formatWorkOutput(
            testWorks, [('uuid1', 1), ('uuid2', 2), ('uuid3', 3)]
        )

        assert outWorks == ['formattedWork1', 'formattedWork2']
        mockFormat.assert_has_calls([
            mocker.call(testWorks[0], 1, True, formats=None, reader=None),
            mocker.call(testWorks[1], 2, True, formats=None, reader=None)
        ])

    def test_formatWork_showAll(self, testWork, mocker):
        mockFormatEdition = mocker.patch.object(APIUtils, 'formatEdition')
        mockFormatEdition.return_value = {
            'edition_id': 'ed1', 'items': ['it1']
        }

        testWorkDict = APIUtils.formatWork(testWork, ['ed1'], True)

        assert testWorkDict['uuid'] == 'testUUID'
        assert testWorkDict['title'] == 'Test Title'
        assert testWorkDict['editions'][0]['edition_id'] == 'ed1'
        assert testWorkDict['editions'][0]['items'][0] == 'it1'
        assert testWorkDict['edition_count'] == 1
        mockFormatEdition.assert_called_once()

    def test_formatWork_showAll_false(self, testWork, mocker):
        mockFormatEdition = mocker.patch.object(APIUtils, 'formatEdition')
        mockFormatEdition.return_value = {
            'edition_id': 'ed1', 'items': ['it1']
        }
        testWorkDict = APIUtils.formatWork(testWork, ['ed1'], False)

        assert testWorkDict['uuid'] == 'testUUID'
        assert testWorkDict['title'] == 'Test Title'
        assert len(testWorkDict['editions']) == 1
        assert testWorkDict['edition_count'] == 1

    def test_formatWork_blocked_edition(self, testWork):
        testWork.editions[0].items = []
        testWorkDict = APIUtils.formatWork(testWork, ['ed2'], True)

        assert testWorkDict['uuid'] == 'testUUID'
        assert testWorkDict['title'] == 'Test Title'
        assert len(testWorkDict['editions']) == 0
        assert testWorkDict['edition_count'] == 1

    def test_formatWork_ordered_editions(self, testWork, mocker):
        testWork.editions = [mocker.MagicMock(id=1), mocker.MagicMock(id=2)]

        mockFormatEdition = mocker.patch.object(APIUtils, 'formatEdition')
        mockFormatEdition.side_effect = [
            {'edition_id': 'ed1', 'items': ['it1']},
            {'edition_id': 'ed2', 'items': ['it2']}
        ]

        testWorkDict = APIUtils.formatWork(testWork, [2, 1], True)

        assert testWorkDict['editions'][0]['edition_id'] == 'ed2'
        assert testWorkDict['editions'][1]['edition_id'] == 'ed1'

    def test_formatEditionOputput(self, mocker):
        mockFormatEdition = mocker.patch.object(APIUtils, 'formatEdition')
        mockFormatEdition.return_value = 'testEdition'

        assert APIUtils.formatEditionOutput(
            1, records='testRecords', showAll=True
        ) == 'testEdition'

        mockFormatEdition.assert_called_once_with(
            1, 'testRecords', showAll=True, reader=None
        )

    def test_formatEdition_no_records(self, testEdition):
        formattedEdition = APIUtils.formatEdition(testEdition)

        assert formattedEdition['work_uuid'] == 'uuid1'
        assert formattedEdition['edition_id'] == 'ed1'
        assert formattedEdition['publication_date'] == 2000
        assert formattedEdition['links'][0]['link_id'] == 'co1'
        assert formattedEdition['links'][0]['mediaType'] == 'image/png'
        assert formattedEdition['links'][0]['url'] == 'testCover'
        assert formattedEdition['items'][0]['item_id'] == 'it1'
        assert formattedEdition['items'][0]['location'] == 'test'
        assert formattedEdition['items'][0]['links'][0]['link_id'] == 'li1'
        assert formattedEdition['items'][0]['links'][0]['mediaType'] ==\
            'application/test'
        assert formattedEdition['items'][0]['links'][0]['url'] == 'testURI'
        assert formattedEdition['items'][0]['rights'][0]['source'] == 'test'
        assert formattedEdition['items'][0]['rights'][0]['license'] ==\
            'testLicense'
        assert formattedEdition['items'][0]['rights'][0]['rightsStatement'] ==\
            'testStatement'
        assert formattedEdition.get('instances', None) is None

    def test_formatEdition_w_records(self, testEdition, mocker):
        mockRecFormat = mocker.patch.object(APIUtils, 'formatRecord')
        mockRecFormat.side_effect = [
            {'id': 1, 'items': []}, {'id': 2, 'items': ['it1']}
        ]

        formattedEdition = APIUtils.formatEdition(
            testEdition, ['rec1', 'rec2'], showAll=False
        )

        assert len(formattedEdition['instances']) == 1
        assert formattedEdition['instances'][0]['id'] == 2
        assert formattedEdition.get('items', None) is None

        testItemDict = {
            'id': 'it1',
            'links': [{
                'link_id': 'li1',
                'mediaType': 'application/test',
                'url': 'testURI'
            }],
            'rights': [{
                'source': 'test',
                'license': 'testLicense',
                'rightsStatement': 'testStatement'
            }],
            'physical_location': {'name': 'test'},
            'item_id': 'it1',
            'location': 'test'
        }

        mockRecFormat.assert_has_calls([
            mocker.call('rec1', {'testURI': testItemDict}),
            mocker.call('rec2', {'testURI': testItemDict})
        ])

    def test_formatEdition_filter_reader_v1(self, testEdition, testWebpubItem):
        testEdition.items.append(testWebpubItem)

        formattedEdition = APIUtils.formatEdition(testEdition, reader='v1')

        assert len(formattedEdition['items']) == 1
        assert formattedEdition['items'][0]['item_id'] == 'it1'
        assert formattedEdition['items'][0]['links'][0]['mediaType'] ==\
            'application/test'

    def test_formatEdition_filter_reader_v2(self, testEdition, testWebpubItem):
        testEdition.items.append(testWebpubItem)

        formattedEdition = APIUtils.formatEdition(testEdition, reader='v2')

        assert len(formattedEdition['items']) == 2
        assert formattedEdition['items'][1]['item_id'] == 'it2'
        assert formattedEdition['items'][1]['links'][0]['mediaType'] ==\
            'application/webpub+json'

    def test_formatRecord(self, testRecord, mocker):
        testLinkItems = {
            'url1': {'item_id': 1, 'url': 'url1'},
            'url2': {'item_id': 2, 'url': 'url2'}
        }

        mockFormatPipe = mocker.patch.object(
            APIUtils, 'formatPipeDelimitedData'
        )
        mockFormatPipe.side_effect = [
            'testAuthors', 'testContribs', 'testPublishers',
            'testDates', 'testLangs', 'testIDs'
        ]

        testFormatted = APIUtils.formatRecord(testRecord, testLinkItems)

        assert testFormatted['instance_id'] == 'rec1'
        assert testFormatted['title'] == 'Test Record'
        assert testFormatted['publication_place'] == 'Test Place'
        assert testFormatted['extent'] == 'Test Extent'
        assert testFormatted['summary'] == 'Test Summary'
        assert testFormatted['table_of_contents'] == 'Test TOC'
        assert testFormatted['authors'] == 'testAuthors'
        assert testFormatted['contributors'] == 'testContribs'
        assert testFormatted['publishers'] == 'testPublishers'
        assert testFormatted['dates'] == 'testDates'
        assert testFormatted['languages'] == 'testLangs'
        assert testFormatted['identifiers'] == 'testIDs'
        assert testFormatted['items'] == [
            {'item_id': 1, 'url': 'url1'}, {'item_id': 2, 'url': 'url2'}
        ]

    def test_formatLinkOutput(self, testLink, testWork, testEdition, testItem):
        testEdition.work = testWork
        testItem.edition = testEdition
        testLink.items = [testItem]

        testLink = APIUtils.formatLinkOutput(testLink)

        assert testLink['link_id'] == 'li1'
        assert testLink['work']['uuid'] == 'testUUID'
        assert testLink['work']['editions'][0]['edition_id'] == 'ed1'
        assert testLink['work']['editions'][0]['items'][0]['item_id'] == 'it1'

    def test_formatLanguages_no_counts(self, mocker):
        mockAggs = mocker.MagicMock()
        mockAggs.languages.languages.buckets = [
            mocker.MagicMock(key='bLang'), mocker.MagicMock(key='aLang')
        ]

        assert APIUtils.formatLanguages(mockAggs) ==\
            [{'language': 'aLang'}, {'language': 'bLang'}]

    def test_formatLanguages_counts(self, mocker):
        mockAggs = mocker.MagicMock()
        mockAggs.languages.languages.buckets = [
            mocker.MagicMock(
                key='bLang', work_totals=mocker.MagicMock(doc_count=10)
            ),
            mocker.MagicMock(
                key='cLang', work_totals=mocker.MagicMock(doc_count=30)
            ),
            mocker.MagicMock(
                key='aLang', work_totals=mocker.MagicMock(doc_count=20)
            )
        ]

        assert APIUtils.formatLanguages(mockAggs, True) == [
            {'language': 'cLang', 'work_total': 30},
            {'language': 'aLang', 'work_total': 20},
            {'language': 'bLang', 'work_total': 10}
        ]

    def test_formatTotals(self):
        assert APIUtils.formatTotals([('test', 3), ('other', 6)]) ==\
            {'test': 3, 'other': 6}

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
            'status': 200,
            'timestamp': 'presentTimestamp',
            'responseType': 'test',
            'data': 'testData'
        })

    def test_formatPipeDelimitedData_string(self):
        assert APIUtils.formatPipeDelimitedData('test|object', ['one', 'two'])\
            == {'one': 'test', 'two': 'object'}

    def test_formatPipeDelimitedData_list(self):
        assert APIUtils.formatPipeDelimitedData(
            ['test|object', None, 'another|thing'], ['one', 'two']
        ) == [
            {'one': 'test', 'two': 'object'},
            {'one': 'another', 'two': 'thing'}
        ]

    def test_formatPipeDelimitedData_none(self):
        assert APIUtils.formatPipeDelimitedData(None, ['one', 'two']) is None

    def test_validatePassword_success(self):
        testHash = scrypt(b'testPswd', salt=b'testSalt', n=2**14, r=8, p=1)

        assert APIUtils.validatePassword('testPswd', testHash, b'testSalt')\
            is True

    def test_validatePassword_error(self):
        testHash = scrypt(b'testPswd', salt=b'testSalt', n=2**14, r=8, p=1)

        assert APIUtils.validatePassword('testError', testHash, b'testSalt')\
            is False

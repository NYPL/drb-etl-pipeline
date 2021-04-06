import pytest

from managers import SFRRecordManager


class TestSFRRecordManager:
    @pytest.fixture
    def testInstance(self, mocker):
        mocker.patch('managers.sfrRecord.Work')
        return SFRRecordManager(mocker.MagicMock(), {'2b': {'ger': 'deu'}})

    @pytest.fixture
    def testDCDWRecord(self, mocker):
        mockUUID = mocker.MagicMock()
        mockUUID.hex = 'testUUID'
        return mocker.MagicMock(
            uuid=mockUUID,
            title='Test Title',
            alternative=['Test Alt 1', 'Test Alt 2'],
            medium='testing',
            is_part_of=['test ser|1|series', 'test vol|1|volume'],
            has_version='testVersion',
            identifiers=['1|test', '2|isbn', '3|owi'],
            authors=['Test Author'],
            publisher='Test Publisher',
            spatial='Test Publication Place',
            contributors=['Contrib 1|printer', 'Contrib 2|||provider', 'Contrib 3|||translator'],
            subjects=['Subject 1', 'Subject 2', 'Subject 3'],
            dates=['Date 1', 'Date 2'],
            languages=['Language 1'],
            abstract='Test Abstract',
            table_of_contents='Test TOC',
            extent='Test Extent',
            requires=['true|government_doc', 'test|other'],
            has_part=[
                '|url1|test|test|{"cover": true}',
                '1|url2|test|test|{"test": "flag"}',
                '2|url3|test|test|'
            ],
            coverage=['tst|Test Location|1']
        )

    def test_initializer(self, testInstance, mocker):
        assert isinstance(testInstance.work, mocker.MagicMock)
        assert isinstance(testInstance.session, mocker.MagicMock)

    def test_mergeRecords(self, testInstance, mocker):
        recordMocks = mocker.patch.multiple(
            SFRRecordManager,
            dedupeIdentifiers=mocker.DEFAULT,
            dedupeLinks=mocker.DEFAULT
        )
        recordMocks['dedupeIdentifiers'].side_effect = [
            ['newEd1', 'newEd2'], ['item1'], ['item2'], ['newEd3'],
            ['item3'], ['item4'], ['work1']
        ]
        recordMocks['dedupeLinks'].side_effect = [
            ['url1'], ['url2'], ['url3'], ['url4']
        ]

        firstEdItems = [
            mocker.MagicMock(identifiers=['it1'], links=['url1', 'url2']),
            mocker.MagicMock(identifiers=['it2'], links=['url3'])
        ]
        secondEdItems = [
            mocker.MagicMock(identifiers=['it3'], links=['url4']),
            mocker.MagicMock(identifiers=['it4'], links=['url5', 'url6'])
        ]
        testInstance.work.editions = [
            mocker.MagicMock(identifiers=['id1', 'id2'], items=firstEdItems, dcdw_uuids=['uuid1', 'uuid2']),
            mocker.MagicMock(identifiers=['id3'], items=secondEdItems, dcdw_uuids=['uuid4'])
        ]
        testInstance.work.identifiers = ['wo1', 'wo2', 'wo3']

        testWork = mocker.MagicMock(id='wo1', uuid='uuid1')

        matchingEditions = [
            mocker.MagicMock(work_id=1, id='ed1', work=testWork, dcdw_uuids=['uuid1']),
            mocker.MagicMock(work_id=1, id='ed2', work=testWork, dcdw_uuids=['uuid2']),
            mocker.MagicMock(work_id=1, id='ed3', work=testWork, dcdw_uuids=['uuid3'])
        ]
        testInstance.session.query().filter().all.return_value = matchingEditions
        testInstance.session.merge.return_value = testInstance.work

        testUUIDsToDelete = testInstance.mergeRecords()

        assert testUUIDsToDelete == set(['uuid1'])

        assert testInstance.work.id == 1
        assert testInstance.work.identifiers == ['work1']
        assert testInstance.work.editions[0].id == 'ed1'
        assert testInstance.work.editions[1].identifiers == ['newEd3']
        assert testInstance.work.editions[0].items[0].identifiers == ['item1']
        assert testInstance.work.editions[1].items[1].links == ['url4']

        testInstance.session.query().filter().all.assert_called_once()
        testInstance.session.delete.assert_called_once_with(testWork)

        testInstance.session.merge.assert_called_once_with(testInstance.work)

    def test_dedupeIdentifiers(self, testInstance, mocker):
        testExistingIDs = {}
        mockIdentifiers = [
            mocker.MagicMock(identifier=1, authority='test', id=None),
            mocker.MagicMock(identifier=2, authority='test', id=None),
            mocker.MagicMock(identifier=3, authority='test', id=None),
            mocker.MagicMock(identifier=4, authority='test', id=None),
            mocker.MagicMock(identifier=2, authority='test', id=None),
        ]

        testInstance.session.query().filter().filter().all.return_value = [
            mocker.MagicMock(id=5, identifier=3, authority='test'),
            mocker.MagicMock(id=6, identifier=1, authority='test'),
        ]

        testIdentifiers = testInstance.dedupeIdentifiers(mockIdentifiers, testExistingIDs)

        assert len(testExistingIDs) == 4
        assert testExistingIDs[('test', 3)].id == 5
        assert testExistingIDs[('test', 2)].id == None
        assert len(testIdentifiers) == 4
        assert set([i.identifier for i in testIdentifiers]) == set([1, 2, 3, 4])
        assert set([getattr(i, 'id', None) for i in testIdentifiers]) == set([5, 6, None])
        testInstance.session.query().filter().filter().all.assert_called_once()

    def test_dedupeLinks(self, testInstance, mocker):
        mockLinks = [
            mocker.MagicMock(url='url1', id=None),
            mocker.MagicMock(url='url2', id=None),
            mocker.MagicMock(url='url3', id=None)
        ]
        testInstance.session.query().filter().first.side_effect = [
            None, mocker.MagicMock(id='item1'), None
        ]

        testLinks = testInstance.dedupeLinks(mockLinks)

        assert len(testLinks) == 3
        assert testInstance.session.query().filter().first.call_count == 3
        assert set([l.id for l in testLinks]) == set(['item1', None])

    def test_buildEditionStructure(self, testInstance, mocker):
        mockRecords = [
            mocker.MagicMock(uuid='uuid1'), mocker.MagicMock(uuid='uuid2'), mocker.MagicMock(uuid='uuid3')
        ]

        testEditions = testInstance.buildEditionStructure(
            mockRecords, [(1900, ['uuid1', 'uuid2', 'uuid4']), (2000, ['uuid3', 'uuid5'])]
        )

        assert testEditions[0][0] == 1900
        assert testEditions[0][1] == mockRecords[:2]
        assert testEditions[1][0] == 2000
        assert testEditions[1][1] == mockRecords[2:]

    def test_buildWork(self, testInstance, mocker):
        managerMocks = mocker.patch.multiple(
            SFRRecordManager,
            buildEditionStructure=mocker.DEFAULT,
            createEmptyWorkRecord=mocker.DEFAULT,
            buildEdition=mocker.DEFAULT
        )

        managerMocks['buildEditionStructure'].return_value = [
            (1900, ['instance1', 'instance2']),
            (2000, ['instance3', 'instance4', 'instance5'])
        ]
        managerMocks['createEmptyWorkRecord'].return_value = 'testWorkData'
        
        testWorkData = testInstance.buildWork('testRecords', 'testEditions')

        assert testWorkData == 'testWorkData'
        
        managerMocks['buildEditionStructure'].assert_called_once_with('testRecords', 'testEditions')
        managerMocks['createEmptyWorkRecord'].assert_called_once
        managerMocks['buildEdition'].assert_has_calls([
            mocker.call('testWorkData', 1900, ['instance1', 'instance2']),
            mocker.call('testWorkData', 2000, ['instance3', 'instance4', 'instance5']),
        ])

    def test_buildEdition(self, testInstance, mocker):
        mockEmptyEdition = mocker.patch.object(SFRRecordManager, 'createEmptyEditionRecord')
        mockEmptyEdition.return_value = {'title': 'Test Edition'}
        mockParse = mocker.patch.object(SFRRecordManager, 'parseInstance')

        testWorkData = {'editions': []}
        testInstance.buildEdition(testWorkData, 1900, ['instance1', 'instance2'])

        assert testWorkData['editions'] == [{'title': 'Test Edition', 'publication_date': 1900}]
        mockEmptyEdition.assert_called_once
        mockParse.assert_has_calls([
            mocker.call(testWorkData, {'title': 'Test Edition', 'publication_date': 1900}, 'instance1'),
            mocker.call(testWorkData, {'title': 'Test Edition', 'publication_date': 1900}, 'instance2')
        ])

    def test_parseInstance(self, testInstance, testDCDWRecord, mocker):
        mockItemBuild = mocker.patch.object(SFRRecordManager, 'buildItems')
        mockNormalizeDates = mocker.patch.object(SFRRecordManager, 'normalizeDates')
        mockNormalizeDates.return_value = ['Date 1', 'Date 2']
        testWork = SFRRecordManager.createEmptyWorkRecord()
        testEdition = SFRRecordManager.createEmptyEditionRecord()

        testInstance.parseInstance(testWork, testEdition, testDCDWRecord)

        assert list(testWork['title'].elements()) == ['Test Title']
        assert list(testWork['alt_titles'].elements()) == ['Test Alt 1', 'Test Alt 2']
        assert list(testEdition['alt_titles'].elements()) == ['Test Alt 1', 'Test Alt 2']
        assert list(testWork['medium'].elements()) == ['testing']
        assert list(testWork['series_data'].elements()) == ['test ser|1|series']
        assert list(testEdition['volume_data'].elements()) == ['test vol|1|volume']
        assert list(testEdition['edition_data'].elements()) == ['testVersion']
        assert list(testWork['authors']) == ['Test Author']
        assert list(testEdition['publishers']) == ['Test Publisher']
        assert list(testEdition['publication_place'].elements()) == ['Test Publication Place']
        assert list(testEdition['contributors']) == ['Contrib 1|printer']
        assert list(testWork['contributors']) == ['Contrib 3|||translator']
        assert testWork['subjects'] == set(['Subject 1', 'Subject 2', 'Subject 3'])
        assert testEdition['dates'] == set(['Date 1', 'Date 2'])
        assert testEdition['languages'] == set(['Language 1'])
        assert testWork['languages'] == set(['Language 1'])
        assert list(testEdition['summary'].elements()) == ['Test Abstract']
        assert list(testEdition['table_of_contents'].elements()) == ['Test TOC']
        assert list(testEdition['extent'].elements()) == ['Test Extent']
        assert testWork['measurements'] == set(['true|government_doc'])
        assert testEdition['measurements'] == set(['test|other'])
        assert testEdition['dcdw_uuids'] == ['testUUID']
        mockItemBuild.assert_called_once_with(testEdition, testDCDWRecord, set(['Contrib 2|||provider']))
        mockNormalizeDates.assert_called_once_with(['Date 1', 'Date 2'])

    def test_buildItems(self, testInstance, testDCDWRecord):
        testEditionData = {'items': [], 'links': []}

        testInstance.buildItems(testEditionData, testDCDWRecord, set(['Item Contrib 1']))

        assert testEditionData['links'][0] == 'url1|test|{"cover": true}'
        assert len(testEditionData['items']) == 3
        assert testEditionData['items'][2] is None
        assert testEditionData['items'][0]['links'][0] == 'url2|test|{"test": "flag"}'
        assert testEditionData['items'][1]['links'][0] == 'url3|test|'
        assert testEditionData['items'][0]['content_type'] == 'ebook'
        assert testEditionData['items'][1]['source'] == 'test'
        assert testEditionData['items'][1]['contributors'] == set(['Item Contrib 1'])
        assert testEditionData['items'][0]['identifiers'] == set(['1|test'])
        assert testEditionData['items'][1]['identifiers'] == set(['1|test'])
        assert testEditionData['items'][0]['physical_location'] == {'code': 'tst', 'name': 'Test Location'}

    def test_setPipeDelimitedData(self, mocker):
        mockParse = mocker.patch.object(SFRRecordManager, 'parseDelimitedEntry')
        mockParse.side_effect = [1, 2, 3]

        testParsedData = SFRRecordManager.setPipeDelimitedData([1, 2, 3], 'testFields', dType='testType', dParser='testFunction')

        assert testParsedData == [1, 2, 3]
        mockParse.assert_has_calls([
            mocker.call(1, 'testFields', 'testType', 'testFunction'),
            mocker.call(2, 'testFields', 'testType', 'testFunction'),
            mocker.call(3, 'testFields', 'testType', 'testFunction')
        ])

    def test_parseDelimitedEntry_no_function_no_type(self):
        parsedData = SFRRecordManager.parseDelimitedEntry('1|2|3', ['f1', 'f2', 'f3'], None, None)

        assert parsedData == {'f1': '1', 'f2': '2', 'f3': '3'}

    def test_parseDelimitedEntry_custom_function_no_type(self, mocker):
        mockParser = mocker.MagicMock()
        mockParser.return_value = {'tests': [1, 2, 3]}
        parsedData = SFRRecordManager.parseDelimitedEntry('1|2|3', ['f1', 'f2', 'f3'], None, dParser=mockParser)

        assert parsedData == {'tests': [1, 2, 3]}

    def test_parseDelimitedEntry_custom_function_custom_type(self, mocker):
        mockParser = mocker.MagicMock()
        mockParser.return_value = {'tests': [1, 2, 3]}
        parsedData = SFRRecordManager.parseDelimitedEntry('1|2|3', ['f1', 'f2', 'f3'], dType=mocker.MagicMock, dParser=mockParser)

        assert parsedData.tests == [1, 2, 3]

    def test_getLanguage_all_values_match_full_name(self, testInstance):
        testLanguage = testInstance.getLanguage({'language': 'English'})

        assert testLanguage['iso_2'] == 'en'
        assert testLanguage['iso_3'] == 'eng'
        assert testLanguage['language'] == 'English'

    def test_getLanguage_all_values_match_iso_2(self, testInstance):
        testLanguage = testInstance.getLanguage({'iso_2': 'de'})

        assert testLanguage['iso_2'] == 'de'
        assert testLanguage['iso_3'] == 'deu'
        assert testLanguage['language'] == 'German'

    def test_getLanguage_all_values_match_iso_3(self, testInstance):
        testLanguage = testInstance.getLanguage({'iso_3': 'zho'})

        assert testLanguage['iso_2'] == 'zh'
        assert testLanguage['iso_3'] == 'zho'
        assert testLanguage['language'] == 'Chinese'

    def test_getLanguage_all_values_match_iso_639_2_b(self, testInstance):
        testLanguage = testInstance.getLanguage({'iso_3': 'ger'})

        assert testLanguage['iso_2'] == 'de'
        assert testLanguage['iso_3'] == 'deu'
        assert testLanguage['language'] == 'German'

    def test_parseLinkFlags(self):
        assert (
            SFRRecordManager.parseLinkFlags({'flags': '{"testing": true}', 'key': 'value'})\
                ==\
            {'flags': {'testing': True}, 'key': 'value'}
        )

    def test_getLanguage_all_values_match_missing_iso_2(self, testInstance):
        testLanguage = testInstance.getLanguage({'language': 'Klingon'})

        assert testLanguage['iso_2'] is None
        assert testLanguage['iso_3'] == 'tlh'
        assert testLanguage['language'] == 'Klingon'

    def test_agentParser_single_agent(self, testInstance):
        testAgents = testInstance.agentParser(['Test|||author'], ['name', 'viaf', 'lcnaf', 'role'])

        assert testAgents == [{'name': 'Test', 'viaf': '', 'lcnaf': '', 'roles': ['author']}]

    def test_agentParser_multiple_agents(self, testInstance):
        inputAgents = ['Author|||author', 'Publisher|1234||publisher']
        testAgents = testInstance.agentParser(inputAgents, ['name', 'viaf', 'lcnaf', 'role'])

        assert testAgents == [
            {'name': 'Author', 'viaf': '', 'lcnaf': '', 'roles': ['author']},
            {'name': 'Publisher', 'viaf': '1234', 'lcnaf': '', 'roles': ['publisher']}
        ]

    def test_agentParser_multiple_agents_overlap(self, testInstance):
        inputAgents = ['Author|||author', 'Publisher|1234||publisher', 'Pub Alt Name|1234|n9876|other']
        testAgents = testInstance.agentParser(inputAgents, ['name', 'viaf', 'lcnaf', 'role'])

        assert testAgents[0]['name'] == 'Author'
        assert testAgents[1]['name'] == 'Publisher'
        assert testAgents[1]['viaf'] == '1234'
        assert testAgents[1]['lcnaf'] == 'n9876'
        assert set(testAgents[1]['roles']) == set(['publisher', 'other'])


    def test_agentParser_multiple_agents_empty_and_overlap(self, testInstance):
        inputAgents = ['Author||n9876|author', 'Author Alt|1234|n9876|illustrator', '|other']
        testAgents = testInstance.agentParser(inputAgents, ['name', 'viaf', 'lcnaf', 'role'])

        assert len(testAgents) == 1
        assert testAgents[0]['name'] == 'Author'
        assert testAgents[0]['viaf'] == '1234'
        assert testAgents[0]['lcnaf'] == 'n9876'
        assert set(testAgents[0]['roles']) == set(['author', 'illustrator'])

    def test_agentParser_multiple_agents_jw_match(self, testInstance):
        inputAgents = ['Author T. Tester|||author', 'Author Tester (1950-)|||illustrator', '|other']
        testAgents = testInstance.agentParser(inputAgents, ['name', 'viaf', 'lcnaf', 'role'])

        assert len(testAgents) == 1
        assert testAgents[0]['name'] == 'Author T. Tester'
        assert testAgents[0]['viaf'] == ''
        assert testAgents[0]['lcnaf'] == ''
        assert set(testAgents[0]['roles']) == set(['author', 'illustrator'])

    def test_setSortTitle_w_stops(self, testInstance):
        testInstance.work.languages = [{'iso_3': 'eng'}]
        testInstance.work.title = 'The Test Title'

        testInstance.setSortTitle()

        assert testInstance.work.sort_title == 'test title'

    def test_setSortTitle_wo_stops(self, testInstance):
        testInstance.work.languages = [{'iso_3': 'tlh'}]
        testInstance.work.title = 'Kplagh: Batleth Handbook'

        testInstance.setSortTitle()

        assert testInstance.work.sort_title == 'kplagh: batleth handbook'

    def test_normalizeDates(self, testInstance):
        testDates = testInstance.normalizeDates(['1999.|test', '2000|other', 'sometime 1900-12 [pub]|other'])

        assert sorted(testDates) == sorted(['1999|test', '2000|other', '1900-12|other'])

    def test_subjectParser(self, testInstance, mocker):
        mockSetDelimited = mocker.patch.object(SFRRecordManager, 'setPipeDelimitedData')
        mockSetDelimited.return_value = ['testSubject']
        testInstance.subjectParser(['Test||', 'test.|auth|1234', '|auth|56768'])

        assert testInstance.work.subjects == ['testSubject']
        mockSetDelimited.assert_called_once_with(
            ['Test|auth|1234'], ['heading', 'authority', 'controlNo']
        )

    def test_subjectParser_unexpected_heading(self, testInstance, mocker):
        mockSetDelimited = mocker.patch.object(SFRRecordManager, 'setPipeDelimitedData')
        mockSetDelimited.return_value = ['testSubject']
        testInstance.subjectParser(['Test|Other|auth|1234'])

        assert testInstance.work.subjects == ['testSubject']
        mockSetDelimited.assert_called_once_with(
            ['Test,Other|auth|1234'], ['heading', 'authority', 'controlNo']
        )

import datetime
import pytest
from sqlalchemy import column

from model import Edition, Link
from processes import CoverProcess


class TestCoverProcess:
    @pytest.fixture
    def testProcess(self):
        class TestCoverProcess(CoverProcess):
            def __init__(self, *args):
                self.fileBucket = 'test_aws_bucket'
                self.batchSize = 3

        return TestCoverProcess()

    def test_runProcess(self, testProcess, mocker):
        processMocks = mocker.patch.multiple(CoverProcess,
            generateQuery=mocker.DEFAULT,
            fetchEditionCovers=mocker.DEFAULT,
            saveRecords=mocker.DEFAULT,
            commitChanges=mocker.DEFAULT
        )
        processMocks['generateQuery'].return_value = 'testQuery'

        testProcess.runProcess()

        processMocks['generateQuery'].assert_called_once()
        processMocks['fetchEditionCovers'].assert_called_once_with('testQuery')
        processMocks['saveRecords'].assert_called_once()
        processMocks['commitChanges'].assert_called_once()

    def test_generateQuery_complete(self, testProcess, mocker):
        mockQuery = mocker.MagicMock()
        mockQuery.filter.return_value = 'testQuery'

        mockSubQuery = mocker.MagicMock()
        mockSubQuery.select_from().join().distinct().filter.return_value = ['sub']

        testProcess.session = mocker.MagicMock()
        testProcess.session.query.side_effect = [mockQuery, mockSubQuery]

        testProcess.process = 'complete'
        testQuery = testProcess.generateQuery()

        assert testQuery == 'testQuery'
        assert mockQuery.filter.call_args[0][0].compare(~Edition.id.in_(['sub']))
        assert testProcess.session.query.call_count == 2
        mockSubQuery.select_from().join().distinct().filter.call_args[0][0].compare(Link.flags['cover'] == 'true')

    def test_generateQuery_custom_date(self, testProcess, mocker):
        mockQuery = mocker.MagicMock()
        mockQuery.filter.return_value = 'testQuery'

        mockSubQuery = mocker.MagicMock()
        mockSubQuery.select_from().join().distinct().filter.return_value = ['sub'] 

        testProcess.session = mocker.MagicMock()
        testProcess.session.query.side_effect = [mockQuery, mockSubQuery]

        testProcess.process = 'custom'
        testProcess.ingestPeriod = '2020-01-01'
        testQuery = testProcess.generateQuery()

        assert testQuery == 'testQuery'
        assert mockQuery.filter.call_args[0][0].compare(~Edition.id.in_(['sub']))
        testDate = datetime.datetime.strptime('2020-01-01', '%Y-%m-%d')
        assert mockQuery.filter.call_args[0][1].compare(Edition.date_modified >= testDate)

    def test_generateQuery_daily(self, testProcess, mocker):
        mockQuery = mocker.MagicMock()
        mockQuery.filter.return_value = 'testQuery'

        mockSubQuery = mocker.MagicMock()
        mockSubQuery.select_from().join().distinct().filter.return_value = ['sub']

        testProcess.session = mocker.MagicMock()
        testProcess.session.query.side_effect = [mockQuery, mockSubQuery]

        testStartDate = datetime.datetime(1900, 1, 1)
        testQueryDate = testStartDate - datetime.timedelta(hours=24)
        mockDatetime = mocker.patch('processes.covers.datetime')
        mockDatetime.utcnow.return_value = testStartDate

        testProcess.process = 'daily'
        testProcess.ingestPeriod = None
        testQuery = testProcess.generateQuery()

        assert testQuery == 'testQuery'
        assert mockQuery.filter.call_args[0][0].compare(~Edition.id.in_(['sub']))
        assert mockQuery.filter.call_args[0][1].compare(Edition.date_modified >= testQueryDate)

    def test_fetchEditionCovers(self, testProcess, mocker):
        processMocks = mocker.patch.multiple(CoverProcess,
            searchForCover=mocker.DEFAULT,
            storeFoundCover=mocker.DEFAULT,
            windowedQuery=mocker.DEFAULT
        )
        processMocks['searchForCover'].side_effect = ['manager1', None, 'manager2']
        processMocks['windowedQuery'].return_value = ['ed1', 'ed2', 'ed3']

        testProcess.fetchEditionCovers('mockQuery')

        processMocks['searchForCover'].assert_has_calls([
            mocker.call('ed1'), mocker.call('ed2'), mocker.call('ed3')
        ])
        processMocks['storeFoundCover'].assert_has_calls([
            mocker.call('manager1', 'ed1'), mocker.call('manager2', 'ed3')
        ])

    def test_searchForCover_success(self, testProcess, mocker):
        mockIdentifierGet = mocker.patch.object(CoverProcess, 'getEditionIdentifiers')
        mockIdentifierGet.return_value = [(1, 'test')]

        mockManager = mocker.MagicMock()
        mockManager.fetchCover.return_value = True

        mockGenerator = mocker.patch('processes.covers.CoverManager')
        mockGenerator.return_value = mockManager

        testProcess.session = 'testSession'
        testManager = testProcess.searchForCover('testEdition')

        assert testManager == mockManager
        mockIdentifierGet.assert_called_once_with('testEdition')
        mockGenerator.assert_called_once_with([(1, 'test')], 'testSession')
        mockManager.fetchCover.assert_called_once()
        mockManager.fetchCoverFile.assert_called_once()
        mockManager.resizeCoverFile.assert_called_once()

    def test_searchForCover_missing(self, testProcess, mocker):
        mockIdentifierGet = mocker.patch.object(CoverProcess, 'getEditionIdentifiers')
        mockIdentifierGet.return_value = [(1, 'test')]

        mockManager = mocker.MagicMock()
        mockManager.fetchCover.return_value = False

        mockGenerator = mocker.patch('processes.covers.CoverManager')
        mockGenerator.return_value = mockManager

        testProcess.session = 'testSession'
        testManager = testProcess.searchForCover('testEdition')

        assert testManager == None
        mockIdentifierGet.assert_called_once_with('testEdition')
        mockGenerator.assert_called_once_with([(1, 'test')], 'testSession')
        mockManager.fetchCover.assert_called_once()
        mockManager.fetchCoverFile.assert_not_called()
        mockManager.resizeCoverFile.assert_not_called()

    def test_getEditionIdentifiers(self, testProcess, mocker):
        mockCheckRedis = mocker.patch.object(CoverProcess, 'checkSetRedis')
        mockCheckRedis.side_effect = [True, False]

        mockIdentifiers = [mocker.MagicMock(identifier=1, authority='test'), mocker.MagicMock(identifier=2, authority='test')]
        mockEdition = mocker.MagicMock(identifiers=mockIdentifiers)

        testIdentifiers = list(testProcess.getEditionIdentifiers(mockEdition))
        
        assert testIdentifiers == [(2, 'test')]
        mockCheckRedis.assert_has_calls([
            mocker.call('sfrCovers', 1, 'test', expirationTime=2592000),
            mocker.call('sfrCovers', 2, 'test', expirationTime=2592000)
        ])

    def test_storeFoundCover(self, testProcess, mocker):
        mockPut = mocker.patch.object(CoverProcess, 'putObjectInBucket')
        mockSave = mocker.patch.object(CoverProcess, 'bulkSaveObjects')

        mockFetcher = mocker.MagicMock(SOURCE='test', coverID=1)
        mockManager = mocker.MagicMock(fetcher=mockFetcher, coverFormat='tst', coverContent='testBytes')
        mockEdition = mocker.MagicMock(links=[])

        testProcess.records = set(['ed1', 'ed2'])
        testProcess.storeFoundCover(mockManager, mockEdition)

        assert list(testProcess.records) == []
        assert mockEdition.links[0].url == 'test_aws_bucket.s3.amazonaws.com/covers/test/1.tst'
        assert mockEdition.links[0].media_type == 'image/tst'
        assert mockEdition.links[0].flags == {'cover': True}
        assert mockSave.call_args[0][0] == set(['ed1', 'ed2', mockEdition])
        mockPut.assert_called_once_with('testBytes', 'covers/test/1.tst', 'test_aws_bucket')

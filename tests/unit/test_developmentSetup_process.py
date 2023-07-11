import csv
import gzip
import pytest
import requests
import sqlalchemy as sa

from tests.helper import TestHelpers
from processes import DevelopmentSetupProcess


class TestDevelopmentSetupProcess:
    @classmethod
    def setup_class(cls):
        TestHelpers.setEnvVars()

    @classmethod
    def teardown_class(cls):
        TestHelpers.clearEnvVars()

    @pytest.fixture
    def devInstance(self, mocker):
        class TestDevelopmentProcess(DevelopmentSetupProcess):
            def __init__(self, process, customFile, ingestPeriod):
                self.adminDBConnection = mocker.MagicMock()
                self.statics = {}
                self.es = mocker.MagicMock()

        return TestDevelopmentProcess('TestProcess', 'testFile', 'testDate')

    @pytest.fixture
    def hathiFilesData(self):
        return [
            {'created': '2020-01-01T00:00:00+0000', 'url': 'hathiUrl1'},
            {'created': '2019-01-01T00:00:00+0000', 'url': 'hathiUrl2'},
            {'created': '2018-01-01T00:00:00+0000', 'url': 'hathiUrl3'}
        ]

    @pytest.fixture
    def hathiTSV(self):
        rows = []
        for i in range(1000):
            rightsStmt = 'ic' if i % 3 == 0 else 'pd'
            rows.append([i, 'hathi', rightsStmt])

        return rows

    def test_runProcess(self, devInstance, mocker):
        mockGenerateEngine = mocker.patch.object(DevelopmentSetupProcess, 'generateEngine')
        mockInitializeDatabase = mocker.patch.object(DevelopmentSetupProcess, 'initializeDatabase')
        mockCreateSession = mocker.patch.object(DevelopmentSetupProcess, 'createSession')

        mockCreateElastic = mocker.patch.object(DevelopmentSetupProcess, 'createElasticConnection')
        mockCreateElasticIndex = mocker.patch.object(DevelopmentSetupProcess, 'createElasticSearchIndex')

        mockCreateRabbit = mocker.patch.object(DevelopmentSetupProcess, 'createRabbitConnection')
        mockCreateQueue = mocker.patch.object(DevelopmentSetupProcess, 'createOrConnectQueue')

        mockFetchHathi = mocker.patch.object(DevelopmentSetupProcess, 'fetchHathiSampleData')

        mockClassify = mocker.patch('processes.developmentSetup.ClassifyProcess')
        mockCatalog = mocker.patch('processes.developmentSetup.CatalogProcess')
        mockCluster = mocker.patch('processes.developmentSetup.ClusterProcess')

        devInstance.runProcess()

        mockGenerateEngine.assert_called_once()
        mockInitializeDatabase.assert_called_once()
        mockCreateSession.assert_called_once()
        mockCreateElastic.assert_called_once()
        mockCreateElasticIndex.assert_called_once()
        mockCreateRabbit.assert_called_once()
        mockCreateQueue.assert_has_calls([
            mocker.call('test_oclc_queue', 'test_oclc_key'),
            mocker.call('test_file_queue', 'test_file_key')
        ])
        mockFetchHathi.assert_called_once()

        mockClassify.assert_called_with('complete', None, None, None, None)
        mockCatalog.assert_called_with('complete', None, None, None, None)
        mockCluster.assert_called_with('complete', None, None, None, None)

    def test_initializeDB(self, devInstance, mocker):
        mockEngine = mocker.MagicMock()
        mockConnection = mocker.MagicMock(name='mockConnection')
        devInstance.adminDBConnection.engine = mockEngine
        mockEngine.connect.return_value.__enter__.return_value = mockConnection

        devInstance.initializeDB()

        devInstance.adminDBConnection.generateEngine.assert_called_once()
        mockConnection.connection.set_isolation_level.assert_called_once()
        createDBCall, createUserCall, grantPrivilegesCall = mockConnection.execute.call_args_list
        assert createDBCall[0][0].compare(sa.text('CREATE DATABASE test_psql_name'))
        assert createUserCall[0][0].compare(
            sa.text('CREATE USER test_psql_user WITH PASSWORD \'test_psql_pswd\''),
        )
        assert grantPrivilegesCall[0][0].compare(
            sa.text('GRANT ALL PRIVILEGES ON DATABASE test_psql_name TO test_psql_user'),
        )
        mockEngine.dispose.assert_called_once()

    def test_fetchHathiSampleData(self, devInstance, mocker):
        fetchMocks = mocker.patch.multiple(
            DevelopmentSetupProcess,
            importFromHathiTrustDataFile=mocker.DEFAULT,
            saveRecords=mocker.DEFAULT,
            commitChanges=mocker.DEFAULT
        )

        devInstance.fetchHathiSampleData()

        fetchMocks['importFromHathiTrustDataFile'].assert_called_once()
        fetchMocks['saveRecords'].assert_called_once()
        fetchMocks['commitChanges'].assert_called_once()

    def test_importFromHathiTrustDataFile_standard(self, devInstance, hathiFilesData, hathiTSV, mocker):
        mockRequest = mocker.patch.object(requests, 'get')
        mockListResponse = mocker.MagicMock()
        mockTSVResponse = mocker.MagicMock()
        mockRequest.side_effect = [mockListResponse, mockTSVResponse]
        mockListResponse.status_code = 200
        mockListResponse.json.return_value = hathiFilesData

        mockOpen = mocker.patch('processes.developmentSetup.open')
        mockTSV = mocker.MagicMock()
        mockOpen.return_value.__enter__.return_value = mockTSV

        mockGzip = mocker.patch.object(gzip, 'open')
        mockCSVReader = mocker.patch.object(csv, 'reader')
        mockCSVReader.return_value = hathiTSV

        mockHathiMapping = mocker.patch('processes.developmentSetup.HathiMapping')
        mockAddDCDW = mocker.patch.object(DevelopmentSetupProcess, 'addDCDWToUpdateList')

        devInstance.importFromHathiTrustDataFile()

        mockRequest.assert_has_calls([
            mocker.call('test_hathi_url'), mocker.call('hathiUrl1')
        ])
        mockTSV.write.assert_called_once
        mockCSVReader.assert_called_once
        assert mockHathiMapping.call_count == 334
        assert mockAddDCDW.call_count == 334

    def test_importFromHathiTrustDataFile_error(self, devInstance, mocker):
        mockRequest = mocker.patch.object(requests, 'get')
        mockResponse = mocker.MagicMock()
        mockResponse.status_code = 500

        with pytest.raises(IOError):
            devInstance.importFromHathiTrustDataFile()
            mockRequest.assert_called_once

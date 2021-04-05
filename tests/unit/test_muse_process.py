import csv
from datetime import datetime
import pytest
import requests
from requests.exceptions import HTTPError

from processes.muse import MUSEProcess, MUSEError
from tests.helper import TestHelpers


class TestMUSEProcess:
    @classmethod
    def setup_class(cls):
        TestHelpers.setEnvVars()

    @classmethod
    def teardown_class(cls):
        TestHelpers.clearEnvVars()

    @pytest.fixture
    def testProcess(self):
        class TestMUSE(MUSEProcess):
            def __init__(self):
                self.s3Bucket = 'test_aws_bucket'
        
        return TestMUSE()

    @pytest.fixture
    def testMUSEPage(self):
        return open('./tests/fixtures/muse_book_42.html', 'r').read()

    @pytest.fixture
    def testMUSEPageUnreleased(self):
        return open('./tests/fixtures/muse_book_63320.html', 'r').read()

    @pytest.fixture
    def testBookCSV(self):
        return [
            ['Header 1'],
            ['Header 2'],
            ['Header 3'],
            ['Header 4'],
            [0, 1, 2, 3, 4, 5, 6, 'row1', 8, 9, '2020-01-01'],
            [0, 1, 2, 3, 4, 5, 6, 'row2', 8, 9],
            [0, 1, 2, 3, 4, 5, 6, 'row3', 8, 9, '2020-01-01'],
        ]

    def test_runProcess_daily(self, testProcess, mocker):
        mockImport = mocker.patch.object(MUSEProcess, 'importMARCRecords')
        mockSave = mocker.patch.object(MUSEProcess, 'saveRecords')
        mockCommit = mocker.patch.object(MUSEProcess, 'commitChanges')

        testProcess.process = 'daily'
        testProcess.runProcess()

        mockImport.assert_called_once
        mockSave.assert_called_once
        mockCommit.assert_called_once

    def test_runProcess_complete(self, testProcess, mocker):
        mockImport = mocker.patch.object(MUSEProcess, 'importMARCRecords')
        mockSave = mocker.patch.object(MUSEProcess, 'saveRecords')
        mockCommit = mocker.patch.object(MUSEProcess, 'commitChanges')

        testProcess.process = 'complete'
        testProcess.runProcess()

        mockImport.assert_called_once_with(full=True)
        mockSave.assert_called_once
        mockCommit.assert_called_once

    def test_runProcess_custom(self, testProcess, mocker):
        mockImport = mocker.patch.object(MUSEProcess, 'importMARCRecords')
        mockSave = mocker.patch.object(MUSEProcess, 'saveRecords')
        mockCommit = mocker.patch.object(MUSEProcess, 'commitChanges')

        testProcess.process = 'custom'
        testProcess.ingestPeriod = 'customTimestamp'
        testProcess.runProcess()

        mockImport.assert_called_once_with(startTimestamp='customTimestamp')
        mockSave.assert_called_once
        mockCommit.assert_called_once

    def test_importMARCRecords_daily(self, testProcess, mocker):
        processMocks = mocker.patch.multiple(MUSEProcess,
            downloadRecordUpdates=mocker.DEFAULT,
            downloadMARCRecords=mocker.DEFAULT,
            recordToBeUpdated=mocker.DEFAULT,
            parseMuseRecord=mocker.DEFAULT,
        )
        processMocks['recordToBeUpdated'].side_effect = [True, False, True, True]
        processMocks['downloadMARCRecords'].return_value = 'mockFile'
        processMocks['parseMuseRecord'].side_effect = [None, MUSEError('test'), None]

        mockDatetime = mocker.patch('processes.muse.datetime')
        mockDatetime.utcnow.return_value = datetime(1900, 1, 2, 12, 0, 0)

        mockReader = mocker.patch('processes.muse.MARCReader')
        mockReader.return_value = ['rec1', 'rec2', 'rec3', 'rec4']

        testProcess.importMARCRecords()

        processMocks['downloadRecordUpdates'].assert_called_once()
        processMocks['downloadMARCRecords'].assert_called_once()
        mockReader.assert_called_once_with('mockFile')
        testDate = datetime(1900, 1, 1, 12, 0, 0)
        processMocks['recordToBeUpdated'].assert_has_calls([
            mocker.call('rec1', testDate), mocker.call('rec2', testDate),
            mocker.call('rec3', testDate), mocker.call('rec4', testDate), 
        ])
        processMocks['parseMuseRecord'].assert_has_calls([
            mocker.call('rec1'), mocker.call('rec3'), mocker.call('rec4')
        ])

    def test_importMARCRecords_custom(self, testProcess, mocker):
        processMocks = mocker.patch.multiple(MUSEProcess,
            downloadRecordUpdates=mocker.DEFAULT,
            downloadMARCRecords=mocker.DEFAULT,
            recordToBeUpdated=mocker.DEFAULT,
            parseMuseRecord=mocker.DEFAULT,
        )
        processMocks['recordToBeUpdated'].side_effect = [True, False, True, True]
        processMocks['downloadMARCRecords'].return_value = 'mockFile'
        processMocks['parseMuseRecord'].side_effect = [None, MUSEError('test'), None]

        mockReader = mocker.patch('processes.muse.MARCReader')
        mockReader.return_value = ['rec1', 'rec2', 'rec3', 'rec4']

        testProcess.importMARCRecords(startTimestamp='2020-01-01')

        processMocks['downloadRecordUpdates'].assert_called_once()
        processMocks['downloadMARCRecords'].assert_called_once()
        mockReader.assert_called_once_with('mockFile')
        testDate = datetime(2020, 1, 1)
        processMocks['recordToBeUpdated'].assert_has_calls([
            mocker.call('rec1', testDate), mocker.call('rec2', testDate),
            mocker.call('rec3', testDate), mocker.call('rec4', testDate), 
        ])
        processMocks['parseMuseRecord'].assert_has_calls([
            mocker.call('rec1'), mocker.call('rec3'), mocker.call('rec4')
        ])

    def test_importMARCRecords_full(self, testProcess, mocker):
        processMocks = mocker.patch.multiple(MUSEProcess,
            downloadRecordUpdates=mocker.DEFAULT,
            downloadMARCRecords=mocker.DEFAULT,
            recordToBeUpdated=mocker.DEFAULT,
            parseMuseRecord=mocker.DEFAULT,
        )
        processMocks['downloadMARCRecords'].return_value = 'mockFile'
        processMocks['parseMuseRecord'].side_effect = [None, MUSEError('test'), None, None]

        mockReader = mocker.patch('processes.muse.MARCReader')
        mockReader.return_value = ['rec1', 'rec2', 'rec3', 'rec4']

        testProcess.importMARCRecords(full=True)

        processMocks['downloadRecordUpdates'].assert_called_once()
        processMocks['downloadMARCRecords'].assert_called_once()
        mockReader.assert_called_once_with('mockFile')
        processMocks['recordToBeUpdated'].assert_not_called()
        processMocks['parseMuseRecord'].assert_has_calls([
            mocker.call('rec1'), mocker.call('rec2'), mocker.call('rec3'), mocker.call('rec4')
        ])

    def test_downloadMARCRecords_success(self, testProcess, mocker):
        mockGet = mocker.patch.object(requests, 'get')
        mockResp = mocker.MagicMock()
        mockResp.iter_content.return_value = [b'm', b'a', b'r', b'c']
        mockGet.return_value = mockResp

        testRecords = testProcess.downloadMARCRecords()

        assert testRecords.read() == b'marc'
        mockGet.assert_called_once_with('test_muse_url', stream=True, timeout=30)

    def test_downloadMARCRecords_failure(self, testProcess, mocker):
        mockGet = mocker.patch.object(requests, 'get')
        mockResp = mocker.MagicMock()
        mockResp.raise_for_status.side_effect = HTTPError
        mockGet.return_value = mockResp

        with pytest.raises(Exception):
            testProcess.downloadMARCRecords()

    def test_downloadRecordUpdates_success(self, testProcess, testBookCSV, mocker):
        mockGet = mocker.patch.object(requests, 'get')
        mockResp = mocker.MagicMock()
        mockResp.iter_lines.return_value = 'testFile'
        mockGet.return_value = mockResp

        mockCSV = mocker.patch.object(csv, 'reader')
        mockCSV.return_value = iter(testBookCSV)

        testProcess.downloadRecordUpdates()

        assert testProcess.updateDates == {'row1': datetime(2020, 1, 1), 'row3': datetime(2020, 1, 1)}
        mockGet.assert_called_once_with('test_muse_csv', stream=True, timeout=30)
        mockResp.iter_lines.assert_called_once_with(decode_unicode=True)
        mockCSV.assert_called_once_with('testFile', skipinitialspace=True)

    def test_downloadRecordUpdates_failure(self, testProcess, mocker):
        mockGet = mocker.patch.object(requests, 'get')
        mockResp = mocker.MagicMock()
        mockResp.raise_for_status.side_effect = HTTPError
        mockGet.return_value = mockResp

        with pytest.raises(Exception):
            testProcess.downloadRecordUpdates()

    def test_recordToBeUpdated_true(self, testProcess, mocker):
        mockRecord = mocker.MagicMock()
        mockRecord.get_fields.return_value = [{'u': 'testURL/'}]

        testProcess.updateDates = {'testURL': datetime(2020, 1, 1)}

        assert testProcess.recordToBeUpdated(mockRecord, datetime(1900, 1, 1)) == True

    def test_recordToBeUpdated_false(self, testProcess, mocker):
        mockRecord = mocker.MagicMock()
        mockRecord.get_fields.return_value = [{'u': 'testURL/'}]

        testProcess.updateDates = {'testURL': datetime(1900, 1, 1)}

        assert testProcess.recordToBeUpdated(mockRecord, datetime(2020, 1, 1)) == False

    def test_parseMuseRecord(self, testProcess, mocker):
        mockRecord = mocker.MagicMock()
        mockRecord.source_id = 'muse1'
        mockRecord.has_part = ['1|testURL|muse|type|flags']

        mockMapping = mocker.MagicMock()
        mockMapping.record = mockRecord
        mockMapper = mocker.patch('processes.muse.MUSEMapping')
        mockMapper.return_value = mockMapping

        processMocks = mocker.patch.multiple(MUSEProcess,
            constructPDFManifest=mocker.DEFAULT,
            createManifestInS3=mocker.DEFAULT,
            addDCDWToUpdateList=mocker.DEFAULT
        )

        processMocks['constructPDFManifest'].return_value = 'testManifest'
        processMocks['createManifestInS3'].return_value = 'testS3URL'

        testProcess.parseMuseRecord('testMARC')

        mockMapper.assert_called_once_with('testMARC')
        mockMapping.applyMapping.assert_called_once
        processMocks['constructPDFManifest'].assert_called_once_with('testURL', 'type', mockRecord)
        processMocks['createManifestInS3'].assert_called_once_with('testManifest', 'muse1')
        mockMapping.addHasPartLink.assert_called_once_with(
            'testS3URL', 'application/webpub+json', '{"reader": true, "download": false, "catalog": false}'
        )
        processMocks['addDCDWToUpdateList'].assert_called_once_with(mockMapping)

    def test_constructPDFManifest(self, testProcess, testMUSEPage, mocker):
        mockLoad = mocker.patch.object(MUSEProcess, 'loadMusePage')
        mockLoad.return_value = testMUSEPage

        mockManifest = mocker.MagicMock()
        mockManifestConstructor = mocker.patch('processes.muse.WebpubManifest')
        mockManifestConstructor.return_value = mockManifest

        testManifest = testProcess.constructPDFManifest('testLink', 'testType', 'testRecord')

        assert testManifest == mockManifest

        mockLoad.assert_called_once_with('testLink')
        mockManifestConstructor.assert_called_once_with('testLink', 'testType')
        mockManifest.addMetadata.assert_called_once_with('testRecord')

        mockManifest.addSection.assert_has_calls([
            mocker.call('Part One. Reading Reading Historically', ''),
            mocker.call('PART TWO. Contextual Receptions, Reading Experiences, and Patterns of Response: Four Case Studies', '')
        ])

        mockManifest.addChapter.assert_has_calls([
            mocker.call('https://muse.jhu.edu/chapter/440/pdf', 'Cover'),
            mocker.call('https://muse.jhu.edu/chapter/2183675/pdf', 'Title Page'),
            mocker.call('https://muse.jhu.edu/chapter/2183674/pdf', 'Copyright'),
            mocker.call('https://muse.jhu.edu/chapter/2183673/pdf', 'Dedication'),
            mocker.call('https://muse.jhu.edu/chapter/441/pdf', 'Contents'),
            mocker.call('https://muse.jhu.edu/chapter/442/pdf', 'Preface'),
            mocker.call('https://muse.jhu.edu/chapter/444/pdf', 'Chapter 1. Historical Hermeneutics, Reception Theory, and the Social Conditions of Reading in Antebellum America'),
            mocker.call('https://muse.jhu.edu/chapter/445/pdf', 'Chapter 2. Interpretive Strategies and Informed Reading in the Antebellum Public Sphere'),
            mocker.call('https://muse.jhu.edu/chapter/6239/pdf', 'Chapter 3. “These Days of Double Dealing”: Informed Response, Reader Appropriation, and the Tales of Poe'),
            mocker.call('https://muse.jhu.edu/chapter/6240/pdf', 'Chapter 4. Multiple Audiences and Melville’s Fiction: Receptions, Recoveries, and Regressions'),
            mocker.call('https://muse.jhu.edu/chapter/6241/pdf', 'Chapter 5. Response as (Re)construction: The Reception of Catharine Sedgwick’s Novels'),
            mocker.call('https://muse.jhu.edu/chapter/6242/pdf', 'Chapter 6. Mercurial Readings: The Making and Unmaking of Caroline Chesebro’'),
            mocker.call('https://muse.jhu.edu/chapter/6243/pdf', 'Conclusion. American Literary History and the Historical Study of Interpretive Practices'),
            mocker.call('https://muse.jhu.edu/chapter/6244/pdf', 'Notes'),
            mocker.call('https://muse.jhu.edu/chapter/6245/pdf', 'Index')
        ])

        mockManifest.closeSection.assert_has_calls([mocker.call(), mocker.call()])

    def test_constructPDFManifest_muse_error(self, testProcess, testMUSEPageUnreleased, mocker):
        mockLoad = mocker.patch.object(MUSEProcess, 'loadMusePage')
        mockLoad.return_value = testMUSEPageUnreleased

        mockManifest = mocker.MagicMock()
        mockManifestConstructor = mocker.patch('processes.muse.WebpubManifest')
        mockManifestConstructor.return_value = mockManifest

        mockRecord = mocker.MagicMock()
        mockRecord.source_id = 1

        with pytest.raises(MUSEError):
            testProcess.constructPDFManifest('testLink', 'testType', mockRecord)

    def test_constructPDFManifest_error(self, testProcess, mocker):
        mockLoad = mocker.patch.object(MUSEProcess, 'loadMusePage')
        mockLoad.side_effect = Exception

        assert testProcess.constructPDFManifest('testLink', 'testType', 'testRecord') == None

    def test_loadMusePage_success(self, testProcess, mocker):
        mockGet = mocker.patch.object(requests, 'get')
        mockResp = mocker.MagicMock()
        mockResp.status_code = 200
        mockResp.text = 'testHTML'
        mockGet.return_value = mockResp

        assert testProcess.loadMusePage('testLink') == 'testHTML'
        mockGet.assert_called_once_with('testLink', timeout=15, headers={'User-agent': 'Mozilla/5.0'})

    def test_loadMusePage_error(self, testProcess, mocker):
        mockGet = mocker.patch.object(requests, 'get')
        mockResp = mocker.MagicMock()
        mockResp.status_code = 500
        mockGet.return_value = mockResp

        with pytest.raises(Exception):
            testProcess.loadMusePage('testLink')

    def test_createManifestInS3(self, testProcess, mocker):
        mockPut = mocker.patch.object(MUSEProcess, 'putObjectInBucket')

        mockManifest = mocker.MagicMock()
        mockManifest.links = []
        mockManifest.toJson.return_value = 'testJSON'

        testURL = testProcess.createManifestInS3(mockManifest, 1)

        assert testURL == 'https://test_aws_bucket.s3.amazonaws.com/manifests/muse/1.json'
        assert mockManifest.links[0] == {'href': testURL, 'type': 'application/webpub+json', 'rel': 'self'}
        mockPut.assert_called_once_with(b'testJSON', 'manifests/muse/1.json', 'test_aws_bucket')

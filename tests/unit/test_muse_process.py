import pytest
import requests

from processes import MUSEProcess
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

        mockImport.assert_called_once_with(fullOrPartial=True)
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

    def test_importMARCRecords(self, testProcess, mocker):
        mockDownload = mocker.patch.object(MUSEProcess, 'downloadMARCRecords')
        mockDownload.return_value = 'mockFile'

        mockReader = mocker.patch('processes.muse.MARCReader')
        mockReader.return_value = ['rec1', 'rec2', 'rec3']

        mockParser = mocker.patch.object(MUSEProcess, 'parseMuseRecord')

        testProcess.importMARCRecords()

        mockDownload.assert_called_once
        mockReader.assert_called_once_with('mockFile')
        mockParser.assert_has_calls([mocker.call('rec1'), mocker.call('rec2'), mocker.call('rec3')])

    def test_downloadMARCRecords_success(self, testProcess, mocker):
        mockGet = mocker.patch.object(requests, 'get')
        mockResp = mocker.MagicMock()
        mockResp.status_code = 200
        mockResp.iter_content.return_value = [b'm', b'a', b'r', b'c']
        mockGet.return_value = mockResp

        testRecords = testProcess.downloadMARCRecords()

        assert testRecords.read() == b'marc'
        mockGet.assert_called_once_with('test_muse_url', stream=True, timeout=30)

    def test_downloadMARCRecords_failure(self, testProcess, mocker):
        mockGet = mocker.patch.object(requests, 'get')
        mockResp = mocker.MagicMock()
        mockResp.status_code = 500
        mockGet.return_value = mockResp

        with pytest.raises(Exception):
            testProcess.downloadMARCRecords()

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
        processMocks['constructPDFManifest'].assert_called_once_with('testURL', mockRecord)
        processMocks['createManifestInS3'].assert_called_once_with('testManifest', 'muse1')
        mockMapping.addHasPartLink.assert_called_once_with(
            'testS3URL', 'application/pdf+json', '{"reader": true, "download": false, "catalog": false}'
        )
        processMocks['addDCDWToUpdateList'].assert_called_once_with(mockMapping)

    def test_constructPDFManifest(self, testProcess, testMUSEPage, mocker):
        mockLoad = mocker.patch.object(MUSEProcess, 'loadMusePage')
        mockLoad.return_value = testMUSEPage

        mockManifest = mocker.MagicMock()
        mockManifestConstructor = mocker.patch('processes.muse.PDFManifest')
        mockManifestConstructor.return_value = mockManifest

        testManifest = testProcess.constructPDFManifest('testLink', 'testRecord')

        assert testManifest == mockManifest

        mockLoad.assert_called_once_with('testLink')
        mockManifestConstructor.assert_called_once_with('testLink')
        mockManifest.addMetadata.assert_called_once_with('testRecord')

        mockManifest.addSection.assert_has_calls([
            mocker.call('Part One. Reading Reading Historically', ''),
            mocker.call('PART TWO. Contextual Receptions, Reading Experiences, and Patterns of Response: Four Case Studies', '')
        ])

        mockManifest.addChapter.assert_has_calls([
            mocker.call('https://muse.jhu.edu/chapter/440/pdf', 'Cover', None),
            mocker.call('https://muse.jhu.edu/chapter/2183675/pdf', 'Title Page', 'pp. i-iii'),
            mocker.call('https://muse.jhu.edu/chapter/2183674/pdf', 'Copyright', 'p. iv'),
            mocker.call('https://muse.jhu.edu/chapter/2183673/pdf', 'Dedication', 'pp. v-vi'),
            mocker.call('https://muse.jhu.edu/chapter/441/pdf', 'Contents', 'pp. vii-viii'),
            mocker.call('https://muse.jhu.edu/chapter/442/pdf', 'Preface', 'pp. ix-xiv'),
            mocker.call('https://muse.jhu.edu/chapter/444/pdf', 'Chapter 1. Historical Hermeneutics, Reception Theory, and the Social Conditions of Reading in Antebellum America', 'pp. 3-35'),
            mocker.call('https://muse.jhu.edu/chapter/445/pdf', 'Chapter 2. Interpretive Strategies and Informed Reading in the Antebellum Public Sphere', 'pp. 36-84'),
            mocker.call('https://muse.jhu.edu/chapter/6239/pdf', 'Chapter 3. “These Days of Double Dealing”: Informed Response, Reader Appropriation, and the Tales of Poe', 'pp. 87-137'),
            mocker.call('https://muse.jhu.edu/chapter/6240/pdf', 'Chapter 4. Multiple Audiences and Melville’s Fiction: Receptions, Recoveries, and Regressions', 'pp. 138-200'),
            mocker.call('https://muse.jhu.edu/chapter/6241/pdf', 'Chapter 5. Response as (Re)construction: The Reception of Catharine Sedgwick’s Novels', 'pp. 201-255'),
            mocker.call('https://muse.jhu.edu/chapter/6242/pdf', 'Chapter 6. Mercurial Readings: The Making and Unmaking of Caroline Chesebro’', 'pp. 256-298'),
            mocker.call('https://muse.jhu.edu/chapter/6243/pdf', 'Conclusion. American Literary History and the Historical Study of Interpretive Practices', 'pp. 299-320'),
            mocker.call('https://muse.jhu.edu/chapter/6244/pdf', 'Notes', 'pp. 321-392'),
            mocker.call('https://muse.jhu.edu/chapter/6245/pdf', 'Index', 'pp. 393-403')
        ])

        mockManifest.closeSection.assert_has_calls([mocker.call(), mocker.call()])

    def test_constructPDFManifest_error(self, testProcess, mocker):
        mockLoad = mocker.patch.object(MUSEProcess, 'loadMusePage')
        mockLoad.side_effect = Exception

        assert testProcess.constructPDFManifest('testLink', 'testRecord') == None

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
        assert mockManifest.links[0] == {
            'rel': 'self', 'href': testURL, 'type': 'application/pdf+json'
        }
        mockPut.assert_called_once_with(b'testJSON', 'manifests/muse/1.json', 'test_aws_bucket')

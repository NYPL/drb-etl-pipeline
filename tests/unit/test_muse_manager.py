from bs4 import BeautifulSoup
import pytest
import requests
from requests.exceptions import ReadTimeout

from managers import MUSEManager, MUSEError
from tests.helper import TestHelpers


class TestMUSEManager:
    @classmethod
    def setup_class(cls):
        TestHelpers.setEnvVars()

    @classmethod
    def teardown_class(cls):
        TestHelpers.clearEnvVars()

    @pytest.fixture
    def testManager(self, mocker):
        class TestMUSE(MUSEManager):
            def __init__(self):
                self.record = mocker.MagicMock(record='testRecord')
                self.museID = 1
                self.link = 'testLink'
                self.mediaType = 'testType'
                self.s3Bucket = 'test_aws_bucket'

                self.pdfDownloadURL = None
                self.epubURL = None
                self.pdfWebpubManifest = None

        return TestMUSE()

    @pytest.fixture
    def testMUSEPage(self):
        return open('./tests/fixtures/muse_book_42.html', 'r').read()

    @pytest.fixture
    def testMUSEPageUnreleased(self):
        return open('./tests/fixtures/muse_book_63320.html', 'r').read()

    def test_parseMusePage_success(self, testManager, mocker):
        mockLoad = mocker.patch.object(MUSEManager, 'loadMusePage')
        mockLoad.return_value = 'testHTML'
        mockSoup = mocker.patch('managers.muse.BeautifulSoup')
        mockSoup.return_value = 'testSoup'

        testManager.parseMusePage()

        assert testManager.museSoup == 'testSoup'
        mockLoad.assert_called_once()
        mockSoup.assert_called_once_with('testHTML', features='lxml')

    def test_parseMusePage_error(self, testManager, mocker):
        mockLoad = mocker.patch.object(MUSEManager, 'loadMusePage')
        mockLoad.side_effect = ReadTimeout
        mockSoup = mocker.patch('managers.muse.BeautifulSoup')

        with pytest.raises(MUSEError):
            testManager.parseMusePage()

        mockSoup.assert_not_called()

    def test_identifyReadableVersions_w_pdf(self, testManager, mocker):
        baseSoup = mocker.MagicMock()
        chapterSoup = mocker.MagicMock()
        buttonSoup = mocker.MagicMock()
        buttonSoup.parent = {'href': '/pdfURL'}

        baseSoup.find.return_value = chapterSoup
        chapterSoup.find.side_effect = [buttonSoup, None]

        testManager.museSoup = baseSoup

        testManager.identifyReadableVersions()

        assert testManager.pdfDownloadURL == 'https://muse.jhu.edu/pdfURL'
        baseSoup.find.assert_called_once_with(id='available_items_list_wrap')
        chapterSoup.find.assert_has_calls([
            mocker.call(alt='Download PDF'), mocker.call(alt='Download EPUB')
        ])

    def test_identifyReadableVersions_w_epub(self, testManager, mocker):
        baseSoup = mocker.MagicMock()
        chapterSoup = mocker.MagicMock()
        buttonSoup = mocker.MagicMock()
        buttonSoup.parent = {'href': '/epubURL'}

        baseSoup.find.return_value = chapterSoup
        chapterSoup.find.side_effect = [None, buttonSoup]

        testManager.museSoup = baseSoup

        testManager.identifyReadableVersions()

        assert testManager.epubURL == 'https://muse.jhu.edu/epubURL'
        baseSoup.find.assert_called_once_with(id='available_items_list_wrap')
        chapterSoup.find.assert_has_calls([
            mocker.call(alt='Download PDF'), mocker.call(alt='Download EPUB')
        ])

    def test_identifyReadableVersions_none(self, testManager, mocker):
        baseSoup = mocker.MagicMock()

        baseSoup.find.return_value = None

        testManager.museSoup = baseSoup

        assert testManager.identifyReadableVersions() is None

    def test_addReadableLinks_pdf(self, testManager, mocker):
        mockConstruct = mocker.patch.object(MUSEManager, 'constructWebpubManifest')

        testManager.pdfDownloadURL = 'testPDFURL'

        testManager.addReadableLinks()

        testManager.record.add_has_part_link.assert_called_once_with(
            'testPDFURL', 'application/pdf', '{"download": true, "reader": false, "catalog": false}'
        )
        mockConstruct.assert_called_once()

    def test_addReadableLinks_epub(self, testManager, mocker):
        mockConstruct = mocker.patch.object(MUSEManager, 'constructWebpubManifest')
        mockS3 = mocker.patch.object(MUSEManager, 'constructS3Link')
        mockS3.side_effect = ['epubDownloadURL', 'epubReadURL']

        testManager.epubURL = 'testEpubURL'

        testManager.addReadableLinks()

        testManager.record.add_has_part_link.assert_has_calls([
            mocker.call('epubDownloadURL', 'application/epub+zip', '{"download": true, "reader": false, "catalog": false}'),
            mocker.call('epubReadURL', 'application/webpub+json', '{"download": false, "reader": true, "catalog": false}')
        ])
        mockS3.assert_has_calls([
            mocker.call('epubs/muse/1.epub'),
            mocker.call('epubs/muse/1/manifest.json')
        ])
        mockConstruct.assert_called_once()

    def test_addReadableLinks_manifest(self, testManager, mocker):
        mockConstruct = mocker.patch.object(MUSEManager, 'constructWebpubManifest')
        mockS3 = mocker.patch.object(MUSEManager, 'create_manifest_in_s3')
        mockS3.return_value = 'webpubReadURL'

        testManager.pdfWebpubManifest = 'testManifestURL'

        testManager.addReadableLinks()

        testManager.record.add_has_part_link.assert_called_once_with(
            'webpubReadURL', 'application/webpub+json', '{"reader": true, "download": false, "catalog": false}'
        )
        mockS3.assert_called_once_with('manifests/muse/1.json')
        mockConstruct.assert_called_once()

    def test_constructWebpubManifest(self, testManager, testMUSEPage, mocker):
        testManager.museSoup = BeautifulSoup(testMUSEPage, features='lxml')

        mockManifest = mocker.MagicMock(readingOrder=[1, 2, 3])
        mockManifestConstructor = mocker.patch('managers.muse.WebpubManifest')
        mockManifestConstructor.return_value = mockManifest

        testManager.constructWebpubManifest()

        assert testManager.pdfWebpubManifest == mockManifest

        mockManifestConstructor.assert_called_once_with('testLink', 'testType')
        mockManifest.addMetadata.assert_called_once_with('testRecord')

        mockManifest.addSection.assert_has_calls([
            mocker.call('Part One. Reading Reading Historically', ''),
            mocker.call('PART TWO. Contextual Receptions, Reading Experiences, and Patterns of Response: Four Case Studies', '')
        ])

        mockManifest.addChapter.assert_has_calls([
            mocker.call('https://muse.jhu.edu/chapter/440/pdf', 'Cover'),
            mocker.call('https://muse.jhu.edu/chapter/2183675/pdf?start=2', 'Title Page'),
            mocker.call('https://muse.jhu.edu/chapter/2183674/pdf?start=2', 'Copyright'),
            mocker.call('https://muse.jhu.edu/chapter/2183673/pdf?start=2', 'Dedication'),
            mocker.call('https://muse.jhu.edu/chapter/441/pdf?start=2', 'Contents'),
            mocker.call('https://muse.jhu.edu/chapter/442/pdf?start=2', 'Preface'),
            mocker.call('https://muse.jhu.edu/chapter/444/pdf?start=2', 'Chapter 1. Historical Hermeneutics, Reception Theory, and the Social Conditions of Reading in Antebellum America'),
            mocker.call('https://muse.jhu.edu/chapter/445/pdf?start=2', 'Chapter 2. Interpretive Strategies and Informed Reading in the Antebellum Public Sphere'),
            mocker.call('https://muse.jhu.edu/chapter/6239/pdf?start=2', 'Chapter 3. “These Days of Double Dealing”: Informed Response, Reader Appropriation, and the Tales of Poe'),
            mocker.call('https://muse.jhu.edu/chapter/6240/pdf?start=2', 'Chapter 4. Multiple Audiences and Melville’s Fiction: Receptions, Recoveries, and Regressions'),
            mocker.call('https://muse.jhu.edu/chapter/6241/pdf?start=2', 'Chapter 5. Response as (Re)construction: The Reception of Catharine Sedgwick’s Novels'),
            mocker.call('https://muse.jhu.edu/chapter/6242/pdf?start=2', 'Chapter 6. Mercurial Readings: The Making and Unmaking of Caroline Chesebro’'),
            mocker.call('https://muse.jhu.edu/chapter/6243/pdf?start=2', 'Conclusion. American Literary History and the Historical Study of Interpretive Practices'),
            mocker.call('https://muse.jhu.edu/chapter/6244/pdf?start=2', 'Notes'),
            mocker.call('https://muse.jhu.edu/chapter/6245/pdf?start=2', 'Index')
        ])

        mockManifest.closeSection.assert_has_calls([mocker.call(), mocker.call()])

    def test_loadMusePage_success(self, testManager, mocker):
        mockGet = mocker.patch.object(requests, 'get')
        mockResp = mocker.MagicMock()
        mockResp.status_code = 200
        mockResp.text = 'testHTML'
        mockGet.return_value = mockResp

        assert testManager.loadMusePage() == 'testHTML'
        mockGet.assert_called_once_with('testLink', timeout=15, headers={'User-agent': 'Mozilla/5.0'})

    def test_loadMusePage_error(self, testManager, mocker):
        mockGet = mocker.patch.object(requests, 'get')
        mockResp = mocker.MagicMock()
        mockResp.raise_for_status.side_effect = Exception
        mockGet.return_value = mockResp

        with pytest.raises(Exception):
            testManager.loadMusePage()

    def test_constructS3Link(self, testManager):
        assert testManager.constructS3Link('testLocation')\
            == 'https://test_aws_bucket.s3.amazonaws.com/testLocation'

    def test_create_manifest_in_s3(self, testManager, mocker):
        mockConstruct = mocker.patch.object(MUSEManager, 'constructS3Link')
        mockConstruct.return_value = 'testS3URL'

        testManager.pdfWebpubManifest = mocker.MagicMock()
        testManager.pdfWebpubManifest.links = []

        testURL = testManager.create_manifest_in_s3('testPath')

        assert testURL == 'testS3URL'
        assert testManager.pdfWebpubManifest.links[0]\
            == {'href': testURL, 'type': 'application/webpub+json', 'rel': 'self'}
        mockConstruct.assert_called_once_with('testPath')

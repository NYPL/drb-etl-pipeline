from PIL import Image, UnidentifiedImageError
import pytest

from managers import CoverManager


class TestCoverManager:
    @pytest.fixture
    def testManager(self, mocker):
        class MockCoverManager(CoverManager):
            def __init__(self, edition, dbSession):
                self.edition = edition
                self.dbSession = dbSession

        return MockCoverManager(mocker.MagicMock(), mocker.MagicMock())

    @pytest.fixture
    def mockImageCreator(self, mocker):
        def createImageMocks(width, height, format):
            mockOriginal = mocker.MagicMock(width=width, height=height, format=format)
            mockResized = mocker.MagicMock()

            mockOriginal.resize.return_value = mockResized

            return mockOriginal

        return createImageMocks

    def test_loadFetchers(self, testManager):
        testManager.loadFetchers()

        assert len(testManager.fetchers) == 4
        assert testManager.fetchers[0].__name__ == 'HathiFetcher'
        assert testManager.fetchers[3].__name__ == 'ContentCafeFetcher'

    def test_fetchCover_success(self, testManager, mocker):
        testManager.edition.identifiers = [mocker.MagicMock(identifier=1, authority='test')]

        mockFetcher = mocker.MagicMock()
        mockFetcher.hasCover.return_value = True
        testManager.fetchers = [mocker.MagicMock(return_value=mockFetcher)]

        assert testManager.fetchCover() == True

        testManager.fetchers[0].assert_called_once_with([(1, 'test')], testManager.dbSession)
        mockFetcher.hasCover.assert_called_once()

    def test_fetchCover_none(self, testManager, mocker):
        testManager.edition.identifiers = [mocker.MagicMock(identifier=1, authority='test')]

        mockFetcher = mocker.MagicMock()
        mockFetcher.hasCover.return_value = False
        testManager.fetchers = [mocker.MagicMock(return_value=mockFetcher)]

        assert testManager.fetchCover() == False

    def test_fetchCoverFile(self, testManager, mocker):
        testManager.fetcher = mocker.MagicMock()
        testManager.fetcher.downloadCoverFile.return_value = 'testContent'

        testManager.fetchCoverFile()

        assert testManager.coverContent == 'testContent'
        testManager.fetcher.downloadCoverFile.assert_called_once()

    def test_resizeCover_tall(self, testManager, mockImageCreator, mocker):
        mockImage = mocker.patch.object(Image, 'open')

        mockOriginal = mockImageCreator(500, 900, 'test')
        mockImage.return_value = mockOriginal

        testManager.coverContent = b'testImageBytes'
        testManager.resizeCoverFile()

        assert testManager.coverContent == b''
        assert testManager.coverFormat == 'test'
        mockOriginal.resize.assert_called_once_with((222, 400))

    def test_resizeCover_short(self, testManager, mockImageCreator, mocker):
        mockImage = mocker.patch.object(Image, 'open')

        mockOriginal = mockImageCreator(900, 500, 'test')
        mockImage.return_value = mockOriginal

        testManager.coverContent = b'testImageBytes'
        testManager.resizeCoverFile()

        assert testManager.coverContent == b''
        assert testManager.coverFormat == 'test'
        mockOriginal.resize.assert_called_once_with((300, 167))

    def test_resizeCover_square(self, testManager, mockImageCreator, mocker):
        mockImage = mocker.patch.object(Image, 'open')

        mockOriginal = mockImageCreator(500, 500, 'test')
        mockImage.return_value = mockOriginal

        testManager.coverContent = b'testImageBytes'
        testManager.resizeCoverFile()

        assert testManager.coverContent == b''
        assert testManager.coverFormat == 'test'
        mockOriginal.resize.assert_called_once_with((300, 300))

    def test_resizeCover_error(self, testManager, mocker):
        mockImage = mocker.patch.object(Image, 'open')
        mockImage.side_effect = UnidentifiedImageError

        testManager.coverContent = b'testImageBytes'

        assert testManager.resizeCoverFile() == None
        assert testManager.coverContent == None
        

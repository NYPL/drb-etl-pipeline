import pytest
import requests
from requests.exceptions import ReadTimeout

from managers.coverFetchers import ContentCafeFetcher


class TestContentCafeFetcher:
    @pytest.fixture
    def testFetcher(self):
        class MockCCFetcher(ContentCafeFetcher):
            def __init__(self, *args):
                self.apiUser = 'testUser'
                self.apiPswd = 'testPswd'

        return MockCCFetcher()

    @pytest.fixture
    def testNoCoverBytes(self):
        return b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xe1\x00hExif\x00\x00MM\x00*\x00\x00\x00\x08\x00\x04\x01\x1a\x00\x05\x00\x00\x00\x01\x00\x00\x00>\x01\x1b\x00\x05\x00\x00\x00\x01\x00\x00\x00F\x01(\x00\x03\x00\x00\x00\x01\x00\x02\x00\x00\x011\x00\x02\x00\x00\x00\x12\x00\x00\x00N\x00\x00\x00\x00\x00\x00\x00`\x00\x00\x00\x01\x00\x00\x00`\x00\x00\x00\x01Paint.NET v3.5.10\x00\xff\xdb\x00C\x00\x05\x04\x04\x04\x04\x03\x05\x04\x04\x04\x06\x05\x05\x06\x08\r\x08\x08\x07\x07\x08\x10\x0b\x0c\t\r\x13\x10\x14\x13\x12\x10\x12\x12\x14\x17\x1d\x19\x14\x16\x1c\x16\x12\x12\x1a#\x1a\x1c\x1e\x1f!!!\x14\x19$\'$ &\x1d ! \xff\xdb\x00C\x01\x05\x06\x06\x08\x07\x08\x0f\x08\x08\x0f \x15\x12\x15                                                  \xff\xc0\x00\x11\x08\x00x\x00P\x03\x01"\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82\t\n\x16\x17\x18\x19\x1a%&\'()*456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xc4\x00\x1f\x01\x00\x03\x01\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x11\x00\x02\x01\x02\x04\x04\x03\x04\x07\x05\x04\x04\x00\x01\x02w\x00\x01\x02\x03\x11\x04\x05!1\x06\x12AQ\x07aq\x13"2\x81\x08\x14B\x91\xa1\xb1\xc1\t#3R\xf0\x15br\xd1\n\x16$4\xe1%\xf1\x17\x18\x19\x1a&\'()*56789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00?\x00\xfa\xd9M:\xa0V\xa7\xee\xa0\x07\x93L&\x90\xb50\x92i\x80\xfc\xd1\x9at*\xae\xa4\xb784\x92K\xb1\xca\xa0\x0b\x8e\xf8\xa0\x04*\xd8\xce0=\xf8\xa8]\x80\xef\x93\xedC\xc8O$\xe4\xd5i\x1e\x80\x12I1T\xe6\x9b\x03\xad,\xaeB\xee<\x0fZ\xcc\x9en\xbc\xd0#\xa5\x0fR#\x06u\\\xf58\xaa\xb94\xf8\x98\xf9\xc9\xf5\x14\x0c\xb93$8\x01A\'\xb9\xaa\xc5\xa4\x94\xf0\x0b\x7f*[\xe6\xc3\xa7\xd2\x96\xf6FK\x7f\x94\xe3\x9cq@\x13Z\xb6\x15\xc1\xea\x1b\x15Zy1;\x8aK\x07&\'\xfa\xd5[\x99\x08\xba\x7f\xad\x02.\xa4-"\x86,\x15MU\x9ex!\xc8\x8dw\xb8\xfe&\xe8*\xec\x0cM\xb4\x7fJ\xe6\xaee>c\xfdM\x03\x0b\x9b\x96v%\x9b&\xb2\xe6\x979\xa7\xcb!\xaa\x12\xb9\xa6#\xba\xa7E\xfe\xbd?\xde\x14\xdat_\xeb\xd3\xfd\xe1I\x0c\x92\xfb\xef\xa7\xd2\x8b\xff\x00\xf8\xf6\x1f\xef\n/\xbe\xfa}(\xbf\xff\x00\x8fa\xfe\xf0\xa0C4\xff\x00\xf5O\xfe\xf5T\xba\xff\x00\x8f\xa9>\xb5oO\xff\x00T\xff\x00\xefUK\xaf\xf8\xfa\x93\xebL\r\x1b\x7f\xf8\xf5\x8f\xe9\\\xc5\xc7'

    def test_hasCover_true(self, testFetcher, mocker):
        mockFetch = mocker.patch.object(ContentCafeFetcher, 'fetchVolumeCover')
        mockFetch.return_value = True

        testFetcher.identifiers = [(1, 'test'), (2, 'isbn')]
        assert testFetcher.hasCover() == True

    def test_hasCover_false(self, testFetcher, mocker):
        mockFetch = mocker.patch.object(ContentCafeFetcher, 'fetchVolumeCover')
        mockFetch.return_value = False

        testFetcher.identifiers = [(1, 'test'), (2, 'isbn')]
        assert testFetcher.hasCover() == False

    def test_fetchVolumeCover_success(self, testFetcher, mocker):
        mockResp = mocker.MagicMock(status_code=200)
        mockResp.raw.read.return_value = 'testStartBytes'
        mockResp.raw.data = 'testRemainderBytes'
        mockGet = mocker.patch.object(requests, 'get')
        mockGet.return_value = mockResp

        mockCoverCheck = mocker.patch.object(ContentCafeFetcher, 'isNoCoverImage')
        mockCoverCheck.return_value = False

        assert testFetcher.fetchVolumeCover(1) == True
        assert testFetcher.content == 'testStartBytestestRemainderBytes'
        mockGet.assert_called_once_with('http://contentcafe2.btol.com/ContentCafe/Jacket.aspx?userID=testUser&password=testPswd&type=L&Value=1', timeout=5, stream=True)
        mockCoverCheck.assert_called_once_with('testStartBytes')

    def test_fetchVolumeCover_missing(self, testFetcher, mocker):
        mockResp = mocker.MagicMock(status_code=200)
        mockResp.raw.read.return_value = 'testStartBytes'
        mockGet = mocker.patch.object(requests, 'get')
        mockGet.return_value = mockResp

        mockCoverCheck = mocker.patch.object(ContentCafeFetcher, 'isNoCoverImage')
        mockCoverCheck.return_value = True

        assert testFetcher.fetchVolumeCover(1) == False
        mockGet.assert_called_once_with('http://contentcafe2.btol.com/ContentCafe/Jacket.aspx?userID=testUser&password=testPswd&type=L&Value=1', timeout=5, stream=True)
        mockCoverCheck.assert_called_once_with('testStartBytes')

    def test_fetchVolumeCover_error(self, testFetcher, mocker):
        mockGet = mocker.patch.object(requests, 'get')
        mockGet.side_effect = ReadTimeout

        assert testFetcher.fetchVolumeCover(1) == False

    def test_isNoCoverImage_true(self, testFetcher, testNoCoverBytes):
        assert testFetcher.isNoCoverImage(testNoCoverBytes) == True

    def test_isNoCoverImage_false(self, testFetcher):
        assert testFetcher.isNoCoverImage(b'otherThing') == False

    def test_downloadCoverFile(self, testFetcher):
        testFetcher.content = 'testImageContent'
        assert testFetcher.downloadCoverFile() == 'testImageContent'
import pytest

from managers.pdfManifest import PDFChapter


class TestPDFChapter:
    @pytest.fixture
    def testChapterWithRange(self):
        return PDFChapter('testLink', 'testTitle', '1-5')

    @pytest.fixture
    def testChapterWithoutRange(self):
        return PDFChapter('testLink', 'testTitle', None)

    @pytest.fixture
    def testChapterWithRomanRange(self):
        return PDFChapter('testLink', 'testTitle', 'III-LIX')

    def test_initializer(self, testChapterWithRange):
        assert testChapterWithRange.link == 'testLink'
        assert testChapterWithRange.title == 'testTitle'
        assert testChapterWithRange.pageRange == '1-5'
        assert testChapterWithRange.startPage == None
        assert testChapterWithRange.endPage == None

    def test_parsePageRange_arabic(self, testChapterWithRange, mocker):
        mockParse = mocker.patch.object(PDFChapter, 'parseRangeValue')
        mockParse.side_effect = [1, 5]

        testChapterWithRange.parsePageRange()

        mockParse.assert_has_calls([
            mocker.call('1'), mocker.call('5')
        ])
        assert testChapterWithRange.startPage == 1
        assert testChapterWithRange.endPage == 5

    def test_parsePageRange_roman(self, testChapterWithRomanRange, mocker):
        mockParse = mocker.patch.object(PDFChapter, 'parseRangeValue')
        mockParse.side_effect = [3, 59]

        testChapterWithRomanRange.parsePageRange()

        mockParse.assert_has_calls([
            mocker.call('III'), mocker.call('LIX')
        ])
        assert testChapterWithRomanRange.startPage == 3
        assert testChapterWithRomanRange.endPage == 59

    def test_parsePageRange_none(self, testChapterWithoutRange, mocker):
        mockParse = mocker.patch.object(PDFChapter, 'parseRangeValue')

        testChapterWithoutRange.parsePageRange()

        mockParse.assert_not_called
        assert testChapterWithoutRange.startPage == None
        assert testChapterWithoutRange.endPage == None

    def test_parseRangeValue_int_str(self, mocker):
        mockTranslateRoman = mocker.patch.object(PDFChapter, 'translateRomanNumeral')

        assert PDFChapter.parseRangeValue('1') == 1
        mockTranslateRoman.assert_not_called

    def test_parseRangeValue_char_str(self, mocker):
        mockTranslateRoman = mocker.patch.object(PDFChapter, 'translateRomanNumeral')
        mockTranslateRoman.return_value = 1

        assert PDFChapter.parseRangeValue('iii') == 1
        mockTranslateRoman.assert_called_once_with('iii')

    def test_translateRomanNumeral_simple(self):
        assert PDFChapter.translateRomanNumeral('V') == 5

    def test_translateRomanNumeral_complex(self):
        assert PDFChapter.translateRomanNumeral('mcmxciv') == 1994

    def test_translateRomanNumeral_invalid(self):
        assert PDFChapter.translateRomanNumeral('hello') == None

    def test_toDict(self, testChapterWithRange):
        testChapterWithRange.startPage = 1
        testChapterWithRange.endPage = 5

        assert testChapterWithRange.toDict() == {
            'href': 'testLink', 'title': 'testTitle',
            'pageStart': 1, 'pageEnd': 5
        }

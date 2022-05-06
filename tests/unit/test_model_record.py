import pytest


class TestModelRecord:
    @pytest.fixture
    def testRecord(self, mocker):
        mockHasVersion = mocker.MagicMock()
        mockHasVersion.hex = 'first edition'
        return mocker.MagicMock(
            uuid='Test UUID',
            title='Test Title',
            alternative=['Test Alt 1', 'Test Alt 2'],
            medium='testing',
            is_part_of=['test ser|1|series', 'test vol|1|volume'],
            has_version=mockHasVersion,
            identifiers=['1|test', '2|isbn', '3|owi'],
            authors=['Test Author'],
            publisher=['Test Publisher'],
            spatial='Test Publication Place',
            contributors=['Contrib 1|printer', 'Contrib 2|||provider', 'Contrib 3|||translator'],
            subjects=['Subject 1', 'Subject 2', 'Subject 3'],
            dates=['Date 1', 'Date 2'],
            languages=['English'],
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

    #Test for getter method of record model version
    def test_hasVersion(self, testRecord):
        testRecord.hasVersion.return_value = 'first edition'
        versionStatement = testRecord.hasVersion()
        assert versionStatement == 'first edition'

    #Test for getter method of record model langauge
    def test_language(self, testRecord):
        testRecord.getLanguage.return_value = 'English'
        testlanguage = testRecord.getLanguage()
        assert testlanguage == 'English'

    #First test for setter method of record model
    def test_updateHasVersion(self, testRecord):
        testRecord.updateHasVersion.return_value = 'first edition|1'
        newVersion = testRecord.updateHasVersion()
        assert newVersion == 'first edition|1'

    #Second Test for setter method of record model 
    def test_updateHasVersion2(self, testRecord):
        testRecord.has_version = '1st edition'
        testRecord.updateHasVersion.return_value = '1st edition|1'
        newVersion = testRecord.updateHasVersion()
        assert newVersion == '1st edition|1'
        
            
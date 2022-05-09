import pytest
from model import Record

class TestModelRecord:
    @pytest.fixture
    def testRecord(self):
        return Record(
            uuid='Test UUID',
            title='Test Title',
            languages=['English|en|eng'],
            has_version='first edition'
        )

    def test_no_language(self, testRecord):
        testRecord.languages = None
        testRecord.has_version = 'first edition'
        assert testRecord.has_version == 'first edition|1'


    #Test for getter method of record model langauge
    def test_language(self, testRecord):
        testlanguage = testRecord.getLanguage
        assert testlanguage == 'English'

    # Failed Test for setter method of record model 
    def test_has_version_failure(self, testRecord):
        testRecord.has_version = 'other edition'
        assert testRecord.has_version == 'other edition|None'

    # Test for setter method of record model with edition in English
    def test_has_version_english(self, testRecord):
        testRecord.has_version = 'first edition'
        assert testRecord.has_version == 'first edition|1'

    # Test for setter method of record model with edition in numeric form
    def test_has_version_numeric(self, testRecord):
        testRecord.has_version = '2nd edition'
        assert testRecord.has_version == '2nd edition|2'

    # Test for setter method of record model with edition in other languages
    def test_has_version_other_language(self, testRecord):
        testRecord.has_version = 'deuxieme edition'
        testRecord.languages = ['French|fr|fre']
        assert testRecord.has_version == 'deuxieme edition|2'
        
            
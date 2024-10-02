import pytest

from mappings.muse import MUSEMapping
from model import Record

test_source = { 
    '008': type('data-object', (object,), { 'data' : 'testingdate2000pla' })
}

def test_create_mapping():
    muse_mapping = MUSEMapping(test_source)
    
    assert set([
        'identifiers', 'authors', 'title', 'alternative', 'has_version',
        'publisher', 'spatial', 'dates', 'languages', 'extent',
        'table_of_contents', 'abstract', 'subjects', 'contributors',
        'is_part_of', 'has_part'
    ]).issubset(set(muse_mapping.mapping.keys()))
    assert muse_mapping.mapping['is_part_of'] == ('490', '{a}|{v}|volume')

def test_apply_formatting():
    muse_mapping = MUSEMapping(test_source)
    record = Record()
    record.identifiers = ['1|muse', '2|test', '3|other']
    record.title = ['Main Title', 'Secondary Title']
    record.subjects = ['subj1', 'subj2', 'subj3']
    record.has_part = ['1|testURL|muse|testType|testFlags']
    record.languages = ['||lng1', '||lng2']
    record.publisher = []
    record.dates = []
    muse_mapping.record = record

    muse_mapping.applyFormatting()

    assert muse_mapping.record.source == 'muse'
    assert muse_mapping.record.source_id == '1'
    assert muse_mapping.record.title == 'Main Title'
    assert muse_mapping.record.subjects == ['subj1', 'subj2', 'subj3']
    assert muse_mapping.record.languages == ['||lng1', '||lng2']
    assert muse_mapping.record.dates[0] == '2000|publication_date'

def test_clean_up_subject_head():
    muse_mapping = MUSEMapping(test_source)
    
    cleanSubject = muse_mapping.clean_up_subject_head('first -- second. -- -- |||')

    assert cleanSubject == 'first -- second|||'

def test_extract_language():
    muse_mapping = MUSEMapping(test_source)

    extracted_language = muse_mapping.extract_language('||100607s2011    mdu     o      00 0 eng d  z  ')

    assert extracted_language == '||eng'

def test_cleanup_identifier():
    muse_mapping = MUSEMapping(test_source)

    cleaned_identifier = muse_mapping.cleanup_identifier('(OCoLC)12235')

    assert cleaned_identifier == '12235'

def test_add_has_part_link():
    muse_mapping = MUSEMapping(test_source)
    muse_mapping.record = Record()
    muse_mapping.record.has_part = ['1|test_url|muse|epub|flags']

    muse_mapping.add_has_part_link('newURL', 'pdf+json', 'pdfFlags')

    assert muse_mapping.record.has_part[1] == '1|newURL|muse|pdf+json|pdfFlags'    

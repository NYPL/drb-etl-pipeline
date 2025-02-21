import json

TEST_SOURCE = 'test_source'

# Default return value
# {
#     'title': 'test record',
#     'uuid': uuid4(),
#     'frbr_status': 'complete',
#     'cluster_status': False,
#     'source': 'test_source',
#     'authors': ['Test Author||true'],
#     'languages': ['test_language'],
#     'dates': ['1907|publication_date'],
#     'publisher': ['test publisher||'],
#     'identifiers': [],
#     'source_id': 'test_source|test',
#     'contributors': ['test contributor|||contributor'],
#     'extent': '11, 164 p. ;', 
#     'is_part_of': ['Tauchnitz edition|Vol. 4560|volume'],  
#     'abstract': ['test abstract 1', 'test abstract 2'],
#     'subjects': ['test_subject||'], 
#     'rights': 'test source|public_domain|expiration of copyright term for non-US work with corporate author|Public Domain|2021-10-02 05:25:13',
#     'has_part': [f'1|example.com/1.pdf|{test_source}|text/html|{json.dumps(flags)}'], 
#     'flags': { 'catalog': False, 'download': False, 'reader': False, 'embed': True }
# }

def generate_test_data(
    title='test record',
    uuid=None,
    frbr_status='complete',
    cluster_status=False,
    source=TEST_SOURCE,
    authors=None,
    languages=None,
    dates=None,
    publisher=None,
    identifiers=None,
    source_id='test_source|test',
    contributors=None,
    extent=None,
    is_part_of=None,
    abstract=None,
    subjects=None,
    rights=None,
    has_part=None,
    flags = { 'catalog': False, 'download': False, 'reader': False, 'embed': True }
):
    return {
        'title': title,
        'uuid': uuid,
        'frbr_status': frbr_status,
        'cluster_status': cluster_status,
        'source': source,
        'authors': authors or ['Test Author||true'],
        'languages': languages or ['test_language'],
        'dates': dates or ['1907|publication_date'],
        'publisher': publisher or ['test publisher||'],
        'identifiers': identifiers or [],
        'source_id': source_id,
        'contributors': contributors or ['test contributor|||contributor'],
        'extent': extent or '11, 164 p. ;',
        'is_part_of': is_part_of or ['Tauchnitz edition|Vol. 4560|volume'],
        'abstract': abstract or ['test abstract 1', 'test abstract 2'],
        'subjects': subjects or ['test_subject||'],
        'rights': rights or 'test source|public_domain|expiration of copyright term for non-US work with corporate author|Public Domain|2021-10-02 05:25:13',
        'has_part': has_part or [f'1|example.com/1.pdf|{TEST_SOURCE}|text/html|{json.dumps(flags)}'],
    }

import os
import pytest
from datetime import datetime, timezone
import json
from sqlalchemy import text, delete
from uuid import uuid4

from processes import ClusterProcess
from model import Collection, Edition, Item, Link, Record, Work
from model.postgres.item import ITEM_LINKS
from logger import create_log
from managers import DBManager, RabbitMQManager, S3Manager
from load_env import load_env_file
from tests.fixtures.generate_test_data import generate_test_data


logger = create_log(__name__)

TEST_SOURCE = 'test_source'
OCLC_SOURCE = 'oclcClassify'


def pytest_addoption(parser):
    parser.addoption('--env', action='store', default='local', help='Environment to use for tests')


@pytest.fixture(scope='session', autouse=True)
def setup_env(pytestconfig, request):
    environment = os.environ.get('ENVIRONMENT') or pytestconfig.getoption('--env') or 'local'

    running_unit_tests = any('unit' in item.keywords for item in request.session.items)

    if not running_unit_tests and environment in ['local', 'local-qa', 'qa']:
        load_env_file(environment, file_string=f'config/{environment}.yaml')


@pytest.fixture(scope='session')
def db_manager():
    db_manager = DBManager()
    
    try:
        db_manager.createSession()
        db_manager.session.execute(text('SELECT 1'))

        yield db_manager
        
        db_manager.close_connection()
    except:
        yield None


@pytest.fixture(scope='session')
def rabbitmq_manager():
    rabbitmq_manager = RabbitMQManager()

    try: 
        rabbitmq_manager.createRabbitConnection()

        yield rabbitmq_manager

        rabbitmq_manager.closeRabbitConnection()
    except:
        yield None


@pytest.fixture(scope='session')
def s3_manager():
    s3_manager = S3Manager()

    try:
        s3_manager.createS3Client()

        yield s3_manager
    except:
        yield None


@pytest.fixture(scope='session')
def test_title():
    return 'Integration Test Book'


@pytest.fixture(scope='session')
def test_subject():
    return 'Integration Test Subject'


@pytest.fixture(scope='session')
def test_language():
    return 'Integration Test Language'


@pytest.fixture(scope='session')
def seed_test_data(db_manager, test_title, test_subject, test_language):
    # TODO: find path forward to connect to db in GH actions
    if db_manager is None:
        return {
            'edition_id': 1982731,
            'work_id': '701c5f00-cd7a-4a7d-9ed1-ce41c574ad1d',
            'link_id': 1982731,
            'unfrbrized_record_uuid': '7bd4a8c0-9b3a-487b-9c7c-1dd6890a5c7a'
        }

    def create_or_update_record(record_data):
        existing_record = db_manager.session.query(Record).filter(
            Record.source_id == record_data['source_id']
        ).first()

        if existing_record:
            for key, value in record_data.items():
                if key != 'uuid' and hasattr(existing_record, key):
                    setattr(existing_record, key, value)
            
            existing_record.date_modified = datetime.now(timezone.utc).replace(tzinfo=None)
            record_data['uuid'] = existing_record.uuid
            
            return existing_record
        
        return Record(**record_data)    

    flags = { 'catalog': False, 'download': False, 'reader': False, 'embed': True }
    test_frbrized_record_data = {
        'title': test_title,
        'uuid': uuid4(),
        'frbr_status': 'complete',
        'cluster_status': False,
        "source": TEST_SOURCE,
        'authors': ['Ayan||true'],
        'languages': [test_language],
        'dates': ['1907-|publication_date'],
        'publisher': ['Project Gutenberg Literary Archive Foundation||'],
        'identifiers': [],
        'source_id': '4064148285|test',
        'contributors': ['Metropolitan Museum of Art (New York, N.Y.)|||contributor','Metropolitan Museum of Art (New York, N.Y.)|||repository','Thomas J. Watson Library|||provider'],
        'extent': ('11, 164 p. ;'),
        'is_part_of': ['Tauchnitz edition|Vol. 4560|volume'],
        'abstract': ['test abstract 1', 'test abstract 2'],
        'subjects': [f'{test_subject}||'],
        'rights': ('hathitrust|public_domain|expiration of copyright term for non-US work with corporate author|Public Domain|2021-10-02 05:25:13'),
        'has_part': [f'1|example.com/1.pdf|{TEST_SOURCE}|text/html|{json.dumps(flags)}']
    }

    test_unfrbrized_record_data = {
        'title': 'Emma',
        'uuid': uuid4(),
        'frbr_status': 'to_do',
        'cluster_status': False,
        "source": OCLC_SOURCE,
        'authors': ['Jane, Austen||true'],
        'identifiers': ['0198837755|isbn'],
        'source_id': '0198837755|isbn',
        'date_modified': datetime.now(timezone.utc).replace(tzinfo=None)
    }

    test_unclustered_record_data = generate_test_data(title='unclustered record', uuid=uuid4(), source_id='unclustered|test')
    test_unclustered_edition_data = generate_test_data(title='multi edition record', uuid=uuid4(), source_id='unclustered_edition|test', dates=['1988|publication_date'], identifiers=['1234567891011|isbn'])
    test_unclustered_edition_data2 = generate_test_data(title='the multi edition record', uuid=uuid4(), source_id='unclustered_edition2|test', dates=['1977|publication_date'], identifiers=['1234567891011|isbn'])
    test_unclustered_item_data = generate_test_data(title='multi item record', uuid=uuid4(), source_id='unclustered_item|test', dates=['1966|publication_date'], identifiers=['2341317561|isbn'])
    test_unclustered_item_data2 = generate_test_data(
        title='multi item record', uuid=uuid4(), 
        source_id='unclustered_item2|test', 
        dates=['1966|publication_date'],
        identifiers=['2341317561|isbn'],
        has_part=[f'1|example.com/2.pdf|{TEST_SOURCE}|text/html|{json.dumps(flags)}'])

    test_limited_access_record_data = {
        'title': 'Bluets',
        'uuid': uuid4(),
        'frbr_status': 'complete',
        'cluster_status': False,
        'authors': ['Nelson, Maggie||true'],
        'dates': ['2009|publication_date'],
        'publisher': ['Wave Books||'],
        'identifiers': ['1933517409|isbn'],
        'rights':'in_copyright|cc-by|Public Domain|expired_copyright|2024-01-01',
        'contributors': ['qaContributor|||contributor'],
        'subjects': ['poetry||'],
        'source': TEST_SOURCE,
        'source_id': 'pbtestSourceID',
        'publisher_project_source': ['University of Michigan Press'],
        'has_part': [f'1|https://example.com/book.epub|{TEST_SOURCE}|application/epub+zip|{json.dumps({"reader": True})}']

    }

    frbrized_record = create_or_update_record(test_frbrized_record_data)
    unfrbrized_record = create_or_update_record(test_unfrbrized_record_data)

    unclustered_record = create_or_update_record(test_unclustered_record_data)
    unclustered_multi_edition = create_or_update_record(test_unclustered_edition_data)
    unclustered_multi_edition2 = create_or_update_record(test_unclustered_edition_data2)
    unclustered_multi_item = create_or_update_record(test_unclustered_item_data)
    unclustered_multi_item2 = create_or_update_record(test_unclustered_item_data2)

    limited_access_record = create_or_update_record(test_limited_access_record_data)

    
    if not frbrized_record.id:
        db_manager.session.add(frbrized_record)
    if not unfrbrized_record.id:
        db_manager.session.add(unfrbrized_record)
    if not unclustered_record.id:
        db_manager.session.add(unclustered_record)
    if not unclustered_multi_edition.id:
        db_manager.session.add(unclustered_multi_edition)
    if not unclustered_multi_edition2.id:
        db_manager.session.add(unclustered_multi_edition2)
    if not unclustered_multi_item.id:
        db_manager.session.add(unclustered_multi_item)
    if not unclustered_multi_item2.id:
        db_manager.session.add(unclustered_multi_item2)
    if not limited_access_record.id:
        db_manager.session.add(limited_access_record)

    db_manager.session.commit()

    cluster_process = ClusterProcess('complete', None, None, str(test_frbrized_record_data['uuid']), None)
    cluster_process.runProcess()

    frbrized_model = (
        db_manager.session.query(Item, Edition, Work)
            .join(Edition, Edition.id == Item.edition_id)
            .join(Work, Work.id == Edition.work_id)
            .filter(Item.record_id == frbrized_record.id)
            .first()
    )

    item, edition, work = frbrized_model if frbrized_model else (None, None, None)

    links = (
        db_manager.session.query(Link)
            .join(ITEM_LINKS)
            .filter(ITEM_LINKS.c.item_id == item.id)
            .all()
    )

    return {
        'edition_id': str(edition.id) if item else None,
        'work_id': str(work.uuid) if work else None,
        'link_id': links[0].id if links and len(links) > 0 else None,
        'unfrbrized_record_uuid': str(unfrbrized_record.uuid),
        'unclustered_record_uuid': str(unclustered_record.uuid),
        'unclustered_multi_edition_uuid': str(unclustered_multi_edition.uuid),
        'unclustered_multi_item_uuid': str(unclustered_multi_item.uuid),
        'unclustered_multi_item2_uuid': str(unclustered_multi_item2.uuid),
        'unfrbrized_title': str(unfrbrized_record.title),
        'limited_access_record_uuid': str(limited_access_record.uuid)
    }


@pytest.fixture(scope='session')
def test_edition_id(seed_test_data):
    return seed_test_data['edition_id']


@pytest.fixture(scope='session')
def test_collection_id(db_manager, test_edition_id):
    if not db_manager:
        yield '3650664c-c8be-4d07-8d64-2d7003b02048'
        return

    edition = db_manager.session.query(Edition).filter(Edition.id == test_edition_id).first()
    test_collection = Collection(
        title='Test Collection',
        uuid=uuid4(),
        creator='Integration Tests', 
        owner='Integration Tests',
        description='A test collection for integration tests.',
        type='static',
        editions=[edition]
    )

    db_manager.session.add(test_collection)
    db_manager.session.commit()

    yield test_collection.uuid

    with db_manager.engine.connect() as connection:
        with connection.begin():
            connection.execute(delete(Collection).where(Collection.uuid == test_collection.uuid))


@pytest.fixture(scope='session')
def test_work_id(seed_test_data):
    return seed_test_data['work_id']

@pytest.fixture(scope='session')
def test_link_id(seed_test_data):
    return seed_test_data['link_id']

@pytest.fixture(scope='session')
def unfrbrized_record_uuid(seed_test_data):
    return seed_test_data['unfrbrized_record_uuid']

@pytest.fixture(scope='session')
def unclustered_record_uuid(seed_test_data):
    return seed_test_data['unclustered_record_uuid']

@pytest.fixture(scope='session')
def unclustered_multi_edition_uuid(seed_test_data):
    return seed_test_data['unclustered_multi_edition_uuid']

@pytest.fixture(scope='session')
def unclustered_multi_item_uuid(seed_test_data):
    return seed_test_data['unclustered_multi_item_uuid']

@pytest.fixture(scope='session')
def unfrbrized_title(seed_test_data):
    return seed_test_data['unfrbrized_title']

@pytest.fixture(scope='session')
def limited_access_record_uuid(seed_test_data):
    return seed_test_data['limited_access_record_uuid']

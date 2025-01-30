import os
import pytest
from datetime import datetime, timezone
import json
from sqlalchemy import text
from uuid import uuid4

from processes import ClusterProcess
from model import Collection, Edition, Item, Link, Record, Work
from model.postgres.item import ITEM_LINKS
from logger import create_log
from managers import DBManager
from load_env import load_env_file


logger = create_log(__name__)

TEST_SOURCE = 'test_source'


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
        db_manager.session.execute(text('SELECT 1')) # Test the db connection

        yield db_manager
        
        db_manager.close_connection()
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
        }

    flags = { 'catalog': False, 'download': False, 'reader': False, 'embed': True }
    test_record_data = {
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

    existing_record = db_manager.session.query(Record).filter(Record.source_id == test_record_data['source_id']).first()

    if existing_record:
        for key, value in test_record_data.items():
            if key != 'uuid' and hasattr(existing_record, key):
                setattr(existing_record, key, value)
        
        existing_record.date_modified = datetime.now(timezone.utc).replace(tzinfo=None)
        test_record_data['uuid'] = existing_record.uuid
        test_record = existing_record
    else:
        test_record = Record(**test_record_data)
        db_manager.session.add(test_record)
    
    db_manager.session.commit()

    cluster_process = ClusterProcess('complete', None, None, str(test_record_data['uuid']), None)
    cluster_process.runProcess()

    frbrized_model = (
        db_manager.session.query(Item, Edition, Work)
            .join(Edition, Edition.id == Item.edition_id)
            .join(Work, Work.id == Edition.work_id)
            .filter(Item.record_id == test_record.id)
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
    }


@pytest.fixture(scope='session')
def test_edition_id(seed_test_data):
    return seed_test_data['edition_id']


@pytest.fixture(scope='session')
def test_collection_id(db_manager, test_edition_id):
    if not db_manager:
        return '3650664c-c8be-4d07-8d64-2d7003b02048'

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

    db_manager.session.delete(test_collection)
    db_manager.session.commit()


@pytest.fixture(scope='session')
def test_work_id(seed_test_data):
    return seed_test_data['work_id']


@pytest.fixture(scope='session')
def test_link_id(seed_test_data):
    return seed_test_data['link_id']

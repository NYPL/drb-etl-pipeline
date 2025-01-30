import os
import pytest
from datetime import datetime, timezone
import json
from sqlalchemy import text
from uuid import uuid4

from processes import ClusterProcess
from model import Record, Item
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


@pytest.fixture(scope='module')
def db_manager():
    db_manager = DBManager()
    
    try:
        db_manager.createSession()
        db_manager.session.execute(text('SELECT 1')) # Test the db connection

        yield db_manager
        
        db_manager.close_connection()
    except:
        yield None


@pytest.fixture(scope='module')
def seed_test_data(db_manager):
    # TODO: find path forward to connect to db in GH actions
    if db_manager is None:
        return {
            'edition_id': 1982731
        }

    flags = { 'catalog': False, 'download': False, 'reader': False, 'embed': True }
    test_data = {
        'title': 'test data 1',
        'uuid': uuid4(),
        'frbr_status': 'complete',
        'cluster_status': False,
        "source": TEST_SOURCE,
        'authors': ['Ayan||true'],
        'languages': ['Serbian'],
        'dates': ['1907-|publication_date'],
        'publisher': ['Project Gutenberg Literary Archive Foundation||'],
        'identifiers': [],
        'source_id': '4064148285|test',
        'contributors': ['Metropolitan Museum of Art (New York, N.Y.)|||contributor','Metropolitan Museum of Art (New York, N.Y.)|||repository','Thomas J. Watson Library|||provider'],
        'extent': ('11, 164 p. ;'),
        'is_part_of': ['Tauchnitz edition|Vol. 4560|volume'],
        'abstract': ['test abstract 1', 'test abstract 2'],
        'subjects': ['test subjects 1||'],
        'rights': ('hathitrust|public_domain|expiration of copyright term for non-US work with corporate author|Public Domain|2021-10-02 05:25:13'),
        'has_part': [f'1|example.com/1.pdf|{TEST_SOURCE}|text/html|{json.dumps(flags)}']
    }

    existing_record = db_manager.session.query(Record).filter_by(source_id=test_data['source_id']).first()

    if existing_record:
        for key, value in test_data.items():
            if key != 'uuid' and hasattr(existing_record, key):
                setattr(existing_record, key, value)
        existing_record.date_modified = datetime.now(timezone.utc).replace(tzinfo=None)
        test_data['uuid'] = existing_record.uuid
        test_record = existing_record
    else:
        test_record = Record(**test_data)
        db_manager.session.add(test_record)
    
    db_manager.session.commit()

    cluster_process = ClusterProcess('complete', None, None, str(test_data['uuid']), None)
    cluster_process.runProcess()

    item = db_manager.session.query(Item).filter_by(record_id=test_record.id).first()
    edition_id = str(item.edition_id) if item else None

    return {
        'edition_id': edition_id,
        'uuid': str(test_data['uuid'])
    }


@pytest.fixture(scope='module')
def seeded_edition_id(request, seed_test_data):
    if 'functional' in request.keywords or 'integration' in request.keywords:
        return seed_test_data['edition_id']
    
    return None


@pytest.fixture(scope='module')
def seeded_uuid(request, seed_test_data):
    if 'functional' in request.keywords or 'integration' in request.keywords:
        return seed_test_data['uuid']
    
    return None

from datetime import datetime, timezone
import json
from uuid import uuid4
from process import ClusterProcess
from model import Record
from logger import create_log
from managers import DBManager

logger = create_log(__name__)

TEST_SOURCE = 'test_source'

class SeedTestDataProcess():
    def __init__(self, *args):
        self.db_manager = DBManager()

        flags = { 'catalog': False, 'download': False, 'reader': False, 'embed': True }
        self.test_data = {
            'title': 'test data 1',
            'uuid' : uuid4(),
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

    def runProcess(self):
        try:
            self.db_manager.createSession()

            self.save_test_record()

            process_args = ['complete'] + ([None] * 4)
            cluster_process = ClusterProcess(*process_args)
            cluster_process.runProcess()
            
        except Exception as e:
            logger.exception(f'Failed to seed test data')
            raise e
        finally:
            self.db_manager.close_connection()

    def save_test_record(self):
        existing_record = self.db_manager.session.query(Record).filter_by(source_id=self.test_data['source_id']).first()

        if existing_record:
            for key, value in self.test_data.items():
                if key != 'uuid' and hasattr(existing_record, key):
                    setattr(existing_record, key, value)
        
            existing_record.date_modified = datetime.now(timezone.utc).replace(tzinfo=None)
        else:
            test_record = Record(**self.test_data)
            self.db_manager.session.add(test_record)
        
        self.db_manager.session.commit()

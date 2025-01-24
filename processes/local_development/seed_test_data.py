from datetime import datetime
from uuid import uuid4
from mappings.base_mapping import BaseMapping
from datetime import datetime, timezone
from model import Record
from constants.get_constants import get_constants
from logger import create_log
from managers import DBManager
from processes import CatalogProcess, ClassifyProcess, ClusterProcess, HathiTrustProcess

logger = create_log(__name__)

class SeedTestDataProcess():
    def __init__(self, *args):

        self.db_manager = DBManager()
        self.test_data = {
            'title': 'test data 1',
            'uuid' : uuid4(),
            'date_created' : datetime.now(timezone.utc).replace(tzinfo=None),
            'date_modified' :datetime.now(timezone.utc).replace(tzinfo=None),
            'frbr_status': 'to_do',
            'cluster_status': False,
            "source": 'test data source',
            'authors': ['Ayan||true'],
            'languages': ['Serbian'],
            'dates': ['1907-|publication_date'],
            'publisher': ['Project Gutenberg Literary Archive Foundation||'],
            'identifiers': ['4064148285|owi','161468|oclc','161468|oclc','972173562|oclc','1467194159|oclc'],
            'source_id': '4064148285|test',
            'contributors': ['Metropolitan Museum of Art (New York, N.Y.)|||contributor','Metropolitan Museum of Art (New York, N.Y.)|||repository','Thomas J. Watson Library|||provider'],
            'extent': ('11, 164 p. ;'),
            'is_part_of': ['Tauchnitz edition|Vol. 4560|volume'],
            'abstract': ['test abstract 1', 'test abstract 2'],
            'subjects': ['test subjects 1||'],
            'rights': ('hathitrust|public_domain|expiration of copyright term for non-US work with corporate author|Public Domain|2021-10-02 05:25:13'),
            'has_part': ['1|example.com/1.pdf|met|text/html|{"catalog": false, "download": false, "reader": false, "embed": true}']
        }

    def runProcess(self):
        try:
            
            self.db_manager.createSession()

            self.save_test_record()

            process_args = ['complete'] + ([None] * 4)

            classify_process = ClassifyProcess(*process_args)
            classify_process.runProcess()

            catalog_process = CatalogProcess(*process_args)
            catalog_process.runProcess(max_attempts=1)
            
            cluster_process = ClusterProcess(*process_args)
            cluster_process.runProcess()

        except Exception as e:
            logger.exception(f'Failed to seed test data')
            raise e

    def save_test_record(self):
        test_record = Record(**self.test_data)
        self.db_manager.session.add(test_record)
        self.db_manager.session.commit()

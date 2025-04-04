from datetime import datetime, timedelta

from logger import create_log
from managers import DBManager, RedisManager
from processes import CatalogProcess, ClassifyProcess, ClusterProcess
from services import HathiTrustService
from ..record_buffer import RecordBuffer


logger = create_log(__name__)


class SeedLocalDataProcess():
    def __init__(self, *args):
        self.redis_manager = RedisManager()

        self.db_manager = DBManager()
        self.db_manager.create_session()

        self.record_buffer = RecordBuffer(db_manager=self.db_manager)

        self.hathi_trust_service = HathiTrustService()

    def runProcess(self):
        try:
            records = self.hathi_trust_service.get_records(start_timestamp=datetime.now() - timedelta(days=7), limit=50)

            for record in records:
                self.record_buffer.add(record)

            self.record_buffer.flush()

            process_args = ['complete'] + ([None] * 4)

            self.redis_manager.create_client()
            self.redis_manager.clear_cache()

            classify_process = ClassifyProcess(*process_args)
            classify_process.runProcess()

            catalog_process = CatalogProcess(*process_args)
            catalog_process.runProcess(max_attempts=1)
            
            cluster_process = ClusterProcess(*process_args)
            cluster_process.runProcess()
        except Exception as e:
            logger.exception(f'Failed to seed local data')
            raise e

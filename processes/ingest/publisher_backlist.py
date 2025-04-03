from services import PublisherBacklistService

from logger import create_log
from managers import DBManager
from ..record_buffer import RecordBuffer
from .. import utils

logger = create_log(__name__)


class PublisherBacklistProcess:
    def __init__(self, *args):
        self.params = utils.parse_process_args(*args)

        self.db_manager = DBManager()
        self.db_manager.create_session()

        self.record_buffer = RecordBuffer(db_manager=self.db_manager)

        self.publisher_backlist_service = PublisherBacklistService()

    def runProcess(self):
        try:
            self.publisher_backlist_service.delete_records()

            records = self.publisher_backlist_service.get_records(
                start_timestamp=utils.get_start_datetime(
                    process_type=self.params.process_type,
                    ingest_period=self.params.ingest_period,
                ),
                offset=self.params.offset,
                limit=self.params.limit,
            )

            for record_mapping in records:
                self.record_buffer.add(record_mapping.record)

            self.record_buffer.flush()

            logger.info(
                f"Ingested {self.record_buffer.ingest_count} Publisher Backlist records"
            )
        except Exception as e:
            logger.exception("Failed to run Publisher Backlist process")
            raise e
        finally:
            self.db_manager.close_connection()

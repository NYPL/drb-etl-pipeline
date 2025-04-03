from logger import create_log
from managers import DBManager
from ..record_buffer import RecordBuffer
from services import NYPLBibService
from .. import utils

logger = create_log(__name__)


class NYPLProcess():
    def __init__(self, *args):
        self.params = utils.parse_process_args(*args)

        self.db_manager = DBManager()
        self.db_manager.createSession()

        self.record_buffer = RecordBuffer(db_manager=self.db_manager)

        self.nypl_bib_service = NYPLBibService()

    def runProcess(self):
        try:
            records = self.nypl_bib_service.get_records(
                start_timestamp=utils.get_start_datetime(process_type=self.params.process_type, ingest_period=self.params.ingest_period),
                offset=self.params.offset,
                limit=self.params.limit
            )
            
            for record_mapping in records:
                self.record_buffer.add(record_mapping.record)
            
            self.record_buffer.flush()

            logger.info(f'Ingested {self.record_buffer.ingest_count} NYPL records')
        except Exception as e:
            logger.exception(f'Failed to ingest NYPL records')
            raise e
        finally:
            self.db_manager.close_connection()

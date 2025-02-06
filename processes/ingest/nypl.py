from datetime import datetime, timezone, timedelta

from logger import create_log
from managers import DBManager
from .record_buffer import RecordBuffer
from services import NYPLBibService

logger = create_log(__name__)


class NYPLProcess():
    def __init__(self, *args):
        self.process_type = args[0]
        self.ingest_period = args[2]
        self.limit = (len(args) >= 5 and args[4]) or None
        self.offset = (len(args) >= 6 and args[5]) or None

        self.db_manager = DBManager()

        self.nypl_bib_service = NYPLBibService()

    def runProcess(self):
        try:
            self.db_manager.createSession()
            record_buffer = RecordBuffer(self.db_manager)

            start_datetime = (
                datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=24)
                if self.process_type == 'daily'
                else self.ingest_period and datetime.strptime(self.ingest_period, '%Y-%m-%dT%H:%M:%S')
            )

            records = self.nypl_bib_service.get_records(
                start_timestamp=start_datetime,
                offset=self.offset,
                limit=self.limit
            )
            
            for record_mapping in records:
                record_buffer.add(record_mapping.record)
            
            record_buffer.flush()

            logger.info(f'Ingested {record_buffer.ingest_count} NYPL records')
        except Exception as e:
            logger.exception(f'Failed to ingest NYPL records')
            raise e
        finally:
            self.db_manager.close_connection()

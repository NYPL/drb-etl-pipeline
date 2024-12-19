from ..core import CoreProcess
from logger import create_log
from managers import DBManager
from ..record_buffer import RecordBuffer
from services import NYPLBibService

logger = create_log(__name__)


class NYPLProcess(CoreProcess):
    def __init__(self, *args):
        super(NYPLProcess, self).__init__(*args[:4])

        self.limit = (len(args) >= 5 and args[4]) or None
        self.offset = (len(args) >= 6 and args[5]) or None

        self.nypl_bib_service = NYPLBibService()

        self.db_manager = DBManager()

        self.db_manager.generateEngine()
        self.db_manager.createSession()

        self.record_buffer = RecordBuffer(db_manager=self.db_manager)

    def runProcess(self):
        try:
            if self.process == 'daily':
                records = self.nypl_bib_service.get_records(offset=self.offset, limit=self.limit)
            elif self.process == 'complete':
                records = self.nypl_bib_service.get_records(full_import=True)
            elif self.process == 'custom':
                records = self.nypl_bib_service.get_records(start_timestamp=self.ingestPeriod, offset=self.offset, limit=self.limit)
            else: 
                logger.warning(f'Unknown NYPL ingestion process type {self.process}')
                return
            
            for record in records:
                self.record_buffer.add(record)
            
            self.record_buffer.flush()

            logger.info(f'Ingested {self.record_buffer.ingest_count} NYPL records')
        except Exception as e:
            logger.exception(f'Failed to ingest NYPL records')
            raise e
        finally:
            self.db_manager.close_connection()

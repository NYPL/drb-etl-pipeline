from ..core import CoreProcess
from logger import create_log
from services import NYPLBibService

logger = create_log(__name__)


class NYPLProcess(CoreProcess):
    def __init__(self, *args):
        super(NYPLProcess, self).__init__(*args[:4])

        self.limit = (len(args) >= 5 and args[4]) or None
        self.offset = (len(args) >= 6 and args[5]) or None

        self.nypl_bib_service = NYPLBibService()

    def runProcess(self):
        try:
            self.generateEngine()
            self.createSession()

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
                self.addDCDWToUpdateList(record)
            
            self.saveRecords()
            self.commitChanges()

            logger.info(f'Ingested {len(self.records)} NYPL records')
        except Exception as e:
            logger.exception(f'Failed to ingest NYPL records')
            raise e
        finally:
            self.close_connection()

from logger import create_log
from managers import DBManager
from services import HathiTrustService
from ..record_buffer import RecordBuffer
from .. import utils

logger = create_log(__name__)

class HathiTrustProcess():
    def __init__(self, *args):
        self.params = utils.parse_process_args(*args)

        self.db_manager = DBManager()
        self.db_manager.create_session()

        self.record_buffer = RecordBuffer(db_manager=self.db_manager, batch_size=1000)

        self.hathi_trust_service = HathiTrustService()

    def runProcess(self) -> int:
        records = self.hathi_trust_service.get_records(
            start_timestamp=utils.get_start_datetime(process_type=self.params.process_type, ingest_period=self.params.ingest_period),
            offset=self.params.offset,
            limit=self.params.limit
        )

        for record in records:
            self.record_buffer.add(record=record)

        self.record_buffer.flush()

        logger.info(f'Ingested {self.record_buffer.ingest_count} Hathi Trust records')

        return self.record_buffer.ingest_count

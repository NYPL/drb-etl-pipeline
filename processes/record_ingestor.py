import json
import multiprocessing
import os
from sqlalchemy.orm import Session

from logger import create_log
from managers import DBManager, RabbitMQManager, S3Manager
from model import Record, FRBRStatus
from services.sources.source_service import SourceService
from . import utils

logger = create_log(__name__)


class RecordIngestor:

    def __init__(self, source_service: SourceService, source: str, *args):
        self.params = utils.parse_process_args(*args)
        self.source = source
        self.source_service = source_service

    def ingest(self) -> int:
        ingest_count = 0

        try:
            records = self.source_service.get_records(
                start_timestamp=utils.get_start_datetime(process_type=self.params.process_type, ingest_period=self.params.ingest_period),
                offset=self.params.offset,
                limit=self.params.limit
            )

            ingest_pipeline_pool = multiprocessing.Pool(processes=4)
            record_ingest_processes = [ingest_pipeline_pool.apply_async(self._ingest_record, args=(record,)) for record in records]

            ingest_results = [record_ingest_process.get() for record_ingest_process in record_ingest_processes]

            ingest_count = len([ingest_result for ingest_result in ingest_results if ingest_result is True])

            ingest_pipeline_pool.close()
            ingest_pipeline_pool.join()
        except Exception:
            logger.exception(f'Failed to ingest {self.source} records')

        logger.info(f'Ingested {ingest_count} {self.source} records')
        return ingest_count

    @staticmethod
    def _ingest_record(record: Record) -> bool:
        try:
            RecordIngestor._store_record_files(record=record)
            RecordIngestor._save_record(record=record)
            RecordIngestor._send_record_pipeline_message(record_id=record.id)

            return True
        except Exception:
            logger.exception(f'Failed to ingest record: {record}')
            return False
        
    @staticmethod
    def _save_record(record: Record):
        try:
            db_manager = DBManager()

            with Session(db_manager.generateEngine()) as session, session.begin():
                existing_record = session.query(Record).filter(Record.source_id == record.source_id).first()

                if existing_record:
                    record = RecordIngestor._update_record(record, existing_record)

                session.add(record)
        finally: 
            db_manager.engine.dispose()
        
    @staticmethod
    def _send_record_pipeline_message(record_id: int):
        try:
            record_pipeline_queue = os.environ.get('RECORD_PIPELINE_QUEUE')
            record_pipeline_route = os.environ.get('RECORD_PIPELINE_ROUTING_KEY')

            rabbitmq_manager = RabbitMQManager()
            rabbitmq_manager.createRabbitConnection()
            rabbitmq_manager.createOrConnectQueue(record_pipeline_queue, record_pipeline_route)

            rabbitmq_manager.sendMessageToQueue(
                queueName=record_pipeline_queue,
                routingKey=record_pipeline_route,
                message=json.dumps({ 'recordId': record_id })
            )
        finally:
            rabbitmq_manager.closeRabbitConnection()

    @staticmethod
    def _store_record_files(record: Record):
        s3_manager = S3Manager()
        s3_manager.createS3Client()
        file_bucket = os.environ.get('FILE_BUCKET')

        s3_manager.store_pdf_manifest(record=record, bucket_name=file_bucket)

    @staticmethod
    def _update_record(record: Record, existing_record: Record) -> Record:
        for attribute, value in record:
            if attribute == 'uuid': 
                continue

            setattr(existing_record, attribute, value)
        
        existing_record.cluster_status = False
        
        if existing_record.source not in ['oclcClassify', 'oclcCatalog']:
            existing_record.frbr_status = FRBRStatus.TODO.value

        return existing_record

import json
import os
from time import sleep

from .core import CoreProcess
from logger import createLog
from model import Record
from processes import ClassifyProcess, ClusterProcess

logger = createLog(__name__)


class RecordTransformProcess(CoreProcess):
    def __init__(self, *args):
        super(RecordTransformProcess, self).__init__(*args[:4])

        self.createRabbitConnection()
        self.createChannel()

        self.classify_process = ClassifyProcess(*args)
        self.cluster_process = ClusterProcess(*args)

    def runProcess(self):
        try:
            self.generateEngine()
            self.createSession()

            self.process_record_messages()
        except Exception as e:
            logger.exception(f'Failed to run record transform process')
            raise e

    def process_record_messages(self, max_attempts: int=4):
        for attempt in range(0, max_attempts):
            wait_time = 60 * attempt

            if wait_time:
                logger.info(f'Waiting {wait_time}s for OCLC catalog messages')
                sleep(wait_time)

            while message := self.getMessageFromQueue(os.environ['RECORD_QUEUE']):
                message_props, _, message_body = message

                if not message_props or not message_body:
                    break

                self.process_record_message(message_body)
                self.acknowledgeMessageProcessed(message_props.delivery_tag)

    def process_record_message(self, record_message: str):
        message = json.loads(record_message)
        record_id = message.get('recordId')

        self.transform_record(record_id)
    
    def transform_record(self, record_id: str):
        record = self.session.query(Record).get(record_id)

        if not record:
            return
        
        self.classify_process.frbrize_record(record)

        self.saveRecords()
        self.commitChanges()

        work, stale_work_ids = self.cluster_process.cluster_record(record)

        self.cluster_process.update_elastic_search([work], stale_work_ids)
        self.cluster_process.delete_stale_works(stale_work_ids)

        self.commitChanges()

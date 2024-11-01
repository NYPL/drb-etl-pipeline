from managers import DBManager, RabbitMQManager, RedisManager, ElasticsearchManager, S3Manager
from model import Record
from static.manager import StaticManager
import os

from logger import createLog


logger = createLog(__name__)


class CoreProcess(DBManager, RabbitMQManager, RedisManager, StaticManager,
                  ElasticsearchManager, S3Manager):
    def __init__(self, process, customFile, ingestPeriod, singleRecord, batchSize=500):
        super(CoreProcess, self).__init__()
        self.process = process
        self.customFile = customFile
        self.ingestPeriod = ingestPeriod
        self.singleRecord = singleRecord

        self.batchSize = batchSize
        self.records = set()

        self.record_queue = os.environ['RECORD_QUEUE']
        self.record_route = os.environ['RECORD_ROUTING_KEY']
        self.createRabbitConnection()
        self.createOrConnectQueue(self.record_queue, self.record_route)

    def addDCDWToUpdateList(self, rec):
        existing = self.session.query(Record)\
            .filter(Record.source_id == rec.record.source_id).first()
        if existing:
            logger.debug('Existing record: ' + str(existing))
            rec.updateExisting(existing)

            try:
                self.records.remove(existing)
            except KeyError:
                logger.debug('Record not in current set')

            self.records.add(existing)
        else:
            logger.debug('New record: ' + str(rec.record))
            self.records.add(rec.record)

        if len(self.records) >= self.batchSize:
            self.saveRecords()
            self.records = set()

    def windowedQuery(self, table, query, windowSize=100):
        singleEntity = query.is_single_entity
        query = query.add_column(table.date_modified).order_by(table.date_modified)
        query = query.add_column(table.id).order_by(table.id)

        lastID = None
        totalFetched = 0

        while True:
            subQuery = query

            if lastID is not None:
                subQuery = subQuery.filter(table.id > lastID)

            queryChunk = subQuery.limit(windowSize).all()
            totalFetched += windowSize

            if not queryChunk or (self.ingestLimit and totalFetched > self.ingestLimit):
                break

            lastID = queryChunk[-1][-1]

            for row in queryChunk:
                yield row[0] if singleEntity else row[0:-2]

    def saveRecords(self):
        self.bulkSaveObjects(self.records)

    def sendFileToProcessingQueue(self, fileURL, s3Location):
        s3Message = {
            'fileData': {
                'fileURL': fileURL,
                'bucketPath': s3Location
            }
        }
        self.sendMessageToQueue(self.fileQueue, self.fileRoute, s3Message)

    def ingest_records(self, records: list[Record]):
        existing_records_map = { 
            existing_record.source_id: existing_record
            for existing_record in
            (
                self.session.query(Record)
                    .filter(Record.source_id.in_([record.source_id for record in records]))
                    .all()
            )
        }

        for i, record in enumerate(records):
            existing_record = existing_records_map.get(record.source_id)

            if existing_record:
                for attribute, value in record:
                    if attribute == 'uuid' or attribute == 'id': continue
                    setattr(existing_record, attribute, value)
                
                records[i] = existing_record

        updated_records = self.bulkSaveObjects(records)

        for updated_record in updated_records:
            self.sendMessageToQueue(self.record_queue, self.record_route, { 'recordId': updated_record.id })

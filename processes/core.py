from managers import DBManager, RabbitMQManager, RedisManager, ElasticsearchManager, S3Manager, NyplApiManager
from model import Record
from static.manager import StaticManager


class CoreProcess(DBManager, NyplApiManager, RabbitMQManager, RedisManager, StaticManager,
                  ElasticsearchManager, S3Manager):
    def __init__(self, process, customFile, ingestPeriod, singleRecord, batchSize=500):
        super(CoreProcess, self).__init__()
        self.process = process
        self.customFile = customFile
        self.ingestPeriod = ingestPeriod
        self.singleRecord = singleRecord

        self.batchSize = batchSize
        self.records = set()
    
    def addDCDWToUpdateList(self, rec):
        existing = self.session.query(Record)\
            .filter(Record.source_id == rec.record.source_id).first()
        if existing:
            print('EXISTING', existing)
            rec.updateExisting(existing)

            try:
                self.records.remove(existing)
            except KeyError:
                print('Record not in current set')

            self.records.add(existing)
        else:
            print('NEW', rec.record)
            self.records.add(rec.record)
        
        if len(self.records) >= self.batchSize:
            self.saveRecords()
            self.records = set()
    
    def windowedQuery(self, table, query, windowSize=100):
        singleEntity = query.is_single_entity
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
                yield row[0] if singleEntity else row[0:-1]
    
    def saveRecords(self):
        self.bulkSaveObjects(self.records)

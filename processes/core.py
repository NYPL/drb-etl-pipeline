from managers import DBManager, RabbitMQManager, RedisManager, ElasticsearchManager, S3Manager, NyplApiManager
from model import Record
from static.manager import StaticManager


class CoreProcess(DBManager, NyplApiManager, RabbitMQManager, RedisManager, StaticManager,
                  ElasticsearchManager, S3Manager):
    def __init__(self, process, customFile, ingestPeriod, singleRecord):
        super(CoreProcess, self).__init__()
        self.process = process
        self.customFile = customFile
        self.ingestPeriod = ingestPeriod
        self.singleRecord = singleRecord

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
        
        if len(self.records) >= 500:
            self.saveRecords()
            self.records = set()
    
    def saveRecords(self):
        self.bulkSaveObjects(self.records)

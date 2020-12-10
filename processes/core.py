from managers import DBManager, RabbitMQManager, RedisManager, ElasticsearchManager, S3Manager
from model import Record
from static.manager import StaticManager


class CoreProcess(DBManager, RabbitMQManager, RedisManager, StaticManager, ElasticsearchManager, S3Manager):
    def __init__(self, process, customFile, ingestPeriod):
        super(CoreProcess, self).__init__()
        self.process = process
        self.customFile = customFile
        self.ingestPeriod = ingestPeriod

        self.records = []
    
    def addDCDWToUpdateList(self, rec):
        existing = self.session.query(Record)\
            .filter(Record.source_id == rec.record.source_id).first()
        if existing:
            print('EXISTING', existing)
            rec.updateExisting(existing)
            self.records.append(existing)
        else:
            print('NEW', rec.record)
            self.records.append(rec.record)
        
        if len(self.records) >= 10000:
            self.saveRecords()
            self.records = []
    
    def saveRecords(self):
        self.bulkSaveObjects(self.records)

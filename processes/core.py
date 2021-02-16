from managers import DBManager, RabbitMQManager, RedisManager, ElasticsearchManager, S3Manager, NyplApiManager
from model import Record
from static.manager import StaticManager
from logger import createLog

logger = createLog(__name__)


class CoreProcess(DBManager, NyplApiManager, RabbitMQManager, RedisManager, StaticManager,
                  ElasticsearchManager, S3Manager):
    def __init__(self, process, customFile, ingestPeriod, singleRecord):
        super(CoreProcess, self).__init__()
        self.process = process
        self.customFile = customFile
        self.ingestPeriod = ingestPeriod
        self.singleRecord = singleRecord

        self.records = []
    
    def addDCDWToUpdateList(self, rec):
        existing = self.session.query(Record)\
            .filter(Record.source_id == rec.record.source_id).first()
        if existing:
            logger.info('EXISTING {}'.format(existing))
            rec.updateExisting(existing)
            self.records.append(existing)
        else:
            logger.info('NEW {}'.format(rec.record))
            self.records.append(rec.record)
        
        if len(self.records) >= 10000:
            logger.info('Saving batch of {} records'.format(len(self.records)))
            self.saveRecords()
            self.records = []
    
    def saveRecords(self):
        self.bulkSaveObjects(self.records)

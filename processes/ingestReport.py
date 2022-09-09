from datetime import datetime, timedelta
import newrelic.agent
from sqlalchemy import func

from .core import CoreProcess
from model import Work, Edition, Item, Record
from managers import SmartSheetManager
from logger import createLog

logger = createLog(__name__)


class IngestReportProcess(CoreProcess):
    def __init__(self, *args):
        super(IngestReportProcess, self).__init__(*args[:4])

        # PostgreSQL Connection
        self.generateEngine()
        self.createSession()

        # Smartsheet SDK
        self.smartsheet = SmartSheetManager()
        self.smartsheet.createClient()

    def runProcess(self):
        self.generateReport()

    @newrelic.agent.background_task()
    def generateReport(self):
        ingestDate = datetime.today()
        ingestDateStart = ingestDate.replace(hour=0, minute=0, second=0)
        ingestDateEnd = ingestDateStart + timedelta(days=1)

        dailyRow = {'Date': {'value': ingestDate.strftime('%Y-%m-%d')}}
        for table in [Work, Edition, Item, Record]:
            totals = self.getTableCounts(table, ingestDateStart, ingestDateEnd)
            dailyRow = {**dailyRow, **totals}

        self.smartsheet.insertRow(dailyRow)

    @newrelic.agent.background_task()
    def getTableCounts(self, table, ingestStart, ingestEnd):
        logger.info('Getting Totals for {}'.format(table.__name__))

        totalCount = self.session.query(func.count(table.id)).scalar()

        modifiedCount = self.session.query(table.id)\
            .filter(table.date_modified > ingestStart)\
            .filter(table.date_modified < ingestEnd)\
            .filter(table.date_created < ingestStart)\
            .count()

        createdCount = self.session.query(table.id)\
            .filter(table.date_modified > ingestStart)\
            .filter(table.date_modified < ingestEnd)\
            .count()

        totals = self.setAnomalyStatus(totalCount, modifiedCount, createdCount)

        return {
            'Total {}s'.format(table.__name__): totals['total'],
            '{}s Modified'.format(table.__name__): totals['modified'],
            '{}s Created'.format(table.__name__): totals['created'] 
        }

    @newrelic.agent.background_task()
    @staticmethod
    def setAnomalyStatus(total, modified, created):
        anomalyThreshold = total / 10

        return {
            'total': {'value': total, 'anomaly': False},
            'modified': {'value': modified, 'anomaly': modified > anomalyThreshold},
            'created': {'value': created, 'anomaly': created > anomalyThreshold}
        }

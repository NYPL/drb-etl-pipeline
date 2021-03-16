from datetime import date, timedelta
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import DATE

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

    def generateReport(self):
        ingestDate = date.today() - timedelta(days=1)

        dailyRow = {'Date': {'value': ingestDate.strftime('%Y-%m-%d')}}
        for table in [Work, Edition, Item, Record]:
            totals = self.getTableCounts(table, ingestDate)
            dailyRow = {**dailyRow, **totals}

        self.smartsheet.insertRow(dailyRow)

    def getTableCounts(self, table, ingestPeriod):
        logger.info('Getting Totals for {}'.format(table.__name__))

        totalCount = self.session.query(table.id).count()

        modifiedCount = self.session.query(table.id)\
            .filter(func.cast(table.date_modified, DATE) == ingestPeriod)\
            .filter(func.cast(table.date_created, DATE) < ingestPeriod)\
            .count()

        createdCount = self.session.query(table.id)\
            .filter(func.cast(table.date_created, DATE) == ingestPeriod)\
            .count()

        totals = self.setAnomalyStatus(totalCount, modifiedCount, createdCount)

        return {
            'Total {}s'.format(table.__name__): totals['total'],
            '{}s Modified'.format(table.__name__): totals['modified'],
            '{}s Created'.format(table.__name__): totals['created'] 
        }

    @staticmethod
    def setAnomalyStatus(total, modified, created):
        anomalyThreshold = total / 10

        return {
            'total': {'value': total, 'anomaly': False},
            'modified': {'value': modified, 'anomaly': modified > anomalyThreshold},
            'created': {'value': created, 'anomaly': created > anomalyThreshold}
        }

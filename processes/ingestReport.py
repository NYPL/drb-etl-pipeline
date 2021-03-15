from datetime import datetime, timedelta

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
        print(self.smartsheet.client.Server.server_info())
        # raise Exception

    def runProcess(self):
        self.generateReport()

    def generateReport(self):
        now = datetime.utcnow()
        periodStart = now - timedelta(days=1)

        dailyRow = {'Date': {'value': now.strftime('%Y-%m-%d')}}
        for table in [Work, Edition, Item, Record]:
            totals = self.getTableCounts(table, periodStart)
            dailyRow = {**dailyRow, **totals}

        self.smartsheet.insertRow(dailyRow)

    def getTableCounts(self, table, periodStart):
        logger.info('Getting Totals for {}'.format(table.__name__))

        totalCount = self.session.query(table.id).count()

        modifiedCount = self.session.query(table.id)\
            .filter(table.date_modified > periodStart)\
            .filter(table.date_created < periodStart)\
            .count()

        createdCount = self.session.query(table.id)\
            .filter(table.date_created > periodStart).count()

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

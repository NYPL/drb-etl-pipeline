from datetime import datetime, timedelta
import pytest

from processes import IngestReportProcess
from model import Work, Edition, Item, Record


class TestIngestReportProcess:
    @pytest.fixture
    def testInstance(self, mocker):
        class TestIngestReportProcess(IngestReportProcess):
            def __init__(self, *args):
                self.smartsheet = mocker.MagicMock()
                self.session = mocker.MagicMock()
        
        return TestIngestReportProcess('TestProcess', 'testFile', 'testDate')
    
    def test_runProcess(self, testInstance, mocker):
        mockGenerate = mocker.patch.object(IngestReportProcess, 'generateReport')

        testInstance.runProcess()

        mockGenerate.assert_called_once()

    def test_generateReport(self, testInstance, mocker):
        now = datetime.today()
        mockDate = mocker.patch('processes.ingestReport.datetime')
        mockDate.today.return_value = now
        startStr = now.strftime('%Y-%m-%d')
        startTime = now.replace(hour=0, minute=0, second=0)
        endTime = startTime + timedelta(days=1)

        mockGetTable = mocker.patch.object(IngestReportProcess, 'getTableCounts')
        mockGetTable.side_effect = [
            {'Works': 'test'}, {'Editions': 'test'}, {'Items': 'test'}, {'Records': 'test'}
        ]

        testInstance.generateReport()

        mockGetTable.assert_has_calls([
            mocker.call(Work, startTime, endTime),
            mocker.call(Edition, startTime, endTime),
            mocker.call(Item, startTime, endTime),
            mocker.call(Record, startTime, endTime)
        ])
        testInstance.smartsheet.insertRow.assert_called_once_with(
            {'Date': {'value': startStr}, 'Works': 'test', 'Editions': 'test', 'Items': 'test', 'Records': 'test'}
        )

    def test_getTableCounts(self, testInstance, mocker):
        testInstance.session.query().scalar.return_value = 10 # total
        testInstance.session.query().filter().filter().filter().count.return_value = 3 # modified
        testInstance.session.query().filter().filter().count.return_value = 2 # created

        mockAnomaly = mocker.patch.object(IngestReportProcess, 'setAnomalyStatus')
        mockAnomaly.return_value = {'total': 10, 'modified': 3, 'created': 2}

        mockTable = mocker.MagicMock(__name__='Test', id=1, date_modified=1, date_created=1)
        testCounts = testInstance.getTableCounts(mockTable, 0, 1)

        assert testCounts['Total Tests'] == 10
        assert testCounts['Tests Modified'] == 3
        assert testCounts['Tests Created'] == 2
        mockAnomaly.assert_called_once_with(10, 3, 2)

    def test_setAnomalyStatus(self):
        testAnomalyObject = IngestReportProcess.setAnomalyStatus(100, 25, 5)

        assert testAnomalyObject['total'] == {'value': 100, 'anomaly': False}
        assert testAnomalyObject['modified'] == {'value': 25, 'anomaly': True}
        assert testAnomalyObject['created'] == {'value': 5, 'anomaly': False}

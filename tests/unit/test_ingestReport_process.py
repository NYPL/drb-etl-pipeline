from datetime import date, timedelta
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
        now = date.today()
        startTime = now - timedelta(days=1)
        mockDate = mocker.patch('processes.ingestReport.date')
        mockDate.today.return_value = now 
        startStr = startTime.strftime('%Y-%m-%d')

        mockGetTable = mocker.patch.object(IngestReportProcess, 'getTableCounts')
        mockGetTable.side_effect = [
            {'Works': 'test'}, {'Editions': 'test'}, {'Items': 'test'}, {'Records': 'test'}
        ]

        testInstance.generateReport()

        mockGetTable.assert_has_calls([
            mocker.call(Work, startTime), mocker.call(Edition, startTime),
            mocker.call(Item, startTime), mocker.call(Record, startTime)
        ])
        testInstance.smartsheet.insertRow.assert_called_once_with(
            {'Date': {'value': startStr}, 'Works': 'test', 'Editions': 'test', 'Items': 'test', 'Records': 'test'}
        )

    def test_getTableCounts(self, testInstance, mocker):
        testInstance.session.query().count.return_value = 10 # total
        testInstance.session.query().filter().filter().count.return_value = 3 # modified
        testInstance.session.query().filter().count.return_value = 2 # created

        mockAnomaly = mocker.patch.object(IngestReportProcess, 'setAnomalyStatus')
        mockAnomaly.return_value = {'total': 10, 'modified': 3, 'created': 2}

        mockTable = mocker.MagicMock(__name__='Test', id=1, date_modified=1, date_created=1)
        testCounts = testInstance.getTableCounts(mockTable, 0)

        assert testCounts['Total Tests'] == 10
        assert testCounts['Tests Modified'] == 3
        assert testCounts['Tests Created'] == 2
        mockAnomaly.assert_called_once_with(10, 3, 2)

    def test_setAnomalyStatus(self):
        testAnomalyObject = IngestReportProcess.setAnomalyStatus(100, 25, 5)

        assert testAnomalyObject['total'] == {'value': 100, 'anomaly': False}
        assert testAnomalyObject['modified'] == {'value': 25, 'anomaly': True}
        assert testAnomalyObject['created'] == {'value': 5, 'anomaly': False}

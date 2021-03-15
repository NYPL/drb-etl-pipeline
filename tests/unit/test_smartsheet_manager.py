import pytest

from managers import SmartSheetManager
from tests.helper import TestHelpers


class TestNYPLApiManager:
    @classmethod
    def setup_class(cls):
        TestHelpers.setEnvVars()

    @classmethod
    def teardown_class(cls):
        TestHelpers.clearEnvVars()

    @pytest.fixture
    def testInstance(self):
        return SmartSheetManager()

    def test_initializer(self, testInstance):
        assert testInstance.apiToken == 'test_smartsheet_token'
        assert testInstance.sheetID == 1000
        assert testInstance.client == None

    def test_createClient(self, testInstance, mocker):
        mockClient = mocker.MagicMock()
        mockSheet = mocker.patch('managers.smartsheet.smartsheet')
        mockSheet.Smartsheet.return_value = mockClient

        testInstance.createClient()

        assert testInstance.client == mockClient
        mockSheet.Smartsheet.assert_called_once_with('test_smartsheet_token')
        testInstance.client.errors_as_exceptions.assert_called_once_with(True)

    def test_getColumns(self, testInstance, mocker):
        mockColumn = mocker.MagicMock(title='Test Column', id=1)
        mockResp = mocker.MagicMock(data=[mockColumn])
        testInstance.client = mocker.MagicMock()
        testInstance.client.Sheets.get_columns.return_value = mockResp

        testColumns = testInstance.getColumns()

        assert testColumns == {'Test Column': 1}
        testInstance.client.Sheets.get_columns.assert_called_once_with(
            1000, include_all=True
        )

    def test_insertRow(self, testInstance, mocker):
        testInstance.client = mocker.MagicMock()
        sheetMocks = mocker.patch.multiple(
            SmartSheetManager,
            createNewRow=mocker.DEFAULT,
            getColumns=mocker.DEFAULT,
            getRows=mocker.DEFAULT
        )
        mockRow = mocker.MagicMock()
        sheetMocks['createNewRow'].return_value = mockRow
        sheetMocks['getColumns'].return_value = {'Date': 1, 'Col ID': 2, 'Test': 3, 'Test2': 4}
        sheetMocks['getRows'].return_value = []

        testInstance.insertRow(
            {'Date': {'value': 'testDate'}, 'Test': {'value': 10}, 'Test2': {'value': 25, 'anomaly': True}}
        )

        sheetMocks['createNewRow'].assert_called_once()
        sheetMocks['getColumns'].assert_called_once()
        sheetMocks['getRows'].assert_called_once_with(columnIDs=[2], modifiedSince='testDate')
        mockRow.cells.append.assert_has_calls([
            mocker.call({'column_id': 1, 'value': 'testDate', 'format': ',,,,,,,,,3,,,,,,,'}),
            mocker.call({'column_id': 3, 'value': 10, 'format': ',,,,,,,,,3,,,,,,,'}),
            mocker.call({'column_id': 4, 'value': 25, 'format': ',,,,,,,,,28,,,,,,,'}),
            mocker.call({'column_id': 2, 'value': 1, 'format': ',,,,,,,,,3,,,,,,,'})
        ])
        testInstance.client.Sheets.add_rows.assert_called_once_with(1000, [mockRow])
         
    def test_getRows(self, testInstance, mocker):
        mockClient = mocker.MagicMock()
        testInstance.client = mockClient
        mockClient.Sheets.get_sheet.return_value = mocker.MagicMock(rows=[1, 2])

        testRows = testInstance.getRows(columnIDs=[1], modifiedSince='testDate')

        assert testRows == [1, 2]
        mockClient.Sheets.get_sheet.assert_called_once_with(
            1000, column_ids=[1], rows_modified_since='testDate'
        )

    def test_createNewRow(self, mocker):
        mockSheet = mocker.patch('managers.smartsheet.smartsheet')
        mockSheet.models.Row.return_value = 'testRow'

        assert SmartSheetManager.createNewRow() == 'testRow'
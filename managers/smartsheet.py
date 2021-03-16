import os
import smartsheet

class SmartSheetManager:
    def __init__(self, apiToken=None, sheetID=None):
        super(SmartSheetManager, self).__init__()
        self.apiToken = apiToken or os.environ['SMARTSHEET_API_TOKEN']
        self.sheetID = sheetID or int(os.environ['SMARTSHEET_SHEET_ID'])
        self.client = None

    def createClient(self):
        self.client = smartsheet.Smartsheet(self.apiToken)
        self.client.errors_as_exceptions(True)

    def getColumns(self):
        colResponse = self.client.Sheets.get_columns(
            self.sheetID, include_all=True
        )

        return {c.title: c.id for c in colResponse.data}

    def insertRow(self, rowData):
        newRow = self.createNewRow()

        columns = self.getColumns()

        rows = self.getRows(columnIDs=[columns['Col ID']], modifiedSince=rowData['Date']['value'])
        lastPCNum = int(rows[-1].cells[0].value) if len(rows) > 0 else 0
        rowData['Col ID'] = {'value': lastPCNum + 1}

        for name, value in rowData.items():
            colID = columns[name]

            cellValue = {'column_id': colID, 'value': value['value']}
            cellValue['format'] = ',,,,,,,,,28,,,,,,,' if value.get('anomaly', False) else ',,,,,,,,,3,,,,,,,'

            newRow.cells.append(cellValue)

        self.client.Sheets.add_rows(self.sheetID, [newRow])

    def getRows(self, columnIDs=None, modifiedSince=None):
        getSheetArgs = {}
        
        if columnIDs: getSheetArgs['column_ids'] = columnIDs

        if modifiedSince: getSheetArgs['rows_modified_since'] = modifiedSince

        sheetResp = self.client.Sheets.get_sheet(self.sheetID, **getSheetArgs)

        return sheetResp.rows

    @staticmethod
    def createNewRow():
        return smartsheet.models.Row()
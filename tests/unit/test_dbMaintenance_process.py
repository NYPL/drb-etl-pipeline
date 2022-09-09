import pytest

from processes import DatabaseMaintenanceProcess


class TestIngestReportProcess:
    @pytest.fixture
    def testInstance(self, mocker):
        class TestDatabaseMaintenanceProcess(DatabaseMaintenanceProcess):
            def __init__(self, *args):
                self.engine = mocker.MagicMock()

        return TestDatabaseMaintenanceProcess('TestProcess', 'testFile', 'testDate')

    def test_runProcess(self, testInstance, mocker):
        mockVacuum = mocker.patch.object(DatabaseMaintenanceProcess, 'vacuumTables')
        mockClose = mocker.patch.object(DatabaseMaintenanceProcess, 'closeConnection')

        testInstance.runProcess()

        mockVacuum.assert_called_once()
        mockClose.assert_called_once()

    def test_vacuumTables(self, testInstance, mocker):
        mockConnEnter = mocker.MagicMock()
        mockConn = mocker.MagicMock()
        testInstance.engine.connect.return_value = mockConnEnter
        mockConnEnter.__enter__.return_value = mockConn

        mockVacuum = mocker.patch.object(DatabaseMaintenanceProcess, 'vacuumTable')

        testInstance.vacuumTables()

        mockConn.execution_options.assert_called_once_with(isolation_level='AUTOCOMMIT')
        mockVacuum.assert_has_calls([
            mocker.call(mockConn, 'records'),
            mocker.call(mockConn, 'items'),
            mocker.call(mockConn, 'editions'),
            mocker.call(mockConn, 'works'),
            mocker.call(mockConn, 'links'),
            mocker.call(mockConn, 'rights'),
            mocker.call(mockConn, 'identifiers')
        ])

    def test_vacuumTable(self, testInstance, mocker):
        mockConn = mocker.MagicMock()

        testInstance.vacuumTable(mockConn, 'testTable')

        mockConn.execute.assert_called_once_with('VACUUM ANALYZE testTable;')
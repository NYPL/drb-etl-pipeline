import pytest
from unittest.mock import patch

from processes import DatabaseMaintenanceProcess


class TestDatabaseMaintenanceProcess:
    @pytest.fixture
    def db_maintenance_process(self) -> DatabaseMaintenanceProcess:
        with patch('processes.db_maintenance.DBManager'):  
            return DatabaseMaintenanceProcess()

    def test_run_process(self, db_maintenance_process: DatabaseMaintenanceProcess, mocker):
        mock_connection_enter = mocker.MagicMock()
        mock_connection = mocker.MagicMock()
        db_maintenance_process.db_manager.engine.connect.return_value = mock_connection_enter
        mock_connection_enter.__enter__.return_value = mock_connection

        db_maintenance_process.runProcess()

        db_maintenance_process.db_manager.generateEngine.assert_called_once()
        db_maintenance_process.db_manager.createSession.assert_called_once()

        mock_connection.execution_options.assert_called_once_with(isolation_level='AUTOCOMMIT')
        
        expected_vacuum_calls = [mocker.call(f'VACUUM ANALYZE {table};') for table in DatabaseMaintenanceProcess.VACUUMING_TABLES]
        assert mock_connection.execute.call_count == len(db_maintenance_process.VACUUMING_TABLES)
        mock_connection.execute.assert_has_calls(expected_vacuum_calls, any_order=True)
        
        db_maintenance_process.db_manager.closeConnection.assert_called_once()    

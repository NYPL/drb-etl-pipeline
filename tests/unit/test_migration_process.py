from alembic import config

from processes import MigrationProcess


class TestMigrationProcess:
    def test_api_runProcess(self, mocker):
        mockAlembic = mocker.patch.object(config, 'main')

        testProc = MigrationProcess(
            'TestProcess', 'testFile', 'testDate', 'testRecord', 'testLimit',
            'testOffset', ['testOpt1', 'testOpt2']
        )
        testProc.runProcess()

        mockAlembic.assert_called_once_with(
            argv=['--raiseerr', 'testOpt1', 'testOpt2']
        )

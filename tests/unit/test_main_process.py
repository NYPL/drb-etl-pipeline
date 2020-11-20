import pytest

from dcdw.main import main, registerProcesses, createArgParser, loadEnvFile


class TestMainProcess:
    @pytest.fixture
    def processArgs(self, mocker):
        mockArgs = mocker.MagicMock()
        mockArgs.process = 'TestProcess'
        mockArgs.ingestType = 'test'
        mockArgs.inputFile = 'testFile'
        mockArgs.startDate = 'testDate'

        return mockArgs

    def test_main(self, processArgs, mocker):
        mockRegister = mocker.patch('dcdw.main.registerProcesses')
        mockProcess = mocker.MagicMock()
        mockInstance = mocker.MagicMock()
        mockProcess.return_value = mockInstance
        mockRegister.return_value = {'TestProcess': mockProcess}

        main(processArgs)

        mockProcess.assert_called_with('test', 'testFile', 'testDate')
        mockInstance.runProcess.assert_called_once
        
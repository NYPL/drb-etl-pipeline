import inspect
import pytest
import sys
import yaml

from load_env import load_env_file
from main import main, registerProcesses, createArgParser
import processes


class TestMainProcess:

    @pytest.fixture
    def processArgs(self, mocker):
        mockArgs = mocker.MagicMock()
        mockArgs.process = 'TestProcess'
        mockArgs.ingestType = 'test'
        mockArgs.inputFile = 'testFile'
        mockArgs.startDate = 'testDate'
        mockArgs.singleRecord = 'testRecord'
        mockArgs.limit = 'testLimit'
        mockArgs.offset = 'testOffset'
        mockArgs.options = ['opt1', 'opt2']

        return mockArgs

    @pytest.fixture
    def sampleEnvFile(self):
        return {
            'TEST_NAME': 'test_name',
            'TEST_PORT': '9999'
        }

    def test_main(self, processArgs, mocker):
        mockRegister = mocker.patch('main.registerProcesses')
        mockProcess = mocker.MagicMock()
        mockInstance = mocker.MagicMock()
        mockProcess.return_value = mockInstance
        mockRegister.return_value = {'TestProcess': mockProcess}

        main(processArgs)

        mockProcess.assert_called_with(
            'test', 'testFile', 'testDate', 'testRecord', 'testLimit',
            'testOffset', ['opt1', 'opt2']
        )
        mockInstance.runProcess.assert_called_once

    def test_registerProcesses(self, mocker):
        mockInspect = mocker.patch('main.inspect.getmembers')
        mockInspect.return_value = {'TestProcess': 'mockProcess'}

        registeredProcs = registerProcesses()

        mockInspect.assert_called_with(processes, inspect.isclass)
        assert isinstance(registeredProcs, dict)
        assert registeredProcs['TestProcess'] == 'mockProcess'

    def test_argParser_allArgs_shortform(self, mocker):
        sys.argv = [
            'createArgParser',
            '-p', 'TestProcess',
            '-e', 'test',
            '-i', 'testIngest',
            '-f', 'testFile',
            '-s', 'testDate',
            '-l', 'testLimit',
            '-o', 'testOffset'
        ]

        argParser = createArgParser()
        testArgs = argParser.parse_args()

        assert testArgs.process == 'TestProcess'
        assert testArgs.environment == 'test'
        assert testArgs.ingestType == 'testIngest'
        assert testArgs.inputFile == 'testFile'
        assert testArgs.startDate == 'testDate'
        assert testArgs.limit == 'testLimit'
        assert testArgs.offset == 'testOffset'

    def test_argParser_allArgs_longform(self, mocker):
        sys.argv = [
            'createArgParser',
            '--process', 'TestProcess',
            '--environment', 'test',
            '--ingestType', 'testIngest',
            '--inputFile', 'testFile',
            '--startDate', 'testDate',
            '--limit', 'testLimit',
            '--offset', 'testOffset'
        ]

        argParser = createArgParser()
        testArgs = argParser.parse_args()

        assert testArgs.process == 'TestProcess'
        assert testArgs.environment == 'test'
        assert testArgs.ingestType == 'testIngest'
        assert testArgs.inputFile == 'testFile'
        assert testArgs.startDate == 'testDate'
        assert testArgs.limit == 'testLimit'
        assert testArgs.offset == 'testOffset'

    def test_argParser_missingReqArg(self, mocker):
        sys.argv = [
            'createArgParser',
            '--process', 'TestProcess'
        ]

        argParser = createArgParser()
        with pytest.raises(SystemExit):
            argParser.parse_args()

    def test_load_env_file_default_file(self, sampleEnvFile, mocker):
        mockStream = mocker.MagicMock()
        mockOpen = mocker.patch('load_env.open')
        mockOpen.return_value = mockStream
        mockYaml = mocker.patch('yaml.full_load')
        mockYaml.return_value = sampleEnvFile
        mockEnviron = mocker.patch.dict('os.environ', {})

        load_env_file('test', None)

        mockOpen.assert_called_with('local.yaml')

        assert mockEnviron['TEST_NAME'] == 'test_name'
        assert mockEnviron['TEST_PORT'] == '9999'
        
    def test_load_env_file_specified_file(self, sampleEnvFile, mocker):
        mockStream = mocker.MagicMock()
        mockOpen = mocker.patch('load_env.open')
        mockOpen.return_value = mockStream
        mockYaml = mocker.patch('yaml.full_load')
        mockYaml.return_value = sampleEnvFile
        mockEnviron = mocker.patch.dict('os.environ', {})

        load_env_file('test', './test/path/{}.yaml')

        mockOpen.assert_called_with('./test/path/test.yaml')

        assert mockEnviron['TEST_NAME'] == 'test_name'
        assert mockEnviron['TEST_PORT'] == '9999'

    def test_load_env_file_missing_file(self, sampleEnvFile, mocker):
        mockOpen = mocker.patch('load_env.open')
        mockOpen.side_effect = FileNotFoundError
        mockYaml = mocker.patch('yaml.full_load')
        mockEnviron = mocker.patch.dict('os.environ', {})

        with pytest.raises(FileNotFoundError):
            load_env_file('test', None)
            mockYaml.assert_not_called

        assert mockEnviron.get('TEST_NAME', None) is None
        assert mockEnviron.get('TEST_PORT', None) is None

    def test_load_env_file_invalid_yaml(self, sampleEnvFile, mocker):
        mockStream = mocker.MagicMock()
        mockOpen = mocker.patch('load_env.open')
        mockOpen.return_value = mockStream
        mockYaml = mocker.patch('yaml.full_load')
        mockYaml.side_effect = yaml.YAMLError
        mockEnviron = mocker.patch.dict('os.environ', {})

        with pytest.raises(yaml.YAMLError):
            load_env_file('test', None)

        assert mockEnviron.get('TEST_NAME', None) is None
        assert mockEnviron.get('TEST_PORT', None) is None

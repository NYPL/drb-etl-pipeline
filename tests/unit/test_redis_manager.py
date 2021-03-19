from datetime import datetime
import pytest

from managers import RedisManager


class TestRedisManager:
    @pytest.fixture
    def testInstance(self, mocker):
        mocker.patch.dict('os.environ', {
            'REDIS_HOST': 'host', 'REDIS_PORT': 'port', 'ENVIRONMENT': 'testEnv'
        })
        return RedisManager()

    def test_initializer(self, testInstance):
        assert testInstance.redisHost == 'host'
        assert testInstance.redisPort == 'port'

    def test_createRedisClient(self, testInstance, mocker):
        mockRedis = mocker.patch('managers.redis.Redis')
        mockRedis.return_value = 'testClient'

        testInstance.createRedisClient()

        assert testInstance.redisClient == 'testClient'
        mockRedis.assert_called_once_with(
            host='host', port='port', socket_timeout=5
        )

    def test_checkSetRedis_key_found_recent(self, testInstance, mocker):
        testInstance.redisClient = mocker.MagicMock()
        testInstance.redisClient.get.return_value = datetime.now().strftime('%Y-%m-%dT%H:%M:%S').encode('utf-8')

        mockSet = mocker.patch.object(RedisManager, 'setRedis')

        assert testInstance.checkSetRedis('test', 1, 'test') is True
        testInstance.redisClient.get.assert_called_once_with('testEnv/test/1/test')
        mockSet.assert_not_called

    def test_checkSetRedis_key_found_old(self, testInstance, mocker):
        testInstance.redisClient = mocker.MagicMock()
        testInstance.redisClient.get.return_value = datetime(1900, 1, 1).strftime('%Y-%m-%dT%H:%M:%S').encode('utf-8')

        mockSet = mocker.patch.object(RedisManager, 'setRedis')

        assert testInstance.checkSetRedis('test', 1, 'test') is False
        testInstance.redisClient.get.assert_called_once_with('testEnv/test/1/test')
        mockSet.assert_called_once

    def test_checkSetRedis_key_not_found(self, testInstance, mocker):
        testInstance.redisClient = mocker.MagicMock()
        testInstance.redisClient.get.return_value = None

        mockSet = mocker.patch.object(RedisManager, 'setRedis')

        assert testInstance.checkSetRedis('test', 1, 'test') is False
        testInstance.redisClient.get.assert_called_once_with('testEnv/test/1/test')
        mockSet.assert_called_once

    def test_setRedis(self, testInstance, mocker):
        testInstance.redisClient = mocker.MagicMock()

        testInstance.setRedis('test', 1, 'test', )

        testInstance.redisClient.set.assert_called_once_with(
            'testEnv/test/1/test', testInstance.presentTime.strftime('%Y-%m-%dT%H:%M:%S'), ex=604800
        )

    def test_checkIncrementerRedis_false(self, testInstance, mocker):
        testInstance.redisClient = mocker.MagicMock()
        testInstance.redisClient.get.return_value = b'1'

        assert testInstance.checkIncrementerRedis('test', 'id') == False

        testInstance.redisClient.get.assert_called_once_with(
            'test/{}/id'.format(testInstance.presentTime.strftime('%Y-%m-%d'))
        )

    def test_checkIncrementerRedis_true(self, testInstance, mocker):
        testInstance.redisClient = mocker.MagicMock()
        testInstance.redisClient.get.return_value = b'500001'

        assert testInstance.checkIncrementerRedis('test', 'id') == True

        testInstance.redisClient.get.assert_called_once_with(
            'test/{}/id'.format(testInstance.presentTime.strftime('%Y-%m-%d'))
        )

    def test_checkIncrementerRedis_none_false(self, testInstance, mocker):
        testInstance.redisClient = mocker.MagicMock()
        testInstance.redisClient.get.return_value = None

        assert testInstance.checkIncrementerRedis('test', 'id') == False

        testInstance.redisClient.get.assert_called_once_with(
            'test/{}/id'.format(testInstance.presentTime.strftime('%Y-%m-%d'))
        )

    def test_setIncrementerRedis(self, testInstance, mocker):
        testInstance.redisClient = mocker.MagicMock()

        testInstance.setIncrementerRedis('test', 'id')

        testInstance.redisClient.incr.assert_called_once_with(
            'test/{}/id'.format(testInstance.presentTime.strftime('%Y-%m-%d'))
        )


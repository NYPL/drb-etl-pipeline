import pytest
from pika.exceptions import StreamLostError

from managers import RabbitMQManager


class TestRabbitMQManager:
    @pytest.fixture
    def testInstance(self, mocker):
        mocker.patch.dict('os.environ', {
            'RABBIT_HOST': 'host',
            'RABBIT_PORT': 'port',
            'RABBIT_VIRTUAL_HOST': 'vhost',
            'RABBIT_EXCHANGE': 'exchng',
            'RABBIT_USER': 'testUser',
            'RABBIT_PSWD': 'testPswd'
        })

        return RabbitMQManager()

    def test_initializer(self, testInstance):
        assert testInstance.rabbitHost == 'host'
        assert testInstance.rabbitPort == 'port'
        assert testInstance.rabbitVirtualHost == 'vhost'
        assert testInstance.rabbitExchange == 'exchng'
        assert testInstance.rabbitUser == 'testUser'
        assert testInstance.rabbitPswd == 'testPswd'

    def test_createRabbitConnection(self, testInstance, mocker):
        mockParams = mocker.patch('managers.rabbitmq.ConnectionParameters')
        mockParams.return_value = 'testParams'
        mockConn = mocker.patch('managers.rabbitmq.BlockingConnection')
        mockConn.return_value = 'testConnection'
        mockCreateCreds = mocker.patch.object(RabbitMQManager, 'createRabbitCredentials')
        mockCreateCreds.return_value = 'testCredentials'

        testInstance.createRabbitConnection()

        assert testInstance.rabbitConn == 'testConnection'
        mockParams.assert_called_once_with(
            host='host',
            port='port',
            heartbeat=600,
            virtual_host='vhost',
            credentials='testCredentials'
        )
        mockConn.assert_called_once_with('testParams')

    def test_createRabbitCredentials(self, testInstance, mocker):
        mockCreds = mocker.patch('managers.rabbitmq.PlainCredentials')
        mockCreds.return_value = 'testCredentials'

        assert testInstance.createRabbitCredentials() == 'testCredentials'
        mockCreds.assert_called_once_with('testUser', 'testPswd')

    def test_closeRabbitConnection(self, testInstance, mocker):
        testInstance.rabbitConn = mocker.MagicMock()

        testInstance.closeRabbitConnection()

        testInstance.rabbitConn.close.assert_called_once

    def test_createChannel(self, testInstance, mocker):
        testInstance.rabbitConn = mocker.MagicMock()
        testInstance.rabbitConn.channel.return_value = 'testChannel'

        testInstance.createChannel()

        assert testInstance.channel == 'testChannel'
        testInstance.rabbitConn.channel.assert_called_once

    def test_createOrConnectQueue(self, testInstance, mocker):
        mockChannelCreate = mocker.patch.object(RabbitMQManager, 'createChannel')
        testInstance.channel = mocker.MagicMock()

        testInstance.createOrConnectQueue('testQueue', 'testKey')

        mockChannelCreate.assert_called_once
        testInstance.channel.queue_declare.assert_called_once_with(queue='testQueue', durable=True)
        testInstance.channel.queue_bind.assert_called_once_with(exchange='exchng', queue='testQueue', routing_key='testKey')

    def test_sendMessageToQueue_string(self, testInstance, mocker):
        testInstance.channel = mocker.MagicMock()

        testInstance.sendMessageToQueue('testQueue', 'testKey', 'testMessage')

        testInstance.channel.basic_publish.assert_called_once_with(
            exchange='exchng', routing_key='testKey', body='testMessage'
        )

    def test_sendMessageToQueue_dict(self, testInstance, mocker):
        testInstance.channel = mocker.MagicMock()

        testInstance.sendMessageToQueue('testQueue', 'testKey', {'test': 'message'})

        testInstance.channel.basic_publish.assert_called_once_with(
            exchange='exchng', routing_key='testKey', body='{"test": "message"}'
        )

    def test_getMessageFromQueue(self, testInstance, mocker):
        testInstance.channel = mocker.MagicMock()
        testInstance.channel.basic_get.return_value = 'testMessage'

        assert testInstance.getMessageFromQueue('testQueue') == 'testMessage'
        testInstance.channel.basic_get.assert_called_once_with('testQueue')

    def test_getMessageFromQueue_error(self, testInstance, mocker):
        testInstance.channel = mocker.MagicMock()
        testInstance.channel.basic_get.side_effect = [StreamLostError, 'testMessage']

        mockCreateConn = mocker.patch.object(RabbitMQManager, 'createRabbitConnection')
        mockCreateCh = mocker.patch.object(RabbitMQManager, 'createChannel')

        assert testInstance.getMessageFromQueue('testQueue') == 'testMessage'
        testInstance.channel.basic_get.assert_has_calls([
            mocker.call('testQueue'), mocker.call('testQueue')
        ])
        mockCreateConn.assert_called_once()
        mockCreateCh.assert_called_once()

    def test_acknowledgeMessageProcessed(self, testInstance, mocker):
        testInstance.channel = mocker.MagicMock()

        testInstance.acknowledgeMessageProcessed('testDeliveryTag')

        testInstance.channel.basic_ack.assert_called_once_with('testDeliveryTag')

    def test_acknowledgeMessageProcessed_error(self, testInstance, mocker):
        testInstance.channel = mocker.MagicMock()
        testInstance.channel.basic_ack.side_effect = [StreamLostError, None]

        mockCreateConn = mocker.patch.object(RabbitMQManager, 'createRabbitConnection')
        mockCreateCh = mocker.patch.object(RabbitMQManager, 'createChannel')

        testInstance.acknowledgeMessageProcessed('testDeliveryTag')

        testInstance.channel.basic_ack.assert_has_calls([
            mocker.call('testDeliveryTag'), mocker.call('testDeliveryTag')
        ])
        mockCreateConn.assert_called_once()
        mockCreateCh.assert_called_once()


import pytest

from managers import RabbitMQManager


class TestRabbitMQManager:
    @pytest.fixture
    def testInstance(self, mocker):
        mocker.patch.dict('os.environ', {'RABBIT_HOST': 'host', 'RABBIT_PORT': 'port'})
        return RabbitMQManager()

    def test_initializer(self, testInstance):
        assert testInstance.rabbitHost == 'host'
        assert testInstance.rabbitPort == 'port'

    def test_createRabbitConnection(self, testInstance, mocker):
        mockParams = mocker.patch('managers.rabbitmq.ConnectionParameters')
        mockParams.return_value = 'testParams'
        mockConn = mocker.patch('managers.rabbitmq.BlockingConnection')
        mockConn.return_value = 'testConnection'

        testInstance.createRabbitConnection()

        assert testInstance.rabbitConn == 'testConnection'
        mockParams.assert_called_once_with(host='host', port='port', heartbeat=600)
        mockConn.assert_called_once_with('testParams')

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

        testInstance.createOrConnectQueue('testQueue')

        mockChannelCreate.assert_called_once
        testInstance.channel.queue_declare.assert_called_once_with(queue='testQueue')

    def test_sendMessageToQueue_string(self, testInstance, mocker):
        testInstance.channel = mocker.MagicMock()

        testInstance.sendMessageToQueue('testQueue', 'testMessage')

        testInstance.channel.basic_publish.assert_called_once_with(
            exchange='', routing_key='testQueue', body='testMessage'
        )

    def test_sendMessageToQueue_dict(self, testInstance, mocker):
        testInstance.channel = mocker.MagicMock()

        testInstance.sendMessageToQueue('testQueue', {'test': 'message'})

        testInstance.channel.basic_publish.assert_called_once_with(
            exchange='', routing_key='testQueue', body='{"test": "message"}'
        )

    def test_getMessageFromQueue(self, testInstance, mocker):
        testInstance.channel = mocker.MagicMock()
        testInstance.channel.basic_get.return_value = 'testMessage'

        assert testInstance.getMessageFromQueue('testQueue') == 'testMessage'
        testInstance.channel.basic_get.assert_called_once_with('testQueue')

    def test_acknowledgeMessageProcessed(self, testInstance, mocker):
        testInstance.channel = mocker.MagicMock()

        testInstance.acknowledgeMessageProcessed('testDeliveryTag')

        testInstance.channel.basic_ack.assert_called_once_with('testDeliveryTag')


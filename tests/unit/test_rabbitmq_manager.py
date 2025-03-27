import pytest
from pika.exceptions import StreamLostError, ChannelClosedByBroker

from managers import RabbitMQManager


class TestRabbitMQManager:
    @pytest.fixture
    def test_instance(self, mocker):
        mocker.patch.dict('os.environ', {
            'RABBIT_HOST': 'host',
            'RABBIT_PORT': 'port',
            'RABBIT_VIRTUAL_HOST': 'vhost',
            'RABBIT_EXCHANGE': 'exchng',
            'RABBIT_USER': 'testUser',
            'RABBIT_PSWD': 'testPswd'
        })

        return RabbitMQManager()

    def test_initializer(self, test_instance):
        assert test_instance.host == 'host'
        assert test_instance.port == 'port'
        assert test_instance.virtual_host == 'vhost'
        assert test_instance.exchange == 'exchng'
        assert test_instance.username == 'testUser'
        assert test_instance.password == 'testPswd'

    def test_create_connection(self, test_instance, mocker):
        mock_params = mocker.patch('managers.rabbitmq.ConnectionParameters')
        mock_params.return_value = 'testParams'
        mock_conn = mocker.patch('managers.rabbitmq.BlockingConnection')
        mock_conn.return_value = 'testConnection'
        mock_create_creds = mocker.patch.object(RabbitMQManager, 'create_credentials')
        mock_create_creds.return_value = 'testCredentials'

        test_instance.create_connection()

        assert test_instance.connection == 'testConnection'
        mock_params.assert_called_once_with(
            host='host',
            port='port',
            heartbeat=600,
            virtual_host='vhost',
            credentials='testCredentials'
        )
        mock_conn.assert_called_once_with('testParams')

    def test_create_credentials(self, test_instance, mocker):
        mock_creds = mocker.patch('managers.rabbitmq.PlainCredentials')
        mock_creds.return_value = 'testCredentials'

        assert test_instance.create_credentials() == 'testCredentials'
        mock_creds.assert_called_once_with('testUser', 'testPswd')

    def test_close_connection(self, test_instance, mocker):
        test_instance.connection = mocker.MagicMock()

        test_instance.close_connection()

        test_instance.connection.close.assert_called_once

    def test_create_channel(self, test_instance, mocker):
        test_instance.connection = mocker.MagicMock()
        test_instance.connection.channel.return_value = 'testChannel'

        test_instance.create_channel()

        assert test_instance.channel == 'testChannel'
        test_instance.connection.channel.assert_called_once

    def test_create_or_connect_queue(self, test_instance, mocker):
        mock_channel_create = mocker.patch.object(RabbitMQManager, 'create_channel')
        test_instance.channel = mocker.MagicMock()

        test_instance.create_or_connect_queue('testQueue', 'testKey')

        mock_channel_create.assert_called_once
        test_instance.channel.queue_declare.assert_called_once_with(queue='testQueue', durable=True)
        test_instance.channel.queue_bind.assert_called_once_with(exchange='exchng', queue='testQueue', routing_key='testKey')

    def test_send_message_to_queue_string(self, test_instance, mocker):
        test_instance.channel = mocker.MagicMock()

        test_instance.send_message_to_queue('testQueue', 'testKey', 'testMessage')

        test_instance.channel.basic_publish.assert_called_once_with(
            exchange='exchng', routing_key='testKey', body='testMessage'
        )

    def test_send_message_to_queue_dict(self, test_instance, mocker):
        test_instance.channel = mocker.MagicMock()

        test_instance.send_message_to_queue('testQueue', 'testKey', {'test': 'message'})

        test_instance.channel.basic_publish.assert_called_once_with(
            exchange='exchng', routing_key='testKey', body='{"test": "message"}'
        )

    def test_get_message_from_queue(self, test_instance, mocker):
        test_instance.channel = mocker.MagicMock()
        test_instance.channel.basic_get.return_value = 'testMessage'

        assert test_instance.get_message_from_queue('testQueue') == 'testMessage'
        test_instance.channel.basic_get.assert_called_once_with('testQueue')

    def test_get_message_from_queue_error(self, test_instance, mocker):
        test_instance.channel = mocker.MagicMock()
        test_instance.channel.basic_get.side_effect = [StreamLostError, 'testMessage']

        mock_create_connection = mocker.patch.object(RabbitMQManager, 'create_connection')
        mock_create_channel = mocker.patch.object(RabbitMQManager, 'create_channel')

        assert test_instance.get_message_from_queue('testQueue') == 'testMessage'
        test_instance.channel.basic_get.assert_has_calls([
            mocker.call('testQueue'), mocker.call('testQueue')
        ])
        mock_create_connection.assert_called_once()
        mock_create_channel.assert_called_once()

    def test_get_message_from_queue_channel_closed_error(self, test_instance, mocker):
        test_instance.channel = mocker.MagicMock()
        test_instance.channel.basic_get.side_effect = ChannelClosedByBroker(500, 'test')

        mock_create_connection = mocker.patch.object(RabbitMQManager, 'create_connection')
        mock_create_channel = mocker.patch.object(RabbitMQManager, 'create_channel')

        assert test_instance.get_message_from_queue('testQueue') is None
        test_instance.channel.basic_get.assert_called_once_with('testQueue')
        mock_create_connection.assert_called_once()
        mock_create_channel.assert_called_once()

    def test_acknowledge_message_processed(self, test_instance, mocker):
        test_instance.channel = mocker.MagicMock()

        test_instance.acknowledge_message_processed('testDeliveryTag')

        test_instance.channel.basic_ack.assert_called_once_with('testDeliveryTag')

    def test_acknowledge_message_processed_error(self, test_instance, mocker):
        test_instance.channel = mocker.MagicMock()
        test_instance.channel.basic_ack.side_effect = [StreamLostError, None]

        mock_create_connection = mocker.patch.object(RabbitMQManager, 'create_connection')
        mock_create_channel = mocker.patch.object(RabbitMQManager, 'create_channel')

        test_instance.acknowledge_message_processed('testDeliveryTag')

        test_instance.channel.basic_ack.assert_has_calls([
            mocker.call('testDeliveryTag'), mocker.call('testDeliveryTag')
        ])
        mock_create_connection.assert_called_once()
        mock_create_channel.assert_called_once()


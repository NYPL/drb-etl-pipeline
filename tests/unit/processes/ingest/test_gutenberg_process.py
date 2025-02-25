import dataclasses
from datetime import datetime, timezone, timedelta
import json
import os
import pytest

from tests.helper import TestHelpers
from model import get_file_message, FileFlags, Part, Source
from processes import GutenbergProcess


class TestGutenbergProcess:
    @classmethod
    def setup_class(cls):
        TestHelpers.setEnvVars()

    @classmethod
    def teardown_class(cls):
        TestHelpers.clearEnvVars()

    @pytest.fixture
    def test_instance(self, mocker):
        class TestGutenbergProcess(GutenbergProcess):
            def __init__(self, process, custom_file, ingest_period):
                self.constants = {}
                self.ingest_period = None
                self.offset = 0
                self.limit = 5000
                self.db_manager = mocker.MagicMock()
                self.record_buffer = mocker.MagicMock()
                self.file_bucket = os.environ['FILE_BUCKET']
                self.file_queue = os.environ['FILE_QUEUE']
                self.file_route = os.environ['FILE_ROUTING_KEY']
                self.records = []
                self.rabbitmq_manager = mocker.MagicMock()
        
        return TestGutenbergProcess('TestProcess', 'testFile', 'testDate')

    @pytest.fixture
    def test_yaml_metadata(self):
        return {
            'covers': [
                {'cover_type': 'generated', 'image_path': 'images/cover.png'},
                {'cover_type': 'archival', 'image_path': 'images/cover.jpg'}
            ],
            'identifiers': {'gutenberg': '1'},
            'url': 'gutenberg.org/ebooks/1'
        }
    
    def test_runProcess_daily(self, test_instance: GutenbergProcess, mocker):
        mock_import = mocker.patch.object(GutenbergProcess, 'import_rdf_records')

        test_instance.process = 'daily'
        test_instance.runProcess()

        mock_import.assert_called_once
        test_instance.record_buffer.flush.assert_called_once()

    def test_runProcess_complete(self, test_instance: GutenbergProcess, mocker):
        mock_import = mocker.patch.object(GutenbergProcess, 'import_rdf_records')

        test_instance.process = 'complete'
        test_instance.runProcess()

        mock_import.assert_called_once_with()
        test_instance.record_buffer.flush.assert_called_once()

    def test_runProcess_custom(self, test_instance: GutenbergProcess, mocker):
        mock_import = mocker.patch.object(GutenbergProcess, 'import_rdf_records')

        test_instance.process = 'custom'
        test_instance.ingest_period = '2024-10-10T00:00:00'
        test_instance.runProcess()

        mock_import.assert_called_once_with(start_timestamp=datetime.strptime(test_instance.ingest_period, '%Y-%m-%dT%H:%M:%S'))
        test_instance.record_buffer.flush.assert_called_once()

    def test_import_rdf_records_partial(self, test_instance: GutenbergProcess, mocker):
        mock_process = mocker.patch.object(GutenbergProcess, 'process_gutenberg_files')
        mock_manager = mocker.MagicMock()
        mock_manager.fetchGithubRepoBatch.side_effect = [True, False]
        mock_manager.dataFiles = 'testDataFiles'
        mock_manager_init = mocker.patch('processes.ingest.gutenberg.GutenbergManager')
        mock_manager_init.return_value = mock_manager
        start_timestamp = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=1)
        
        test_instance.import_rdf_records(start_timestamp=start_timestamp)

        mock_manager_init.assert_called_once_with('DESC', 'PUSHED_AT', start_timestamp, 100)
        mock_process.assert_has_calls([mocker.call('testDataFiles'), mocker.call('testDataFiles')])
        assert mock_manager.fetchGithubRepoBatch.call_count == 2
        assert mock_manager.fetchMetadataFilesForBatch.call_count == 2
        assert mock_manager.resetBatch.call_count == 2

    def test_import_rdf_records_custom(self, test_instance: GutenbergProcess, mocker):
        mock_process = mocker.patch.object(GutenbergProcess, 'process_gutenberg_files')
        mock_manager = mocker.MagicMock()
        mock_manager.fetchGithubRepoBatch.side_effect = [True, False]
        mock_manager.dataFiles = 'testDataFiles'
        mock_manager_init = mocker.patch('processes.ingest.gutenberg.GutenbergManager')
        mock_manager_init.return_value = mock_manager

        test_instance.import_rdf_records(start_timestamp=datetime.strptime('1900-01-01T12:00:00',  '%Y-%m-%dT%H:%M:%S'))

        mock_manager_init.assert_called_once_with('DESC', 'PUSHED_AT', datetime(1900, 1, 1, 12, 0, 0), 100)
        mock_process.assert_has_calls([mocker.call('testDataFiles'), mocker.call('testDataFiles')])
        assert mock_manager.fetchGithubRepoBatch.call_count == 2
        assert mock_manager.fetchMetadataFilesForBatch.call_count == 2
        assert mock_manager.resetBatch.call_count == 2

    def test_import_rdf_records_complete(self, test_instance: GutenbergProcess, mocker):
        mock_process = mocker.patch.object(GutenbergProcess, 'process_gutenberg_files')
        mock_manager = mocker.MagicMock()
        mock_manager.fetchGithubRepoBatch.side_effect = [True, False]
        mock_manager.dataFiles = 'testDataFiles'
        mock_manager_init = mocker.patch('processes.ingest.gutenberg.GutenbergManager')
        mock_manager_init.return_value = mock_manager

        test_instance.import_rdf_records()

        mock_manager_init.assert_called_once_with('ASC', 'CREATED_AT', None, 100)
        mock_process.assert_has_calls([mocker.call('testDataFiles'), mocker.call('testDataFiles')])
        assert mock_manager.fetchGithubRepoBatch.call_count == 2
        assert mock_manager.fetchMetadataFilesForBatch.call_count == 2
        assert mock_manager.resetBatch.call_count == 2

    def test_process_gutenberg_files(self, test_instance: GutenbergProcess, mocker):
        mock_gutenberg_record = mocker.MagicMock(name='mock_record_mapping', record=mocker.MagicMock(source_id=1))
        mock_gutenberg_mapping_init = mocker.patch('processes.ingest.gutenberg.GutenbergMapping')
        mock_gutenberg_mapping_init.return_value = mock_gutenberg_record

        process_mocks = mocker.patch.multiple(
            GutenbergProcess,
            store_epubs=mocker.DEFAULT,
            add_cover=mocker.DEFAULT,
        )

        process_mocks['add_cover'].side_effect = [None, KeyError]

        test_instance.process_gutenberg_files([('rdf1', 'yaml1'), ('rdf2', 'yaml2')])

        mock_gutenberg_mapping_init.assert_has_calls([
            mocker.call('rdf1', GutenbergProcess.GUTENBERG_NAMESPACES, {}),
            mocker.call('rdf2', GutenbergProcess.GUTENBERG_NAMESPACES, {})
        ])
        assert mock_gutenberg_record.applyMapping.call_count == 2
        process_mocks['store_epubs'].assert_has_calls([
            mocker.call(mock_gutenberg_record), mocker.call(mock_gutenberg_record)
        ])
        process_mocks['add_cover'].assert_has_calls([
            mocker.call(mock_gutenberg_record, 'yaml1'), mocker.call(mock_gutenberg_record, 'yaml2')
        ])
        test_instance.record_buffer.add.assert_has_calls([
            mocker.call(mock_gutenberg_record.record), mocker.call(mock_gutenberg_record.record)
        ])

    def test_store_epubs(self, test_instance: GutenbergProcess, mocker):
        mock_record_mapping = mocker.MagicMock()
        mock_record_mapping.record.get_parts.return_value = [
            Part(index=1, url='gutenberg.org/ebook/1.epub.images', source=Source.GUTENBERG.value, file_type='application/epub+zip', flags=json.dumps(dataclasses.asdict(FileFlags(download=True)))),
            Part(index=1, url='gutenberg.org/ebook/1.epub.images', source=Source.GUTENBERG.value, file_type='application/epub', flags=json.dumps(dataclasses.asdict(FileFlags(download=False)))),
            Part(index=2, url='gutenberg.org/ebook/2.epub.noimages', source=Source.GUTENBERG.value, file_type='application/epub+zip', flags=json.dumps(dataclasses.asdict(FileFlags(download=True)))),
        ]

        test_instance.store_epubs(mock_record_mapping)

        test_instance.rabbitmq_manager.sendMessageToQueue.assert_has_calls([
            mocker.call(
                test_instance.file_queue,
                test_instance.file_route,
                get_file_message('gutenberg.org/ebook/1.epub.images', 'epubs/gutenberg/1_images.epub')
            ),
            mocker.call(
                test_instance.file_queue,
                test_instance.file_route,
                get_file_message('gutenberg.org/ebook/2.epub.noimages', 'epubs/gutenberg/2_noimages.epub')
            ),
        ])

    def test_add_cover(self, test_instance: GutenbergProcess, test_yaml_metadata, mocker):
        mock_record_mapping = mocker.MagicMock()
        mock_record_mapping.record.has_part = []

        test_instance.add_cover(mock_record_mapping, test_yaml_metadata)

        test_instance.rabbitmq_manager.sendMessageToQueue.assert_called_once_with(
            test_instance.file_queue,
            test_instance.file_route,
            get_file_message('gutenberg.org/files/1/images/cover.jpg', 'covers/gutenberg/1.jpg')
        )
        assert mock_record_mapping.record.has_part == [Part(
            index=None,
            url='https://test_aws_bucket.s3.amazonaws.com/covers/gutenberg/1.jpg',
            file_type='image/jpeg',
            source=Source.GUTENBERG.value,
            flags=json.dumps(dataclasses.asdict(FileFlags(cover=True)))
        ).to_string()]

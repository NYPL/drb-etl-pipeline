from datetime import datetime
import os
import newrelic.agent
import re
from typing import Optional

from managers import DBManager, OCLCCatalogManager, RabbitMQManager, RedisManager
from mappings.oclc_bib import OCLCBibMapping
from model import Record
from logger import create_log
from ..record_buffer import RecordBuffer
from .. import utils


logger = create_log(__name__)


class ClassifyProcess():
    def __init__(self, *args):
        self.process = args[0]
        self.ingest_period = args[2]
        self.single_record = args[3]

        self.limit = int(args[4]) if len(args) >= 5 and args[4] else None
        self.source = args[6] if len(args) >= 7 and args[6] else None

        self.db_manager = DBManager()
        self.db_manager.createSession()

        self.record_buffer = RecordBuffer(db_manager=self.db_manager)

        self.redis_manager = RedisManager()
        self.redis_manager.createRedisClient()

        self.catalog_queue = os.environ['OCLC_QUEUE']
        self.catalog_route = os.environ['OCLC_ROUTING_KEY']

        self.rabbitmq_manager = RabbitMQManager()
        self.rabbitmq_manager.createRabbitConnection()
        self.rabbitmq_manager.createOrConnectQueue(self.catalog_queue, self.catalog_route)

        self.oclc_catalog_manager = OCLCCatalogManager()

    def runProcess(self):
        try:
            start_datetime = utils.get_start_datetime(process_type=self.process, ingest_period=self.ingest_period)
            
            self.classify_records(
                start_datetime=start_datetime,
                record_uuid=self.single_record,
                source=self.source, 
            )
            
            self.record_buffer.flush()
            
            logger.info(f'Classified {self.record_buffer.ingest_count} records')
        except Exception as e:
            logger.exception(f'Failed to run classify process')
            raise e

    def classify_records(self, start_datetime: Optional[datetime]=None, record_uuid: Optional[str]=None, source: Optional[str]=None):
        get_unfrbrized_records_query = (
            self.session.query(Record)
                .filter(Record.source != 'oclcClassify' and Record.source != 'oclcCatalog')
                .filter(Record.frbr_status == 'to_do')
        )

        if start_datetime:
            get_unfrbrized_records_query = get_unfrbrized_records_query.filter(Record.date_modified > start_datetime)

        if record_uuid:
            get_unfrbrized_records_query = get_unfrbrized_records_query.filter(Record.uuid == record_uuid)

        if source:
            get_unfrbrized_records_query = get_unfrbrized_records_query.filter(Record.source == self.source)

        while unfrbrized_record := get_unfrbrized_records_query.first():
            self.frbrize_record(unfrbrized_record)

            unfrbrized_record.cluster_status = False
            unfrbrized_record.frbr_status = 'complete'

            self.session.add(unfrbrized_record)
            self.session.commit()

            if self.limit and self.classified_count >= self.limit:
                break

            if self.redis_manager.checkIncrementerRedis('oclcCatalog', 'API'):
                logger.warning('Exceeded max requests to OCLC catalog')
                break

    def frbrize_record(self, record: Record):
        queryable_ids = self._get_queryable_identifiers(record.identifiers)

        if len(queryable_ids) < 1:
            queryable_ids = [None]

        for id in queryable_ids:
            try:
                identifier, identifier_type = tuple(id.split('|'))
            except Exception:
                identifier, identifier_type = (None, None)

            try:
                author, *_ = tuple(record.authors[0].split('|'))
            except Exception:
                author = None

            if identifier and self.redis_manager.checkSetRedis('classify', identifier, identifier_type):
                continue

            try:
                self.classify_record_by_metadata(identifier, identifier_type, author, record.title)
            except Exception:
                logger.exception(f'Failed to classify record: {record}')

    def classify_record_by_metadata(self, identifier, identifier_type, author, title):
        search_query = self.oclc_catalog_manager.generate_search_query(identifier, identifier_type, title, author)

        related_oclc_bibs = self.oclc_catalog_manager.query_bibs(search_query)

        for related_oclc_bib in related_oclc_bibs:
            oclc_number = related_oclc_bib.get('identifier', {}).get('oclcNumber')
            owi_number = related_oclc_bib.get('work', {}).get('id')

            if not oclc_number or not owi_number:
                logger.warning(f'Unable to get identifiers for bib: {related_oclc_bib}')
                continue

            if self.check_if_classify_work_fetched(owi_number=owi_number):
                continue

            related_oclc_numbers = self.oclc_catalog_manager.get_related_oclc_numbers(oclc_number=oclc_number)

            oclc_record = OCLCBibMapping(
                oclc_bib=related_oclc_bib,
                related_oclc_numbers=list(set(related_oclc_numbers))
            )

            self.record_buffer.add(oclc_record)
            self.get_oclc_catalog_records(oclc_record.record.identifiers)

    def get_oclc_catalog_records(self, identifiers):
        owi_number, _ = tuple(identifiers[0].split('|'))
        catalogued_record_count = 0
        oclc_numbers = set()
        
        for oclc_number in list(filter(lambda x: 'oclc' in x, identifiers)):
            oclc_number, _ = tuple(oclc_number.split('|'))
            oclc_numbers.add(oclc_number)

        oclc_numbers = list(oclc_numbers)

        cached_oclc_numbers = self.redis_manager.multiCheckSetRedis('catalog', oclc_numbers, 'oclc')

        for oclc_number, uncached in cached_oclc_numbers:
            if not uncached:
                logger.debug(f'Skipping catalog lookup process for OCLC number {oclc_number}')
                continue

            self.rabbitmq_manager.sendMessageToQueue(self.catalog_queue, self.catalog_route, { 'oclcNo': oclc_number, 'owiNo': owi_number })
            catalogued_record_count += 1

        if catalogued_record_count > 0:
            self.redis_manager.setIncrementerRedis('oclcCatalog', 'API', amount=catalogued_record_count)

    def check_if_classify_work_fetched(self, owi_number: int) -> bool:
        return self.redis_manager.checkSetRedis('classifyWork', owi_number, 'owi')

    def _get_queryable_identifiers(self, identifiers):
        return list(filter(
            lambda id: re.search(r'\|(?:isbn|issn|oclc)$', id) != None,
            identifiers
        ))

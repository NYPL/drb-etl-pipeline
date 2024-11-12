from datetime import datetime, timedelta, timezone
import os
import newrelic.agent
import re

from ..core import CoreProcess
from managers import OCLCCatalogManager, RabbitMQManager
from mappings.oclc_bib import OCLCBibMapping
from model import Record
from logger import createLog


logger = createLog(__name__)


class ClassifyProcess(CoreProcess):
    WINDOW_SIZE = 100

    def __init__(self, *args):
        super(ClassifyProcess, self).__init__(*args[:4], batchSize=50)

        self.ingestLimit = int(args[4]) if len(args) >= 5 and args[4] else None

        self.generateEngine()
        self.createSession()

        self.createRedisClient()

        self.catalog_queue = os.environ['OCLC_QUEUE']
        self.catalog_route = os.environ['OCLC_ROUTING_KEY']

        self.rabbitmq_manager = RabbitMQManager()
        self.rabbitmq_manager.createRabbitConnection()
        self.rabbitmq_manager.createOrConnectQueue(self.catalog_queue, self.catalog_route)

        self.classified_count = 0

        self.oclc_catalog_manager = OCLCCatalogManager()

    def runProcess(self):
        try:
            if self.process == 'daily':
                self.classify_records()
            elif self.process == 'complete':
                self.classify_records(full=True)
            elif self.process == 'custom':
                self.classify_records(start_date_time=self.ingestPeriod)
            else:
                logger.warning(f'Unknown classify process type: {self.process}')
                return

            self.saveRecords()
            self.commitChanges()
            
            logger.info(f'Classified {self.classified_count} records and saved {len(self.records)} classify records')
        except Exception as e:
            logger.exception(f'Failed to run classify process')
            raise e

    def classify_records(self, full=False, start_date_time=None):
        get_unfrbrized_records_query = (
            self.session.query(Record)
                .filter(Record.source != 'oclcClassify' and Record.source != 'oclcCatalog')
                .filter(Record.frbr_status == 'to_do')
        )

        if not full:
            if not start_date_time:
                start_date_time = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=24)
            
            get_unfrbrized_records_query = get_unfrbrized_records_query.filter(Record.date_modified > start_date_time)

        window_size = min(self.ingestLimit or self.WINDOW_SIZE, self.WINDOW_SIZE)
        frbrized_records = []

        for record in self.windowedQuery(Record, get_unfrbrized_records_query, windowSize=window_size):
            self.frbrize_record(record)

            record.cluster_status = False
            record.frbr_status = 'complete'
            frbrized_records.append(record)

            if self.checkIncrementerRedis('oclcCatalog', 'API'):
                logger.warning('Exceeded max requests to OCLC catalog')
                break

            if len(frbrized_records) >= window_size:
                self.classified_count += len(frbrized_records)
                self.bulkSaveObjects(frbrized_records)
                
                frbrized_records = []

        if len(frbrized_records):
            self.classified_count += len(frbrized_records)
            self.bulkSaveObjects(frbrized_records)

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

            if identifier and self.checkSetRedis('classify', identifier, identifier_type):
                continue

            try:
                self.classify_record_by_metadata(identifier, identifier_type, author, record.title)
            except Exception:
                logger.exception(f'Failed to classify record: {record}')

    def classify_record_by_metadata(self, identifier, identifier_type, author, title):
        search_query = self.oclc_catalog_manager.generate_search_query(identifier, identifier_type, title, author)

        related_oclc_bibs = self.oclc_catalog_manager.query_bibs(search_query)

        if not len(related_oclc_bibs):
            logger.warning(f'No OCLC bibs returned for query {search_query}')

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
                related_oclc_numbers=related_oclc_numbers
            )

            self.addDCDWToUpdateList(oclc_record)
            self.get_oclc_catalog_records(oclc_record.record.identifiers)

    def get_oclc_catalog_records(self, identifiers):
        owi_number, _ = tuple(identifiers[0].split('|'))
        catalogued_record_count = 0
        oclc_numbers = set()
        
        for oclc_number in list(filter(lambda x: 'oclc' in x, identifiers)):
            oclc_number, _ = tuple(oclc_number.split('|'))
            oclc_numbers.add(oclc_number)

        oclc_numbers = list(oclc_numbers)

        cached_oclc_numbers = self.multiCheckSetRedis('catalog', oclc_numbers, 'oclc')

        for oclc_number, uncached in cached_oclc_numbers:
            if not uncached:
                logger.debug(f'Skipping catalog lookup process for OCLC number {oclc_number}')
                continue

            self.rabbitmq_manager.sendMessageToQueue(self.catalog_queue, self.catalog_route, { 'oclcNo': oclc_number, 'owiNo': owi_number })
            catalogued_record_count += 1

        if catalogued_record_count > 0:
            self.setIncrementerRedis('oclcCatalog', 'API', amount=catalogued_record_count)

    def check_if_classify_work_fetched(self, owi_number: int) -> bool:
        return self.checkSetRedis('classifyWork', owi_number, 'owi')

    def _get_queryable_identifiers(self, identifiers):
        return list(filter(
            lambda id: re.search(r'\|(?:isbn|issn|oclc)$', id) != None,
            identifiers
        ))

import re
from typing import Optional
from sqlalchemy.exc import DataError
from logger import create_log
from managers import DBManager, ElasticsearchManager, KMeansManager, SFRElasticRecordManager, SFRRecordManager
from constants.get_constants import get_constants
from model import Record, Work


logger = create_log(__name__)


class RecordClusterer:
    MAX_MATCH_DISTANCE = 4
    CLUSTER_SIZE_LIMIT = 10000
    IDENTIFIERS_TO_MATCH = r'\|(?:isbn|issn|oclc|lccn|owi)$'

    def __init__(self, db_manager: DBManager):
        self.db_manager = db_manager

        self.elastic_search_manager = ElasticsearchManager()

        self.elastic_search_manager.createElasticConnection()
        self.elastic_search_manager.createElasticSearchIngestPipeline()
        self.elastic_search_manager.createElasticSearchIndex()

        self.constants = get_constants()

    def cluster_record(self, record) -> list[Record]:
        try:
            work, stale_work_ids, records = self._get_clustered_work_and_records(record)
            self._update_elastic_search(works_to_index=[work], works_to_delete=stale_work_ids)
            self._delete_stale_works(stale_work_ids)
            logger.info(f'Clustered record: {record}')

            return records
        except Exception as e:
            logger.exception(f'Failed to cluster record {record}')
            raise e

    def _get_clustered_work_and_records(self, record: Record):
        matched_record_ids = self._find_all_matching_records(record) + [record.id]

        clustered_editions, records = self._cluster_matched_records(matched_record_ids)
        work, stale_work_ids = self._create_work_from_editions(clustered_editions, records)

        try:
            self.db_manager.session.flush()
        except Exception:
            self.db_manager.session.rollback()
            logger.exception(f'Unable to cluster record {record}')

        self._update_cluster_status(matched_record_ids)

        return work, stale_work_ids, records

    def _update_elastic_search(self, works_to_index: list, works_to_delete: set):
        self.elastic_search_manager.deleteWorkRecords(works_to_delete)
        self._index_works_in_elastic_search(works_to_index)

    def _delete_stale_works(self, work_ids: set[str]):
        self.db_manager.deleteRecordsByQuery(self.db_manager.session.query(Work).filter(Work.id.in_(list(work_ids))))

    def _cluster_matched_records(self, record_ids: list[str]):
        records = self.db_manager.session.query(Record).filter(Record.id.in_(record_ids)).all()

        kmean_manager = KMeansManager(records)

        kmean_manager.createDF()
        kmean_manager.generateClusters()
        editions = kmean_manager.parseEditions()

        return editions, records

    def _update_cluster_status(self, record_ids: list[str], cluster_status: bool = True):
        (
            self.db_manager.session.query(Record)
                .filter(Record.id.in_(list(set(record_ids))))
                .update(
                    {
                        'cluster_status': cluster_status,
                        'frbr_status': 'complete'
                    }
            )
        )

    def _find_all_matching_records(self, record: Record):
        tokenized_record_title = self._tokenize_title(record.title)
        ids_to_check = list(filter(lambda id: re.search(self.IDENTIFIERS_TO_MATCH, id), record.identifiers))

        matched_record_ids = set()
        checked_ids = set()

        for match_distance in range(0, self.MAX_MATCH_DISTANCE):
            matched_records = self._get_matched_records(list(ids_to_check), matched_record_ids.copy())

            if not matched_records:
                break

            checked_ids.update(ids_to_check)
            ids_to_check.clear()

            for matched_record_title, matched_record_id, matched_record_identifiers in matched_records:
                if not matched_record_title:
                    logger.warning('Invalid title found in matched records')
                    continue

                tokenized_matched_record_title = self._tokenize_title(matched_record_title)

                if match_distance > 0 and not self._titles_overlap(tokenized_record_title, tokenized_matched_record_title):
                    continue

                ids_to_check.update({id for id in matched_record_identifiers 
                                     if re.search(self.IDENTIFIERS_TO_MATCH, id) and id not in checked_ids})
                matched_record_ids.add(matched_record_id)

        if len(matched_record_ids) > self.CLUSTER_SIZE_LIMIT:
            raise Exception(f'Records matched is greater than {self.CLUSTER_SIZE_LIMIT}')

        return list(matched_record_ids)

    def _get_matched_records(self, identifiers: list[str], already_matched_record_ids: list[str]):
        batch_size = 100
        matched_records = []

        for i in range(0, len(identifiers), batch_size):
            id_batch = self._format_identifiers(identifiers[i:i+batch_size])

            try:
                records = (
                    self.db_manager.session.query(
                        Record.title, Record.id, Record.identifiers)
                    .filter(~Record.id.in_(already_matched_record_ids))
                    .filter(Record.identifiers.overlap(id_batch))
                    .filter(Record.title.isnot(None))
                    .all()
                )

                matched_records.extend(records)
            except DataError:
                logger.exception('Unable to get matching records')

        return matched_records

    def _create_work_from_editions(self, editions: list, records: list[Record]):
        record_manager = SFRRecordManager(self.db_manager.session, self.constants['iso639'])

        work_data = record_manager.buildWork(records, editions)

        record_manager.saveWork(work_data)

        stale_work_ids = record_manager.mergeRecords()

        return record_manager.work, stale_work_ids

    def _index_works_in_elastic_search(self, works: Work):
        work_documents = []

        for work in works:
            elastic_manager = SFRElasticRecordManager(work)
            elastic_manager.getCreateWork()
            work_documents.append(elastic_manager.work)

        self.elastic_search_manager.saveWorkRecords(work_documents)

    def _titles_overlap(self, tokenized_record_title: set, tokenized_matched_record_title: set):
        if len(tokenized_record_title) == 1 and not tokenized_record_title <= tokenized_matched_record_title:
            return False
        elif len(tokenized_matched_record_title) == 1 and not tokenized_record_title >= tokenized_matched_record_title:
            return False
        elif (len(tokenized_record_title) > 1 and len(tokenized_matched_record_title) > 1) and len(tokenized_record_title & tokenized_matched_record_title) < 2:
            return False

        return True

    def _tokenize_title(self, title: str):
        title_tokens = re.findall(r'(\w+)', title.lower())

        return set(title_tokens) - set(['a', 'an', 'the', 'of'])

    def _format_identifiers(self, identifiers: list[str]):
        formatted_ids = []

        for id in identifiers:
            formatted_id = f'"{id}"' if re.search(r'[{},]{1}', id) else id
            formatted_ids.append(formatted_id)

        return '{{{}}}'.format(','.join(formatted_ids))

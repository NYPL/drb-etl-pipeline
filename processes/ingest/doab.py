from datetime import datetime, timedelta, timezone

from services import DSpaceService
from ..core import CoreProcess
from logger import create_log
from mappings.doab import DOABMapping
from managers import DOABLinkManager
from model import get_file_message


logger = create_log(__name__)


class DOABProcess(CoreProcess):
    DOAB_BASE_URL = 'https://directory.doabooks.org/oai/request?'
    ROOT_NAMESPACE = {None: 'http://www.openarchives.org/OAI/2.0/'}
    DOAB_IDENTIFIER = "oai:directory.doabooks.org"

    OAI_NAMESPACES = {
        'oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
        'dc': 'http://purl.org/dc/elements/1.1/',
        'datacite': 'https://schema.datacite.org/meta/kernel-4.1/metadata.xsd',
        'oapen': 'http://purl.org/dc/elements/1.1/',
        'oaire': 'https://raw.githubusercontent.com/rcic/openaire4/master/schemas/4.0/oaire.xsd'
    }

    def __init__(self, *args):
        super(DOABProcess, self).__init__(*args[:4])

        self.offset = int(args[5]) if args[5] else 0
        self.limit = (int(args[4]) + self.offset) if args[4] else 10000

        self.dSpace_service = DSpaceService(
            base_url=self.DOAB_BASE_URL, SourceMapping=DOABMapping)

    def runProcess(self):
        try:
            self.generateEngine()
            self.createSession()

            records = []

            if self.process == 'daily':
                records = self.dSpace_service.get_records(offset=self.offset, limit=self.limit)
            elif self.process == 'complete':
                records = self.dSpace_service.get_records(full_or_partial=True, offset=self.offset, limit=self.limit)
            elif self.process == 'custom':
                records = self.dSpace_service.get_records(start_timestamp=self.ingestPeriod, offset=self.offset, limit=self.limit)
            elif self.singleRecord:
                record = self.dSpace_service.get_single_record(record_id=self.singleRecord, source_identifier=self.DOAB_IDENTIFIER)
                self.manage_links(record)

            if records:
                for record in records:
                    self.manage_links(record)

            self.saveRecords()
            self.commitChanges()

            logger.info(f'Ingested {len(self.records) if records else 1} DOAB records')

        except Exception as e:
            logger.exception('Failed to run DOAB process')
            raise e
        finally:
            self.close_connection

    def manage_links(self, record):
        linkManager = DOABLinkManager(record.record)

        linkManager.parseLinks()

        for manifest in linkManager.manifests:
            manifestPath, manifestJSON = manifest
            self.dSpace_service.s3_manager.createManifestInS3(
                manifestPath, manifestJSON, self.dSpace_service.s3_bucket)

        for epubLink in linkManager.ePubLinks:
            ePubPath, ePubURI = epubLink
            self.dSpace_service.rabbitmq_manager.sendMessageToQueue(
                self.dSpace_service.file_queue, self.dSpace_service.file_route, get_file_message(ePubURI, ePubPath))

        self.addDCDWToUpdateList(record)

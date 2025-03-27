from services import DSpaceService

from logger import create_log
from model import Source
from mappings.clacso import CLACSOMapping
from ..record_ingestor import RecordIngestor
from .. import utils

logger = create_log(__name__)

class CLACSOProcess():
    CLACSO_BASE_URL = 'https://biblioteca-repositorio.clacso.edu.ar/oai/request?'

    def __init__(self, *args):
        self.dspace_service = DSpaceService(base_url=self.CLACSO_BASE_URL, source_mapping=CLACSOMapping)
        self.params = utils.parse_process_args(*args)
        self.record_ingestor = RecordIngestor(source_service=self.dspace_service, source=Source.CLACSO.value)

    def runProcess(self):    
        return self.record_ingestor.ingest(params=self.params)

from model import Source
from services import ChicagoISACService
from ..record_ingestor import RecordIngestor
from .. import utils


class ChicagoISACProcess():

    def __init__(self, *args):
        self.chicago_isac_service = ChicagoISACService()
        self.params = utils.parse_process_args(*args)
        self.record_ingestor = RecordIngestor(source_service=self.chicago_isac_service, source=Source.CHICACO_ISAC.value)

    def runProcess(self):    
        return self.record_ingestor.ingest(params=self.params)

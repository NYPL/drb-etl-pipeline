from model import Source
from services import ChicagoISACService
from ..record_ingestor import RecordIngestor
from .. import utils


class ChicagoISACProcess(RecordIngestor):

    def __init__(self, *args):
        self.chicago_isac_service = ChicagoISACService()
        super().__init__(self.chicago_isac_service, Source.CHICACO_ISAC.value)

        self.params = utils.parse_process_args(*args)

    def runProcess(self):    
        return self.ingest(params=self.params)

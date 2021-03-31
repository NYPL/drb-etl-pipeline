from .core import CoreProcess
from api.app import FlaskAPI
from logger import createLog

logger = createLog(__name__)


class APIProcess(CoreProcess):
    def __init__(self, *args):
        super(APIProcess, self).__init__(*args[:4])

        self.createElasticConnection()
        self.generateEngine()
        self.api = FlaskAPI(self.client, self.engine)

    def runProcess(self):
        logger.info('Starting API...')

        self.api.createErrorResponses()

        self.api.run()

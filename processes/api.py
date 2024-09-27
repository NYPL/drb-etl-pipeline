from .core import CoreProcess
from api.app import FlaskAPI
from logging import logger


class APIProcess(CoreProcess):
    def __init__(self, *args):
        super(APIProcess, self).__init__(*args[:4])

        # ElasticSearch Connection
        self.createElasticConnection()

        # Generate PostgreSQL engine
        self.generateEngine()

        # Redis Connection
        self.createRedisClient()

        self.api = FlaskAPI(self.engine, self.redisClient)

    def runProcess(self):
        logger.info('Starting API...')

        self.api.createErrorResponses()

        self.api.run()

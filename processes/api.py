from api.app import FlaskAPI
from logger import create_logger
from managers import DBManager, ElasticsearchManager, RedisManager

logger = create_logger(__name__)


class APIProcess():
    def __init__(self, *args):
        self.db_manager = DBManager()
        self.elastic_search_manager = ElasticsearchManager()
        self.redis_manager = RedisManager()

    def runProcess(self):
        try:
            logger.info('Starting API...')

            db_engine = self.db_manager.generateEngine()
            redis_client = self.redis_manager.createRedisClient()
            self.elastic_search_manager.createElasticConnection()
            
            api = FlaskAPI(db_engine, redis_client)

            api.createErrorResponses()
            api.run()
        except Exception as e:
            logger.exception('Failed to start API')
            raise e

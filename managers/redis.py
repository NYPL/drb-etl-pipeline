from datetime import datetime, timedelta
import os
from redis import Redis

from logger import createLog

logger = createLog(__name__)


class RedisManager:
    def __init__(self, host=None, port=None):
        super(RedisManager, self).__init__()
        self.redisHost = host or os.environ.get('REDIS_HOST', None)
        self.redisPort = port or os.environ.get('REDIS_PORT', None)
        self.environment = os.environ.get('ENVIRONMENT', 'test')

        self.presentTime = datetime.utcnow()
        self.oneDayAgo = self.presentTime - timedelta(days=1)
    
    def createRedisClient(self):
        self.redisClient = Redis(
            host=self.redisHost,
            port=self.redisPort,
            socket_timeout=5
        )
    
    def checkSetRedis(self, service, identifier, idenType):
        queryTime = self.redisClient.get('{}/{}/{}/{}'.format(self.environment, service, identifier, idenType))

        if queryTime is not None and datetime.strptime(queryTime.decode('utf-8'), '%Y-%m-%dT%H:%M:%S') >= self.oneDayAgo:
            logger.debug('Identifier {} recently queried'.format(identifier))    
            return True
        
        self.setRedis(service, identifier, idenType)
        return False
        
    
    def setRedis(self, service, identifier, idenType, expirationTime=60*60*24*7):
        self.redisClient.set(
            '{}/{}/{}/{}'.format(self.environment, service, identifier, idenType),
            self.presentTime.strftime('%Y-%m-%dT%H:%M:%S'),
            ex=expirationTime
        )

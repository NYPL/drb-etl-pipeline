from datetime import datetime, timedelta
import os
from redis import Redis


class RedisManager:
    def __init__(self, host=None, port=None):
        super(RedisManager, self).__init__()
        self.redisHost = host or os.environ['REDIS_HOST']
        self.redisPort = port or os.environ['REDIS_PORT']
        self.environment = os.environ['ENVIRONMENT']
    
    def createRedisClient(self):
        self.redisClient = Redis(
            host=self.redisHost,
            port=self.redisPort,
            socket_timeout=5
        )
    
    def checkSetRedis(self, service, identifier, idenType):
        queryTime = self.redisClient.get('{}/{}/{}'.format(service, identifier, idenType))

        presentTime = datetime.utcnow()
        oneDayAgo = presentTime - timedelta(days=1)

        if queryTime is not None and datetime.strptime(queryTime.decode('utf-8'), '%Y-%m-%dT%H:%M:%S') >= oneDayAgo:
            print('Identifier Recently queried')
            return True
        
        self.setRedis(service, identifier, idenType, presentTime)
        return False
        
    
    def setRedis(self, service, identifier, idenType, presentTime, expirationTime=60*60*24*7):
        self.redisClient.set(
            '{}/{}/{}/{}'.format(self.environment, service, identifier, idenType),
            presentTime.strftime('%Y-%m-%dT%H:%M:%S'),
            ex=expirationTime
        )

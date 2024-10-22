from datetime import datetime, timedelta, timezone
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

        self.presentTime = datetime.now(timezone.utc).replace(tzinfo=None)
        self.oneDayAgo = self.presentTime - timedelta(days=1)

        self.oclcLimit = int(os.environ.get('OCLC_QUERY_LIMIT', 400000))
    
    def createRedisClient(self):
        self.redisClient = Redis(
            host=self.redisHost,
            port=self.redisPort,
            socket_timeout=5
        )

        return self.redisClient

    def clear_cache(self):
        self.redisClient.flushall()
    
    def checkSetRedis(self, service, identifier, idenType, expirationTime=60*60*24*7):
        queryTime = self.redisClient.get('{}/{}/{}/{}'.format(self.environment, service, identifier, idenType))

        if queryTime is not None and datetime.strptime(queryTime.decode('utf-8'), '%Y-%m-%dT%H:%M:%S') >= self.oneDayAgo:
            logger.debug('Identifier {} recently queried'.format(identifier))    
            return True
        
        self.setRedis(service, identifier, idenType, expirationTime=expirationTime)
        return False
        
    def multiCheckSetRedis(self, service, identifiers, idenType, expirationTime=60*60*24*7):
        checkArr = [
            '{}/{}/{}/{}'.format(self.environment, service, identifier, idenType)
            for identifier in identifiers
        ]

        idenQueryTimes = self.redisClient.mget(checkArr)

        outputArr = []
        for i, queryTime in enumerate(idenQueryTimes):
            updateReq = True
            if queryTime is not None and datetime.strptime(queryTime.decode('utf-8'), '%Y-%m-%dT%H:%M:%S') >= self.oneDayAgo:
                logger.debug('Identifier {} recently queried'.format(identifiers[i]))
                updateReq = False

            outputArr.append((identifiers[i], updateReq))
        
        setArr = [key[0] for key in outputArr if key[1] is True]
        self.multiSetRedis(service, setArr, idenType, expirationTime=expirationTime)

        return outputArr

    def setRedis(self, service, identifier, idenType, expirationTime=60*60*24*7):
        self.redisClient.set(
            '{}/{}/{}/{}'.format(self.environment, service, identifier, idenType),
            self.presentTime.strftime('%Y-%m-%dT%H:%M:%S'),
            ex=expirationTime
        )

    def multiSetRedis(self, service, identifiers, idenType, expirationTime=60*60*24*7):
        pipe = self.redisClient.pipeline()

        for identifier in identifiers:
            pipe.set(
                '{}/{}/{}/{}'.format(self.environment, service, identifier, idenType),
                self.presentTime.strftime('%Y-%m-%dT%H:%M:%S'),
                ex=expirationTime
            )

        pipe.execute()

    def checkIncrementerRedis(self, service, identifier):
        incrementValue = self.redisClient.get('{}/{}/{}'.format(
            service, self.presentTime.strftime('%Y-%m-%d'), identifier
        ))

        return bool(incrementValue) and (int(incrementValue) >= self.oclcLimit)

    def setIncrementerRedis(self, service, identifier, amount=1):
        redisKey = '{}/{}/{}'.format(
            service, self.presentTime.strftime('%Y-%m-%d'), identifier
        )

        self.redisClient.incr(redisKey, amount=amount)

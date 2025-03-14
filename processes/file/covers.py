from datetime import datetime, timedelta, timezone
import os

from ..core import CoreProcess
from managers import CoverManager, RedisManager, S3Manager
from model import Edition, Link
from model.postgres.edition import EDITION_LINKS
from logger import create_log

logger = create_log(__name__)


class CoverProcess(CoreProcess):
    def __init__(self, *args):
        super(CoverProcess, self).__init__(*args[:4], batchSize=25)

        self.generateEngine()
        self.createSession()

        self.redis_manager = RedisManager()
        self.redis_manager.createRedisClient()

        self.s3_manager = S3Manager()
        self.s3_manager.createS3Client()
        self.fileBucket = os.environ['FILE_BUCKET']

        self.ingestLimit = None
        self.runTime = datetime.now(timezone.utc).replace(tzinfo=None)

    def runProcess(self):
        coverQuery = self.generateQuery()

        self.fetchEditionCovers(coverQuery)

        self.saveRecords()
        self.commitChanges()

    def generateQuery(self):
        baseQuery = self.session.query(Edition)

        subQuery = self.session.query(EDITION_LINKS.c.edition_id)\
            .join(Link)\
            .distinct('edition_id')\
            .filter(Link.flags['cover'] == 'true')

        filters = [~Edition.id.in_(subQuery)]

        if self.process != 'complete':
            if self.ingestPeriod:
                startDate = datetime.strptime(self.ingestPeriod, '%Y-%m-%d')
            else:
                startDate = self.runTime - timedelta(hours=24)

            filters.append(Edition.date_modified >= startDate)

        return baseQuery.filter(*filters)

    def fetchEditionCovers(self, coverQuery):
        for edition in self.windowedQuery(Edition, coverQuery, windowSize=self.batchSize):
            coverManager = self.searchForCover(edition)

            if coverManager: self.storeFoundCover(coverManager, edition)

            if (self.runTime + timedelta(hours=12)) < datetime.now(timezone.utc).replace(tzinfo=None): break

    def searchForCover(self, edition):
        identifiers = [i for i in self.getEditionIdentifiers(edition)]
        manager = CoverManager(identifiers, self.session)

        if manager.fetchCover() is True:
            manager.fetchCoverFile()
            manager.resizeCoverFile()

            return manager if manager.coverContent else None

    def getEditionIdentifiers(self, edition):
        for iden in edition.identifiers:
            if self.redis_manager.checkSetRedis('sfrCovers', iden.identifier, iden.authority, expirationTime=60*60*24*30):
                logger.debug('{} recently queried. Skipping'.format(iden))
                continue

            yield (iden.identifier, iden.authority)

    def storeFoundCover(self, manager, edition):
        coverPath = 'covers/{}/{}.{}'.format(
            manager.fetcher.SOURCE,
            manager.fetcher.coverID,
            manager.coverFormat.lower()
        )

        self.s3_manager.putObjectInBucket(manager.coverContent, coverPath, self.fileBucket)

        coverLink = Link(
            url='https://{}.s3.amazonaws.com/{}'.format(self.fileBucket, coverPath),
            media_type='image/{}'.format(manager.coverFormat.lower()),
            flags={'cover': True}
        )

        edition.links.append(coverLink)
        self.records.add(edition)

        if len(self.records) >= self.batchSize:
            self.bulkSaveObjects(self.records)
            self.records = set()

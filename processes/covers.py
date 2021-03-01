from datetime import datetime, timedelta
import os


from .core import CoreProcess
from managers import CoverManager
from model import Edition, Link
from model.postgres.edition import EDITION_LINKS


class CoverProcess(CoreProcess):
    def __init__(self, *args):
        super(CoverProcess, self).__init__(*args[:4], batchSize=25)

        self.generateEngine()
        self.createSession()

        self.createS3Client()
        self.fileBucket = os.environ['FILE_BUCKET']

        self.ingestLimit = None

    def runProcess(self):
        coverQuery = self.generateQuery()

        self.fetchEditionCovers(coverQuery)

        self.saveRecords()
        self.commitChanges()

    def generateQuery(self):
        baseQuery = self.session.query(Edition)

        subQuery = self.session.query('edition_id')\
            .select_from(EDITION_LINKS)\
            .join(Link)\
            .distinct('edition_id')\
            .filter(Link.flags['cover'] == 'true')

        filters = [~Edition.id.in_(subQuery)]

        if self.process != 'complete':
            if self.ingestPeriod:
                startDate = datetime.strptime(self.ingestPeriod, '%Y-%m-%d')
            else:
                startDate = datetime.utcnow() - timedelta(hours=24)

            filters.append(Edition.date_modified >= startDate)

        return baseQuery.filter(*filters)

    def fetchEditionCovers(self, coverQuery):
        for edition in self.windowedQuery(Edition, coverQuery, windowSize=self.batchSize):
            coverManager = self.searchForCover(edition)

            if coverManager: self.storeFoundCover(coverManager, edition)

    def searchForCover(self, edition):
        manager = CoverManager(edition, self.session)

        if manager.fetchCover() is True:
            manager.fetchCoverFile()
            manager.resizeCoverFile()

            return manager if manager.coverContent else None

    def storeFoundCover(self, manager, edition):
        coverPath = 'covers/{}/{}.{}'.format(
            manager.fetcher.SOURCE,
            manager.fetcher.coverID,
            manager.coverFormat.lower()
        )

        self.putObjectInBucket(manager.coverContent, coverPath, self.fileBucket)

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

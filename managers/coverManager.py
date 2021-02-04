import inspect
from io import BytesIO
from PIL import Image, UnidentifiedImageError

import managers.coverFetchers as fetchers


class CoverManager:
    def __init__(self, edition, dbSession):
        self.edition = edition
        self.dbSession = dbSession

        self.loadFetchers()

        self.fetcher = None
        self.coverContent = None
        self.coverFormat = None

    def loadFetchers(self):
        fetcherList = inspect.getmembers(fetchers, inspect.isclass)

        self.fetchers = [None] * len(fetcherList)

        for fetcher in fetcherList:
            _, fetcherClass = fetcher
            self.fetchers[fetcherClass.ORDER - 1] = fetcherClass

    def fetchCover(self):
        edIdentifiers = [
            (i.identifier, i.authority)
            for i in self.edition.identifiers
        ]

        for fetcherClass in self.fetchers:
            fetcher = fetcherClass(edIdentifiers, self.dbSession)
            
            if fetcher.hasCover() is True:
                self.fetcher = fetcher
                return True

        return False

    def fetchCoverFile(self):
        self.coverContent = self.fetcher.downloadCoverFile()

    def resizeCoverFile(self):
        try:
            original = Image.open(BytesIO(self.coverContent))
        except UnidentifiedImageError:
            self.coverContent = None
            return None

        originalRatio = original.width / original.height

        resizeHeight = 400
        resizeWidth = 300

        if 400 * originalRatio > 300 and originalRatio > 1:
            resizeHeight = int(round(300 / originalRatio))
        elif 400 * originalRatio > 300:
            resizeHeight = int(round(300 * originalRatio))
        else:
            resizeWidth = int(round(400 * originalRatio))

        resized = original.resize((resizeWidth, resizeHeight))

        resizedContent = BytesIO()
        resized.save(resizedContent, format=original.format)

        self.coverContent = resizedContent.getvalue()
        self.coverFormat = original.format

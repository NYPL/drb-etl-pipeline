import hashlib
import os
import requests
from requests.exceptions import ReadTimeout

from managers.coverFetchers.abstractFetcher import AbstractFetcher


class ContentCafeFetcher(AbstractFetcher):
    ORDER = 4
    SOURCE = 'contentcafe'
    NO_COVER_HASH = 'd41d8cd98f00b204e9800998ecf8427e'
    CONTENT_CAFE_URL = 'http://contentcafe2.btol.com/ContentCafe/Jacket.aspx?userID={}&password={}&type=L&Value={}'

    def __init__(self, *args):
        super().__init__(*args)

        self.apiUser = os.environ['CONTENT_CAFE_USER']
        self.apiPswd = os.environ['CONTENT_CAFE_PSWD']

        self.uri = None
        self.content = None
        self.mediaType = None

    def hasCover(self):
        for value, source in self.identifiers:
            if source != 'isbn': continue

            if self.fetchVolumeCover(value):
                self.coverID = value
                return True

        return False

    def fetchVolumeCover(self, isbn):
        print('Fetching contentcafe cover for {}'.format(isbn))

        jacketURL = self.CONTENT_CAFE_URL.format(self.apiUser, self.apiPswd, isbn)

        try:
            ccResponse = requests.get(jacketURL, timeout=5)
        except ReadTimeout:
            return False

        if ccResponse.status_code == 200:
            self.content = ccResponse.content

            if self.isNoCoverImage(ccResponse.raw.read(1024)) is False:
                return True

    def isNoCoverImage(self, rawBytes):
        return hashlib.md5(rawBytes).hexdigest() == self.NO_COVER_HASH

    def downloadCoverFile(self):
        return self.content
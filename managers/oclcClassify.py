import fasttext
import re
import requests
import os
from requests.exceptions import ConnectTimeout, HTTPError, ReadTimeout

from logger import createLog

logger = createLog(__name__)


class ClassifyManager:
    """Manages creation and execution of queries to the OCLC Classify API.
    Raises:
        DataError: Raised when an invalid title/author query is attempted
        OCLCError: Raised when the query to the API fails
    Returns:
        [str] -- A string of XML data comprising of the Classify response body.
    """
    #Forward slash at the end is needed before the query parameters for the classification API to work
    CLASSIFY_ROOT = 'https://metadata.api.oclc.org/classify/'

    LOOKUP_IDENTIFIERS = [
        'oclc', # OCLC Number
        'isbn', # ISBN (10 or 13)
        'issn', # ISSN
        'upc',  # UPC (Probably unused)
        'lccn', # LCCN
        'swid', # OCLC Work Identifier
        'stdnbr'# Sandard Number (unclear)
    ]

    NAMESPACE = {
        None: 'http://classify.oclc.org',
        'oclc': 'http://classify.oclc.org'
    }

    ANTHOLOGY_TOKENS = [
        'collection', 'collected', 'selected', 'anthology', 'complete'
    ]

    TITLE_STOPWORDS = [
        'a', 'an', 'the', 'at', 'on', 'and', 'of', 'from', 'to'
    ]

    # This is a compressed 917kb file that contains a language detection model
    LANG_MODEL = fasttext.load_model('lid.176.ftz')

    def __init__(self, iden=None, idenType=None, title=None, author=None, start=0):
        self.identifier = iden
        self.identifierType = idenType
        self.title = ClassifyManager.cleanStr(title) if title else None
        self.author = ClassifyManager.cleanStr(author) if author else None
        self.start = start

        self.addlIds = []

    def getClassifyResponse(self):
        self.generateQueryURL()

        try:
            self.execQuery()
        except (ConnectTimeout, HTTPError, ReadTimeout) as e:
            logger.exception(e)
            raise ClassifyError('Unable execute query to Classify service')

        return self.parseXMLResponse()

    def generateQueryURL(self):
        """Parses the received data and generates a Classify query based either
        on an identifier (preferred) or an author/title combination.
        """
        if self.identifier and self.identifierType:
            self.generateIdentifierURL()
        elif self.title and self.author:
            self.generateAuthorTitleURL()
        else:
            print('Cannot Classify work without identifier or title/author')
            raise ClassifyError('Record lacks identifier or title/author pair')

    @staticmethod
    def cleanStr(string):
        """Removes return and line break characters from the current work's
        title. This allows for better matching and cleaner results.
        """
        return ' '.join(string.replace('\r', ' ').replace('\n', ' ').split())

    def execQuery(self):
        """Executes the constructed query against the OCLC endpoint
        Raises:
            OCLCError: Raised if a non-200 status code is received
        Returns:
            [str] -- A string of XML data comprising of the body of the
            Classify response.
        """
        classifyResp = requests.get(self.query, 
            headers={'X-OCLC-API-Key': os.environ['OCLC_CLASSIFY_API_KEY']}, 
            timeout=10
        )

        classifyResp.raise_for_status()

        self.rawXML = classifyResp.text

    def checkTitle(self, oclcTitle):
        oclcCode = ClassifyManager.getStrLang(oclcTitle)
        sourceCode = ClassifyManager.getStrLang(self.title)
        if oclcCode == sourceCode:
            cleanOCLC = ClassifyManager.cleanTitle(oclcTitle)
            oclcAnthology = True if len(set(cleanOCLC) & set(self.ANTHOLOGY_TOKENS)) > 0 else False
            cleanSource = ClassifyManager.cleanTitle(self.title)
            sourceAnthology = True if len(set(cleanSource) & set(self.ANTHOLOGY_TOKENS)) > 0 else False
            if (
                len(set(cleanOCLC) & set(cleanSource)) > 0
                and oclcAnthology == sourceAnthology
            ):
                return True
            else:
                return False

        return True

    def checkAndFetchAdditionalEditions(self, classifyXML):
        if len(classifyXML.findall('.//oclc:edition', namespaces=self.NAMESPACE)) >= 500:
            self.fetchAdditionalIdentifiers()

    def fetchAdditionalIdentifiers(self):
        xpathNamespace = dict(list(filter(lambda x: x[0] is not None, self.NAMESPACE.items())))

        while True:
            self.start = self.start + 500
            print('Fetching editions {} to {}'.format(self.start, self.start + 500))

            self.generateQueryURL()
            self.execQuery()

            nextPageXML = etree.fromstring(self.rawXML.encode('utf-8'))

            oclcNos = nextPageXML.xpath('.//oclc:editions/oclc:edition/@oclc', namespaces=xpathNamespace)

            if len(oclcNos) < 1:
                break

            self.addlIds.extend(['{}|oclc'.format(oclc) for oclc in oclcNos])

    @classmethod
    def getStrLang(cls, string):
        try:
            langPredict = cls.LANG_MODEL.predict(string, threshold=0.5)
            logger.debug(langPredict)
            langCode = langPredict[0][0].split('__')[2]
        except (AttributeError, IndexError, ValueError) as e:
            logger.warn(e)
            langCode = 'unk'

        return langCode

    @staticmethod
    def cleanTitle(title):
        wordTokens = re.split(r'\s+', title)
        return list(filter(
            lambda x: x not in ClassifyManager.TITLE_STOPWORDS and x != '',
            [re.sub(r'[^\w]+', '', token.lower()) for token in wordTokens]
        ))

    @staticmethod
    def cleanIdentifier(identifier):
        return re.sub(r'[\D]+', '', identifier)

    @staticmethod
    def getQueryableIdentifiers(identifiers):
        return list(filter(
            lambda x: re.search(r'\|(?:isbn|issn|oclc)$', x) != None,
            identifiers
        ))


class ClassifyError(Exception):
    def __init__(self, message=None):
        self.message = message

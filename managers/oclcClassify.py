from lxml import etree
from polyglot.detect import Detector
from polyglot.detect.base import UnknownLanguage
import re
import requests


class ClassifyManager:
    """Manages creation and execution of queries to the OCLC Classify API.
    Raises:
        DataError: Raised when an invalid title/author query is attempted
        OCLCError: Raised when the query to the API fails
    Returns:
        [str] -- A string of XML data comprising of the Classify response body.
    """
    CLASSIFY_ROOT = 'http://classify.oclc.org/classify2/Classify'

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
        None: 'http://classify.oclc.org'
    }

    ANTHOLOGY_TOKENS = [
        'collection', 'collected', 'selected', 'anthology', 'complete'
    ]

    TITLE_STOPWORDS = [
        'a', 'an', 'the', 'at', 'on', 'and', 'of', 'from', 'to'
    ]

    def __init__(self, iden=None, idenType=None, title=None, author=None, start=0):
        self.identifier = iden
        self.identifierType = idenType
        self.title = ClassifyManager.cleanStr(title)
        self.author = ClassifyManager.cleanStr(author) if author else None
        self.start = start

    def getClassifyResponse(self):
        self.generateQueryURL()
        self.execQuery()
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

    @staticmethod
    def cleanStr(string):
        """Removes return and line break characters from the current work's
        title. This allows for better matching and cleaner results.
        """
        return ' '.join(string.replace('\r', ' ').replace('\n', ' ').split())

    def generateAuthorTitleURL(self):
        """Generates an author/title query for Classify.
        Raises:
            DataError: Raised if no author is received, which can cause
            unexpectedly large results to be returned for a query.
        """
        titleAuthorParam = 'title={}&author={}'.format(self.title, self.author)

        self.query = "{}?{}".format(ClassifyManager.CLASSIFY_ROOT, titleAuthorParam)

        self.addClassifyOptions()

    def generateIdentifierURL(self):
        """Creates a query based of an identifier and its type. If either field
        is missing for this request, default to an author/title search.
        """
        self.query = "{}?{}={}".format(
            ClassifyManager.CLASSIFY_ROOT,
            self.identifierType,
            self.identifier
        )
        self.addClassifyOptions()

    def addClassifyOptions(self):
        """Adds standard options to the Classify queries. "summary=false"
        indicates that a full set of edition records should be returned with a
        single work response and "maxRecs" controls the upper limit on the
        number of possible editions returned with a work.
        """
        self.query = '{}&summary=false&startRec={}&maxRecs=500'.format(
            self.query, self.start
        )

    def execQuery(self):
        """Executes the constructed query against the OCLC endpoint
        Raises:
            OCLCError: Raised if a non-200 status code is received
        Returns:
            [str] -- A string of XML data comprising of the body of the
            Classify response.
        """
        classifyResp = requests.get(self.query)
        if classifyResp.status_code != 200:
            print('OCLC Classify Request failed')
            raise Exception

        self.rawXML = classifyResp.text
    
    def parseXMLResponse(self):
        try:
            parseXML = etree.fromstring(self.rawXML.encode('utf-8'))
        except Exception:
            print('Classify returned invalid XML')
            raise ClassifyError('Invalid XML received from Classify service')

        # Check for the type of response we recieved
        # 2: Single-Work Response
        # 4: Multi-Work Response
        # 101: Invalid Identifier
        # 102: No Results found for query
        # 200: Internal OCLC Classify API error
        # Other: Raise Error
        responseXML = parseXML.find('.//response', namespaces=self.NAMESPACE)
        responseCode = int(responseXML.get('code'))

        if responseCode == 102:
            print('Did not find any information for this query')
            raise ClassifyError(message='No matching Classify records found')
        elif responseCode == 200:
            raise ClassifyError(message='Internal Classify API error encountered')
        elif responseCode == 101:
            print('Invalid identifier received. Cleaning and retrying')
            oldID = self.identifier
            cleanIdentifier = ClassifyManager.cleanIdentifier(self.identifier)
            if oldID == cleanIdentifier:
                raise ClassifyError('Unable to query identifier, invalid')
            multiRec = ClassifyManager(
                iden=cleanIdentifier,
                idenType=self.identifierType,
                title=self.title,
                author=self.author
            )
            return multiRec.getClassifyResponse()
        elif responseCode == 2:
            print('Got Single Work, parsing work and edition data')
            return [parseXML]
        elif responseCode == 4:
            print('Got Multiwork response, iterate through works to get details')
            works = parseXML.findall('.//work', namespaces=self.NAMESPACE)
            outRecords = []
            for work in works:
                oclcID = work.get('wi')
                oclcTitle = work.get('title', None)

                if self.checkTitle(oclcTitle) is False:
                    print('Found title mismatch with {}. Skipping'.format(
                        oclcTitle
                    ))
                    continue

                multiRec = ClassifyManager(
                    iden=oclcID,
                    idenType='oclc',
                    title=oclcTitle,
                    author=self.author
                )
                outRecords.append(multiRec.getClassifyResponse()[0])
            
            return outRecords
        else:
            print(responseXML)
            raise ClassifyError(message='Got unexpected response code')
    
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

    @staticmethod
    def getStrLang(string):
        try:
            langCode = Detector(string).language.code
        except UnknownLanguage:
            langCode = 'unk'
        except AttributeError:
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
            lambda x: re.search(r'\|(?:isbn|issn|oclc|lccn)$', x) != None,
            identifiers
        ))


class ClassifyError(Exception):
    def __init__(self, message=None):
        self.message = message

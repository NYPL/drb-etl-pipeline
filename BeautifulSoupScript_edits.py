from bs4 import BeautifulSoup
from bs4.element import Tag
import requests, json
from requests.exceptions import ConnectionError, HTTPError


def fetchPageHTML(url):
    elemResponse = requests.get(url)
    elemResponse.raise_for_status()
    return elemResponse

#Dicitionary of each catalog's publications 
request_urls =\
    {'AS':  'https://oi.uchicago.edu/research/publications/assyriological-studies', 
    'CAD':  'https://oi.uchicago.edu/research/publications/assyrian-dictionary-oriental-institute-university-chicago-cad',
    'CDD':  'https://oi.uchicago.edu/research/publications/demotic-dictionary-oriental-institute-university-chicago',
    'CHD':  'https://oi.uchicago.edu/research/publications/hittite-dictionary-oriental-institute-university-chicago-chd',
    'CHDS': 'https://oi.uchicago.edu/research/publications/chicago-hittite-dictionary-supplements-chds',
    'LAM':  'https://oi.uchicago.edu/research/publications/late-antique-and-medieval-islamic-near-east-lamine',
    'MAD':  'https://oi.uchicago.edu/research/publications/materials-assyrian-dictionary',
    'MKSH': 'https://oi.uchicago.edu/research/publications/materials-and-studies-kassite-history-mskh',
    'OIC':  'https://oi.uchicago.edu/research/publications/oriental-institute-communications-oic',
    'OIDA': 'https://oi.uchicago.edu/research/publications/oriental-institute-digital-archives-oida',
    'OIMP': 'https://oi.uchicago.edu/research/oimp',
    'OINE': 'https://oi.uchicago.edu/research/publications/oriental-institute-nubian-expedition-oine',
    'OIP':  'https://oi.uchicago.edu/research/publications/oriental-institute-publications-oip',
    'OIS':  'https://oi.uchicago.edu/research/publications/oriental-institute-seminars-ois',
    'SAOC': 'https://oi.uchicago.edu/research/publications/studies-ancient-oriental-civilization-saoc',
    'LE':   'https://oi.uchicago.edu/research/publications/lost-egypt',
    'MIS':  'https://oi.uchicago.edu/research/publications/miscellaneous-publications'
    }


OIC_ROOT = 'https://oi.uchicago.edu'

def main():
    #Looping through each catalog to add the download links and metadata to a dictionary
    for catalog, url in request_urls.items():
        try:
            if catalog == 'CDD':
                continue
            else:
                elem = fetchPageHTML(url)
        except Exception as e:
            print(e)
            continue

        soup = BeautifulSoup(elem.text, 'lxml')   #Parsing the catalog's webpage using BeautifulSoup

        #Parsing for dictionary catalogs
        if catalog == 'CAD' or catalog == 'CHD' or catalog == 'LE':

            titleContainer = soup.find(class_='subtitle')

            titleText = titleContainer.text

            catContainer = soup.find(class_='catalog')

            pubList = catContainer.find('tbody')

            pubEntry = pubList.find_all('tr')

            for pub in pubEntry:
                print(url)

                print(parsePubDict(pub, titleText))

        #Parsing for journal catalogs
        else:

            catContainer = soup.find(class_='content-inner-left')

            pubList = catContainer.find('ul')

            #Looping through unordered list of publications
            for pub in pubList.children:
                #Testing to make sure pub is a <li> Tag and not an empty string
                if not isinstance(pub, Tag):
                    continue
                metadata = parsePubJour(pub, catalog)

                if metadata is None:
                    continue

                downloadLink = pub.find('a', class_= "publication ss-standard ss-download btn")

                if downloadLink is None:
                    continue

                metadata['url'] = downloadLink.get('href', None)
                print(metadata)

#Parsing the journal and miscelleanous publications for metadata at the bottom of webpage
def parsePubJour(pub, catalog):
    pubLinks = pub.find_all('a')
    #Link should only be the link to the publication webpage
    detailLink = pubLinks[0].get('href', None)

    detailURL = '{}{}'.format(OIC_ROOT, detailLink)

    print(detailURL)

    try:
        pubElem = fetchPageHTML(detailURL)
    except ConnectionError or HTTPError:
        return None
    
    pubSoup = BeautifulSoup(pubElem.text, 'lxml')

    pubContainer = pubSoup.find(class_='content-inner-left')

    subTitleSoup = pubContainer.find(class_='subtitle')

    titleSoup = subTitleSoup.find('cite')

    if pubContainer is None:
        return None
    #Metadata list is the last unordered list on the webpage
    dataList = pubContainer.find_all('ul')[-1]

    metadata = dataList.find_all('li')

    #CHDS metadata dictionary
    if catalog == 'CHDS':
        if metadata[2].text[0:4] == 'ISBN':
            return {
            'title': titleSoup.text,
            'series': metadata[0].text,
            'publicationInfo': metadata[1].text,
            'isbnNumber': metadata[2].text,
            'extent': metadata[3].text
            }
        else:
            return {
            'title': titleSoup.text,
            'series': metadata[1].text,
            'publicationInfo': metadata[2].text,
            'isbnNumber': metadata[3].text,
            'extent': metadata[4].text
            }
    #OIDA metadata dictionary
    elif catalog == 'OIDA':
        return {
        'title': titleSoup.text,
        'series': metadata[0].text,
        'publicationInfo': metadata[1].text,
        'extent': metadata[2].text
        }
    #OIMP and OIP metadata dictionary
    elif catalog == 'OIMP'  or catalog== 'OIP':
        if len(metadata) == 2 or len(metadata) == 3:
            return {
                'title': titleSoup.text,
                'publicationInfo': metadata[0],
                'extent': metadata[1]
            }
        elif len(metadata) == 4: #OIP 117 has metadata in middle of page instead of at the bottom
            return None
        else:
            return {
                'title': titleSoup.text,
                'series': metadata[0].text,
                'publicationInfo': metadata[1].text,
                'isbnNumber': [metadata[2].text, metadata[3].text],
                'extent': metadata[4].text
            }

    #OIS metadata dictionary(Sometimes series firsts and sometimes it's last in the list)
    elif catalog == "OIS":
        return {
            'title': titleSoup.text,
            'series': metadata[3].text,
            'publicationInfo': metadata[0].text,
            'isbnNumber': metadata[1].text,
            'extent': metadata[2].text
            }
    #Miscellaneous metadata dictionary
    elif catalog == 'MIS':
        return {
            'title': titleSoup.text,
            'publicationInfo': metadata[1].text,
            'isbnNumber': [metadata[3].text, metadata[4].text],
            'extent': metadata[2].text
        }
    #Some journals don't have ISBN metadata
    else:
        if len(metadata) == 1:
            return None
        elif metadata[2].text[0:4] == 'ISBN':
            return {
            'title': titleSoup.text,
            'series': metadata[0].text,
            'publicationInfo': metadata[1].text,
            'isbnNumber': metadata[2].text,
            'extent': metadata[3].text
            }
        else:
            return {
            'title': titleSoup.text,
            'series': metadata[0].text,
            'publicationInfo': metadata[1].text,
            'extent': metadata[2].text
            }

#Parsing Dictionary catalogs
def parsePubDict(pub, titleText):
    pub_tds = pub.find_all('td')
    metadata = {
        'title': titleText,
        'Volume': pub_tds[0].text,
        'publicationInfo': pub_tds[2].text,
        'isbnNumber': pub_tds[3].text,
        'extent': pub_tds[1].text
    }
    downloadLink = pub.find('a', class_= "publication ss-standard ss-download btn")
    #Conditional if there is no download link for publication
    if downloadLink != None:
        metadata['url'] = downloadLink.get('href', None)
    return metadata
    

if __name__ == '__main__':
    main()
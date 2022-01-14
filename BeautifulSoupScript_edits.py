from bs4 import BeautifulSoup
from bs4.element import Tag
import requests, json


def fetchPageHTML(url):
    elemResponse = requests.get(url)
    elemResponse.raise_for_status()
    return elemResponse

#Array of each catalog publications
request_urls = [
    'https://oi.uchicago.edu/research/publications/assyriological-studies', 
    'https://oi.uchicago.edu/research/publications/assyrian-dictionary-oriental-institute-university-chicago-cad',
    'https://oi.uchicago.edu/research/publications/demotic-dictionary-oriental-institute-university-chicago',
    'https://oi.uchicago.edu/research/publications/hittite-dictionary-oriental-institute-university-chicago-chd',
    'https://oi.uchicago.edu/research/publications/chicago-hittite-dictionary-supplements-chds',
    'https://oi.uchicago.edu/research/publications/late-antique-and-medieval-islamic-near-east-lamine',
    'https://oi.uchicago.edu/research/publications/materials-assyrian-dictionary',
    'https://oi.uchicago.edu/research/publications/materials-and-studies-kassite-history-mskh',
    'https://oi.uchicago.edu/research/publications/oriental-institute-communications-oic',
    'https://oi.uchicago.edu/research/publications/oriental-institute-digital-archives-oida',
    'https://oi.uchicago.edu/research/oimp',
    'https://oi.uchicago.edu/research/publications/oriental-institute-nubian-expedition-oine',
    'https://oi.uchicago.edu/research/publications/oriental-institute-publications-oip',
    'https://oi.uchicago.edu/research/publications/oriental-institute-seminars-ois',
    'https://oi.uchicago.edu/research/publications/studies-ancient-oriental-civilization-saoc',
    'https://oi.uchicago.edu/research/publications/lost-egypt',
    'https://oi.uchicago.edu/research/publications/miscellaneous-publications'
]

download_dict = {}
key = 1


OIC_ROOT = 'https://oi.uchicago.edu'

def main():
    #Looping through each catalog to add the download links and metadata to a dictionary
    for i, url in enumerate(request_urls):
        try:
            elem = fetchPageHTML(url)
        except Exception as e:
            print(e)
            continue

        soup = BeautifulSoup(elem.text, 'lxml')   #Parsing the catalog's webpage using BeautifulSoup

        if i == 1:
            metadata = parse_Pub_Alt(soup)
            print(metadata)
    
        catContainer = soup.find(class_='content-inner-left')

        pubList = catContainer.find('ul')

        #Looping through unordered list of publications
        for pub in pubList.children:
            #Testing to make sure pub is a <li> Tag and not an empty string
             if not isinstance(pub, Tag):
                 continue
             metadata = parsePub(pub)
             downloadLink = pub.find('a', class_= "publication ss-standard ss-download btn")
             metadata['url'] = downloadLink.get('href', None)
             print(metadata)
        '''
        for link in soup.find_all('a', class_= "publication ss-standard ss-download btn"):
            download_dict[key] = link.get('href')
            key += 1
	'''

    '''
    #Serializing download_dict to create a JSON file
    with open("data_file.json", "w") as write_file:
        json.dump(download_dict, write_file)
    '''
#Parsing the publications for metadata at the bottom of webpage
def parsePub(pub):
    pubLinks = pub.find_all('a')
    #Link should only be the link to the publication webpage
    detailLink = pubLinks[0].get('href', None)

    detailURL = '{}{}'.format(OIC_ROOT, detailLink)

    print(detailURL)

    pubElem = fetchPageHTML(detailURL)
    
    pubSoup = BeautifulSoup(pubElem.text, 'lxml')

    pubContainer = pubSoup.find(class_='content-inner-left')

    #Metadata list is the last unordered list on the webpage
    dataList = pubContainer.find_all('ul')[-1]

    metadata = dataList.find_all('li')

    if metadata[2].text[0:4] == 'ISBN':
        return {
       'series': metadata[0].text,
       'publicationInfo': metadata[1].text,
       'isbnNumber': metadata[2].text,
       'extent': metadata[3].text
    }
    else:
        return {
       'series': metadata[0].text,
       'publicationInfo': metadata[1].text,
       'extent': metadata[2].text
    }

def parse_Pub_Alt(soup):
    catContainer = soup.find(class_='catalog')

    pubList = catContainer.find('tbody')

    pubEntry = pubList.find_all('tr')

    for pub in pubEntry:
        pub_tds = pub.find_all('td')
        return({
            'Volume': pub_tds[0].text,
            'publicationInfo': pub_tds[2].text,
            'isbnNumber': pub_tds[3].text,
            'Extent': pub_tds[1].text
            } )

if __name__ == '__main__':
    main()
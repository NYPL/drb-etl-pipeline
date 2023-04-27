from bs4 import BeautifulSoup, NavigableString
from bs4.element import Tag
import requests, json


def fetchPageHTML(url):
    elemResponse = requests.get(url)
    elemResponse.raise_for_status()
    return elemResponse

#Array of each catalog publications
request_urls = [
    'https://isac.uchicago.edu/research/publications/assyriological-studies',
    'https://isac.uchicago.edu/research/publications/chicago-assyrian-dictionary',
    # 'https://isac.uchicago.edu/research/publications/chicago-demotic-dictionary' COME BACK TO THIS ONE
    'https://isac.uchicago.edu/research/publications/chicago-hittite-dictionary',
    'https://isac.uchicago.edu/research/publications/chicago-hittite-dictionary-supplements-chds',
    'https://isac.uchicago.edu/research/publications/late-antique-and-medieval-islamic-near-east-lamine',
    'https://isac.uchicago.edu/research/publications/materials-assyrian-dictionary',
    'https://isac.uchicago.edu/research/publications/materials-and-studies-kassite-history-mskh',
    'https://isac.uchicago.edu/research/publications/oriental-institute-nubian-expedition-oine',
    'https://isac.uchicago.edu/research/publications/oriental-institute-communications-oic',
    'https://isac.uchicago.edu/research/publications/oriental-institute-digital-archives-oida',
    # 'https://isac.uchicago.edu/research/oimp', Hardbook/ebook isbn 
    # 'https://isac.uchicago.edu/research/publications/oriental-institute-publications-oip' Hardbook/ebook isbn,
    'https://isac.uchicago.edu/research/publications/oriental-institute-seminars-ois',
    # 'https://isac.uchicago.edu/research/publications/studies-ancient-oriental-civilization-saoc', TOC at botoom of page
    'https://isac.uchicago.edu/research/publications/lost-egypt'
    # 'https://isac.uchicago.edu/research/publications/miscellaneous-publications' Long metadata list
]

finalMetaData = []

OIC_ROOT = 'https://isac.uchicago.edu/'

def main(): 

    '''Looping through each catalog to add the download links and metadata to a dictionary'''

    for i, url in enumerate(request_urls):
        try:
            elem = fetchPageHTML(url)
        except Exception as e:
            print(e)
            continue

        if url == 'https://isac.uchicago.edu/research/publications/chicago-assyrian-dictionary' or \
            url == 'https://isac.uchicago.edu/research/publications/chicago-hittite-dictionary' or \
            url == 'https://isac.uchicago.edu/research/publications/lost-egypt':

                parsePub(elem)
        else: 
            parsePub2(elem, url)

    with open("data_file.json", "w") as write_file:
        json.dump(finalMetaData, write_file, indent = 6)

def parsePub(elem):

    '''Parsing publications with metadata present on same page as download link'''

    soup = BeautifulSoup(elem.text, 'lxml')   #Parsing the catalog's webpage using BeautifulSoup
        
    catContainer = soup.find(class_='catalog')

    pubList = catContainer.find('tbody')

    pubEntry = pubList.find_all('tr')

    for pub in pubEntry:
        pub_tds = pub.find_all('td')
        if pub_tds[5].find('a', class_="publication ss-standard ss-download btn"):
            finalMetaData.append({
            'Volume': pub_tds[0].text,
            'publicationInfo': pub_tds[2].text,
            'isbnNumber': pub_tds[3].text,
            'Extent': pub_tds[1].text,
            'url': pub_tds[5].find('a', class_="publication ss-standard ss-download btn").get('href', None)
        })
        else:
            finalMetaData.append({
            'Volume': pub_tds[0].text,
            'publicationInfo': pub_tds[2].text,
            'isbnNumber': pub_tds[3].text,
            'Extent': pub_tds[1].text,
            'url': ''
        })


def parsePub2(elem, url):

    '''Parsing the publications for metadata at the bottom of webpage'''

    soup = BeautifulSoup(elem.text, 'lxml')
    pubContainer = soup.find(class_='content-inner-left')
    pubList = pubContainer.find('ul')

    #Looping through unordered list of publications
    for i, pub in enumerate(pubList.children):
        #Testing to make sure pub is a <li> Tag and not an empty string
        if not isinstance(pub, Tag):
            continue

        # if url == 'https://isac.uchicago.edu/research/publications/studies-ancient-oriental-civilization-saoc':
        #     parsePubSAOC(pub, url)
        #     continue

        if pub.find('a', class_= "publication ss-standard ss-download btn"):
            downloadLink = pub.find('a', class_= "publication ss-standard ss-download btn").get('href', None)
    
        pubLinks = pub.find_all('a')
        
        #Link should only be the link to the publication webpage
        detailLink = pubLinks[0].get('href', None)
        print(detailLink)

        detailURL = detailLinkUpdate(detailLink)
        print(detailURL)

        pubElem = fetchPageHTML(detailURL)
        
        pubSoup = BeautifulSoup(pubElem.text, 'lxml')

        pubContainer = pubSoup.find(class_='content-inner-left')

        # if detailURL == 'https://isac.uchicago.edu//node/3788' or \
        #     detailURL == 'https://isac.uchicago.edu//node/3990'or \
        #     detailURL == 'https://isac.uchicago.edu//node/3390':
        #     parsePubMISC(detailURL, pubContainer, downloadLink)
        #     continue

        # Metadata list is the last unordered list on the webpage
        dataList = pubContainer.find_all('ul')[-1]

        metadata = dataList.find_all('li')

        if url == 'https://isac.uchicago.edu/research/publications/chicago-hittite-dictionary-supplements-chds':
            if len(metadata) > 5:
                finalMetaData.append({
                    'series': metadata[1].text,
                    'publicationInfo': metadata[2].text,
                    'isbnNumber': metadata[3].text,
                    'extent': metadata[4].text,
                    'url': downloadLink
                }) 
            else:
                finalMetaData.append({
                    'series': metadata[0].text,
                    'publicationInfo': metadata[1].text,
                    'isbnNumber': metadata[2].text,
                    'extent': metadata[3].text,
                    'url': downloadLink
                }) 

        elif url == 'https://isac.uchicago.edu/research/publications/oriental-institute-seminars-ois':
            if len(metadata) == 5 and 'Seminars' in metadata[0].text:
                finalMetaData.append({
                    'series': metadata[0].text,
                    'publicationInfo': metadata[1].text,
                    'isbnNumber': metadata[2].text,
                    'extent': metadata[3].text,
                    'url': downloadLink
                }) 
            elif len(metadata) == 5 and 'Seminars' not in metadata[0].text:
                finalMetaData.append({
                    'publicationInfo': metadata[0].text,
                    'isbnNumber': metadata[1].text,
                    'extent': metadata[2].text,
                    'url': downloadLink
                })
            elif len(metadata) == 6 and 'Seminars' in metadata[3].text:
                finalMetaData.append({
                    'series': metadata[3].text,
                    'publicationInfo': metadata[0].text,
                    'isbnNumber': metadata[1].text,
                    'extent': metadata[2].text,
                    'url': downloadLink
                })
            else:
                finalMetaData.append({
                    'series': metadata[0].text,
                    'publicationInfo': metadata[1].text,
                    'isbnNumber': metadata[2].text,
                    'extent': metadata[3].text,
                    'url': downloadLink
                })

        elif (url == 'https://isac.uchicago.edu/research/publications/miscellaneous-publications'#or url == 'https://isac.uchicago.edu/research/oimp')\
            and (len(metadata) == 2 or len(metadata) == 3)):
            
            finalMetaData.append({
                'publicationInfo': metadata[0].text,
                'extent': metadata[1].text,
                'url': downloadLink
            }) 
        
        # elif url == 'https://isac.uchicago.edu/research/publications/oriental-institute-publications-oip'\
        #     and len(metadata) == 2:
        #     finalMetaData.append({
        #         'series': metadata[0].text,
        #         'publicationInfo': metadata[1].text,
        #         'url': downloadLink
        #     }) 
        
        elif url == 'https://isac.uchicago.edu/research/publications/oriental-institute-communications-oic'\
            and detailLink == '/node/3305':
                finalMetaData.append({
                'series': metadata[0].text,
                'publicationInfo': metadata[1].text,
                'url': downloadLink
            }) 

        elif url == 'https://isac.uchicago.edu/research/publications/oriental-institute-digital-archives-oida'\
            and detailLink == '/node/3295':
                finalMetaData.append({
                'series': metadata[0].text,
                'publicationInfo': metadata[1].text,
                'extent': metadata[2].text,
                'url': downloadLink
            })
                
        # elif url == 'https://isac.uchicago.edu/research/publications/oriental-institute-publications-oip'\
        #     and (detailLink == '/node/3195' or detailLink == '/node/3191' or detailLink == '/node/3195' or detailLink == '/node/3184'\
        #     or detailLink == '/node/3254'):
        #         finalMetaData.append({
        #         'series': metadata[0].text,
        #         'publicationInfo': metadata[1].text,
        #         'extent': metadata[2].text,
        #         'url': downloadLink
        #     })
                
        elif 'ISBN' in metadata[2].text:
            finalMetaData.append({
                'series': metadata[0].text,
                'publicationInfo': metadata[1].text,
                'isbnNumber': metadata[2].text,
                'extent': metadata[3].text,
                'url': downloadLink
            }) 
        elif 'ISBN' in metadata[3].text:
            #print(metadata[3].text.split('\\')[0])
            #metadata[3].text = metadata[3].text.split('\\')[0]

            finalMetaData.append({
                'series': metadata[0].text,
                'publicationInfo': metadata[1].text,
                'isbnNumber': metadata[3].text,
                'extent': metadata[2].text,
                'url': downloadLink
            })
        else:
            finalMetaData.append({
                'series': metadata[0].text,
                'publicationInfo': metadata[1].text,
                'extent': metadata[2].text,
                'url': downloadLink
            }) 

# def parsePubSAOC(pub, url):
#     pubLinks = pub.find_all('a')
        
#     #Link should only be the link to the publication webpage
#     detailLink = pubLinks[0].get('href', None)

#     if pubLinks[0].has_attr('class') == True:
#         if 'url' not in finalMetaData[-1]:
#             downloadLink = pub.find('a', class_= "publication ss-standard ss-download btn").get('href', None)
#             print(finalMetaData)
#             #finalMetaData.extend({'url': downloadLink})
#             finalMetaData[-1]['url'] = downloadLink
#     elif pub.find('a', class_= "publication ss-standard ss-download btn") != None and pubLinks[0].has_attr('class') == False:
#         pubLinks = pub.find_all('a')

#         #Link should only be the link to the publication webpage
#         detailLink = pubLinks[0].get('href', None)
#         print(detailLink)

#         detailURL = f'{OIC_ROOT}{detailLink}'

#         pubElem = fetchPageHTML(detailURL)

#         pubSoup = BeautifulSoup(pubElem.text, 'lxml')

#         pubContainer = pubSoup.find(class_='content-inner-left')

#         #Metadata list is the last unordered list on the webpage
#         if detailURL == 'https://isac.uchicago.edu//node/3110':
#             dataList = pubContainer.find_all('ul')[0]
#         else:
#             dataList = pubContainer.find_all('ul')[-1]

#         metadata = dataList.find_all('li')

#         downloadLink = pub.find('a', class_= "publication ss-standard ss-download btn").get('href', None)

#         print(metadata)

#         if 'ISBN' in metadata[2].text:
#             finalMetaData.append({
#                 'series': metadata[0].text,
#                 'publicationInfo': metadata[1].text,
#                 'isbnNumber': metadata[2].text,
#                 'extent': metadata[3].text,
#                 'url': downloadLink
#             }) 
#         else:
#             finalMetaData.append({
#                 'series': metadata[0].text,
#                 'publicationInfo': metadata[1].text,
#                 'extent': metadata[2].text,
#                 'url': downloadLink
#             })
#     else:
#         pubLinks = pub.find_all('a')

#         #Link should only be the link to the publication webpage
#         detailLink = pubLinks[0].get('href', None)
#         print(detailLink)

#         detailURL = f'{OIC_ROOT}{detailLink}'

#         pubElem = fetchPageHTML(detailURL)

#         pubSoup = BeautifulSoup(pubElem.text, 'lxml')

#         pubContainer = pubSoup.find(class_='content-inner-left')

#         #Metadata list is the last unordered list on the webpage
#         dataList = pubContainer.find_all('ul')[-1]

#         metadata = dataList.find_all('li')

#         print(metadata)

#         if 'ISBN' in metadata[2].text:
#             finalMetaData.append({
#                 'series': metadata[0].text,
#                 'publicationInfo': metadata[1].text,
#                 'isbnNumber': metadata[2].text,
#                 'extent': metadata[3].text,
#             }) 
#         else:
#             finalMetaData.append({
#                 'series': metadata[0].text,
#                 'publicationInfo': metadata[1].text,
#                 'extent': metadata[2].text,
#             })

def detailLinkUpdate(detailLink):
    #if detailLink == 'https://oi.uchicago.edu/research/publications/oimp/oimp-36-our-work-modern-jobs' or \
        #detailLink == 'https://oi.uchicago.edu/research/publications/oimp/oimp-28-catastrophe':
            #return detailLink
    # if detailLink == 'https://www.isdistribution.com/Refer.aspx?isbn=9781885923653':
    #     #detailURL = 'https://isac.uchicago.edu/research/publications/oimp/oimp-31-ancient-israel-highlights-collections-oriental-institute'
    #     return detailURL
    # else:
    detailURL = f'{OIC_ROOT}{detailLink}'
    return detailURL
    
# def parsePubMISC(detailURL, pubContainer, downloadLink):
#     if detailURL == 'https://isac.uchicago.edu//node/3788':
#         dataList = pubContainer.find_all('p')[-1]
#         print(dataList)

#         line_break =  dataList.find('br')       # loop through line break tags
#         line_break.replaceWith(' ')       # replace br tags with delimiter
#         strings = dataList.get_text().split('\n')
#         finalMetaData.append({
#         'series': strings[0],
#         'publicationInfo': strings[1],
#         'isbnNumber': strings[4],
#         'extent': strings[1],
#         'url': downloadLink
#         }) 
#         print(strings)
    
#     elif detailURL == 'https://isac.uchicago.edu//node/3990':
#         finalMetaData.append({
#             'url': downloadLink
#         }) 

#     elif detailURL == 'https://isac.uchicago.edu//node/3390':
#         dataList = pubContainer.find_all('ul')[-1]

#         metadata = dataList.find_all('li')

#         finalMetaData.append({
#             'publicationInfo': metadata[0].text,
#             'extent': metadata[1].text,
#         })
        

if __name__ == '__main__':
    main()
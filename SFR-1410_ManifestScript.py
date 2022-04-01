import boto3
import json
import logging

from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

logging.basicConfig(filename='manifest.log', encoding='utf-8', level=logging.INFO)

s3_client = boto3.client("s3")

listObjects = s3_client.list_objects_v2(Bucket='drb-files-qa', Prefix='manifests/muse/')
contentListObjects = listObjects['Contents']

#Iterating through all the Content objects to access the JSON muse objects
for c in contentListObjects:
    currKey = c['Key']
    museObject = s3_client.get_object(Bucket='drb-files-qa', Key=f'{currKey}')

    #Decode UTF-8 bytes to Unicode, and convert single quotes 
    #to double quotes to make it valid JSON
    for i in object['Body'].iter_lines():
        museStrObject = i.decode('utf8').replace("'", '"')

        # Load the JSON to a Python list and access readingOrder link
        museDictObject = json.loads(museStrObject)
        logging.info(museDictObject['readingOrder'])

    r = 1
    while r < len(museDictObject['readingOrder']):

        urlLink = museDictObject['readingOrder'][r]['href']
        logging.info(urlLink)

        #Convert ParseResponse to List object to modify data
        url_parts = list(urlparse(urlLink))
        query = dict(parse_qsl(url_parts[4]))
        logging.info(query)

        #Updating query parameter of url
        params = {'start': 2}
        query.update(params)
        url_parts[4] = urlencode(query)

        #Updating old url link with new one
        museDictObject['readingOrder'][r]['href'] = urlunparse(url_parts)

        r += 1

    s3_client.put_object(Bucket='drb-files-qa', Key=f'{currKey}', Body = json.dumps(museDictObject), ACL='public-read', ContentType = 'application/json')

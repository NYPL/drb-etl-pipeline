import os
import re

from model import Record
from main import loadEnvFile
from managers import DBManager


def main():
    '''
    Updating NYPL catalog records with new link to replace text/html link
    '''

    loadEnvFile('local-qa', fileString='config/{}.yaml')

    dbManager = DBManager(
        user= os.environ.get('POSTGRES_USER', None),
        pswd= os.environ.get('POSTGRES_PSWD', None),
        host= os.environ.get('POSTGRES_HOST', None),
        port= os.environ.get('POSTGRES_PORT', None),
        db= os.environ.get('POSTGRES_NAME', None)
    )

    dbManager.generateEngine()

    dbManager.createSession()

    catalogRegex = r'catalog\": true' 
    linkRegex = r'text\/html'

    for record in dbManager.session.query(Record) \
        .filter(Record.source == 'nypl').all():
            
            for i, elem in enumerate(record.has_part):
                if re.search(linkRegex, elem) != None:
                    if re.search(catalogRegex, elem) != None:
                        record.has_part = [record.has_part[i].replace('text/html', 'application/html+catalog')]

    dbManager.commitChanges()
    

if __name__ == '__main__':
    main()
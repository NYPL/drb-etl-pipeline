import os
import json

from model import Record
from managers import DBManager

import json

jsonFile = 'UofM_FullAccess_CSV.json'

fullAccessArray = []

def main():

    '''Retrieving former LA works that are now PD'''

    dbManager = DBManager(
        user= os.environ.get('POSTGRES_USER', None),
        pswd= os.environ.get('POSTGRES_PSWD', None),
        host= os.environ.get('POSTGRES_HOST', None),
        port= os.environ.get('POSTGRES_PORT', None),
        db= os.environ.get('POSTGRES_NAME', None)
    )

    dbManager.generateEngine()

    dbManager.createSession()

    with open('ingestJSONFiles/UofM_FullAccess_CSV.json') as f:
        UofMBooks = json.load(f)

    for record in dbManager.session.query(Record) \
        .filter(Record.source == 'UofM').all():
            for book in UofMBooks['data']:
                if record.title in book['Title']:
                    if book['Access in DRB'] == "Full Access":
                        fullAccessArray.append(record.title)

    print(fullAccessArray)
    print(len(fullAccessArray))

    dbManager.closeConnection()
                
if __name__ == '__main__':
    main()


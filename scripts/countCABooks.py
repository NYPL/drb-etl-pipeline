import os
import json

from model import Record
from managers import DBManager


def main():

    '''Creating a list of public domain Cali books from Hathitrust that exists in the database'''

    dbManager = DBManager(
        user= os.environ.get('POSTGRES_USER', None),
        pswd= os.environ.get('POSTGRES_PSWD', None),
        host= os.environ.get('POSTGRES_HOST', None),
        port= os.environ.get('POSTGRES_PORT', None),
        db= os.environ.get('POSTGRES_NAME', None)
    )

    dbManager.generateEngine()

    dbManager.createSession()

    count = 0
    UCBooksDRB = []

    with open('UCBooks.json') as f:
        UCBooks = json.load(f)
        
    for sourceID in UCBooks:
        record = dbManager.session.query(Record).filter(Record.source_id == f'{sourceID}|hathi').first()
        if record:
            UCBooksDRB.append(f'{sourceID}|hathi')
            count += 1

    print(UCBooksDRB)
    print(count)

    dbManager.closeConnection()

if __name__ == '__main__':
    main()

    
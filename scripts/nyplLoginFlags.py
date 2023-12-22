import os

from model import Link
from managers import DBManager
from sqlalchemy import or_
import json

def main():
    
    '''Updating NYPL Link flags with a new nypl_login flag'''

    dbManager = DBManager(
        user= os.environ.get('POSTGRES_USER', None),
        pswd= os.environ.get('POSTGRES_PSWD', None),
        host= os.environ.get('POSTGRES_HOST', None),
        port= os.environ.get('POSTGRES_PORT', None),
        db= os.environ.get('POSTGRES_NAME', None)
    )

    dbManager.generateEngine()

    dbManager.createSession()

    for link in dbManager.session.query(Link) \
        .filter(or_(Link.media_type == 'application/html+edd', Link.media_type == 'application/x.html+edd')).all():
            if link.flags and 'edd' in link.flags and link.flags['edd'] == True:
                #The link.flags doesn't update if the dict method isn't called on it
                newLinkFlag = dict(link.flags)
                newLinkFlag['nypl_login'] = True
                link.flags = newLinkFlag

    dbManager.commitChanges()

if __name__ == '__main__':
    main()
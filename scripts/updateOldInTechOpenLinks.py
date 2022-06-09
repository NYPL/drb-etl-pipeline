import os
import re

from model import Record
from main import loadEnvFile
from managers import DBManager
from processes import DOABProcess


def main():
    '''
    Updating current IntechOpen records with new HTML Links to fix Read Online links on DRB site
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

    doabProcess = DOABProcess('single', None, None, None)

    identRegex = r'intechopen.com\/storage\/books\/([\d]+)'

    for record in dbManager.session.query(Record) \
        .filter(Record.source != 'doab') \
        .filter(Record.publisher == '{IntechOpen||,IntechOpen||}').all():
            
            match = re.search(identRegex, record.has_part)

            if match == None:
                doabProcess.importSingleOAIRecord(record.source_id)
                
            
    dbManager.commitChanges()

if __name__ == '__main__':
    main()
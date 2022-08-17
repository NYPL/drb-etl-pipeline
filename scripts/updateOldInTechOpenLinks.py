import os
import re

from model import Record
from main import loadEnvFile
from managers import DBManager
from processes import DOABProcess


def main():

    '''Updating current IntechOpen records with new HTML Links to fix Read Online links on DRB site'''

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

    doabProcess = DOABProcess('single', None, None, None, None, None)

    identRegex = r'intechopen.com\/books\/([\d]+)'

    for record in dbManager.session.query(Record) \
        .filter(Record.source == 'doab') \
        .filter(Record.publisher == '{IntechOpen||,IntechOpen||}').all():
            
            for i in record.has_part:
                match = re.search(identRegex, i)
                if match != None:
                    break

            if match == None:
                doabProcess.importSingleOAIRecord(record.source_id)
                doabProcess.saveRecords()
                doabProcess.records = set()     #Clears memory space for process class after each import

    dbManager.commitChanges()

if __name__ == '__main__':
    main()
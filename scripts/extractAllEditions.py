import os

from model import Edition
from main import loadEnvFile
from managers import DBManager
from model.utilities.extractDailyEdition import extract


#Extracting the edition number from the edition_statement column of the DRB database to fill out the edition column
def main():

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

    for edit in dbManager.session.query(Edition) \
        .filter(Edition.edition_statement != None) \
        .filter(Edition.languages != None) \
        .filter(Edition.languages != []) \
        .filter(Edition.languages != [{}]).all():
            editNumber = extract(edit.edition_statement, edit.languages[0]['language'])
            edit.edition = editNumber

    dbManager.commitChanges()

if __name__ == '__main__':
    main()
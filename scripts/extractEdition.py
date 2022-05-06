import os

from model import Edition
from main import loadEnvFile
from managers import DBManager


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
        .filter(Edition.edition_statement != None and Edition.languages[0]['language'] == 'English'):
            editStatement = edit.edition_statement
            editDict = {'first': 1, 'second': 2, 'third': 3, 'fourth': 4, 'fifth': 5, \
                        'sixth': 6, 'seventh': 7, 'eigth': 8, 'ninth': 9, 'tenth': 10}
            editNumber = None

            #Edition statements with edition numbers in their string form like first, second, third, etc.
            for word in editStatement.split():
                if word in editDict.keys():
                    editNumber = editDict[word]
                    edit.edition = editNumber
                    break

            #Edition statements with edition numbers in their int form like 1, 2, 3, etc.
            if editNumber == None:
                for word in list(editStatement):
                    if word.isdigit():
                        editNumber = int(word)
                        edit.edition = editNumber
                        break

    dbManager.commitChanges()

if __name__ == '__main__':
    main()
import os
import re 

from model import Work
from managers import DBManager
from Levenshtein import jaro_winkler
from logger import createLog
from sqlalchemy import or_, func

logger = createLog(__name__)

def main():

    '''Deleting current duplicate authors/contributors with improved Levenshtein implementation'''

    dbManager = DBManager(
        user= os.environ.get('POSTGRES_USER', None),
        pswd= os.environ.get('POSTGRES_PSWD', None),
        host= os.environ.get('POSTGRES_HOST', None),
        port= os.environ.get('POSTGRES_PORT', None),
        db= os.environ.get('POSTGRES_NAME', None)
    )

    dbManager.generateEngine()

    dbManager.createSession()

    countAuth = 0
    countWorkContrib = 0
    countEditContrib = 0
    batchSize = 1000

    for work in dbManager.session.query(Work) \
        .filter(or_(func.jsonb_array_length(Work.authors) > 1, func.jsonb_array_length(Work.contributors) > 1)) \
        .yield_per(batchSize):
            
            if work.authors and len(work.authors) > 1:
                work.authors = deleteDuplicateAgents(work.authors, countAuth, 'author')
            if work.contributors and len(work.contributors) > 1:
                work.contributors = deleteDuplicateAgents(work.contributors, countWorkContrib, \
                                                          'work contributor')
            dbManager.session.add(work)

            for edition in work.editions:
                if edition.contributors and len(edition.contributors) > 1: 
                    edition.contributors = deleteDuplicateAgents(edition.contributors, \
                                                                countEditContrib, 'edition contributor')
                    dbManager.session.add(edition)

    dbManager.closeConnection()


def deleteDuplicateAgents(agent, count, type):
    
    '''Deleting duplicate agents in works and editions'''
 
    for currIndex, currAgent in enumerate(agent):
                   
        if currIndex == len(agent)-1:
            break
                   
        cleanCurrAgent = re.sub(r'[.,:\(\)\-0-9]+', '', currAgent['name'].lower())

        for nextAgent in agent[1:]:
            cleanNextAgent = re.sub(r'[.,:\(\)\-0-9]+', '', nextAgent['name'].lower())
            if jaro_winkler(cleanCurrAgent, cleanNextAgent) > 0.74:
                mergeAgents(currAgent, nextAgent)
                agent.remove(nextAgent)
                print(agent)
                count+=1
                if type == 'author':
                    logger.info(f'Deleted {count} duplicate work author(s)')
                    
                elif type == 'work contributor':
                    logger.info(f'Deleted {count} duplicate work contributor(s)')
                    
                elif type == 'edition contributor':
                    logger.info(f'Deleted {count} duplicate edition contributor(s)')

                else: 
                    logger.info(agent)
                    raise Exception
                
    return agent

def mergeAgents(existing, new):
    if new['viaf'] != '':
        existing['viaf'] = new['viaf']

    if new['lcnaf'] != '':
        existing['lcnaf'] = new['lcnaf']
    
    if new['primary'] != '':
        existing['primary'] = new['primary']

    if 'role' in new.keys():
        roleSet = set(existing['roles'])
        roleSet.add(new['role'])
        existing['roles'] = list(roleSet)
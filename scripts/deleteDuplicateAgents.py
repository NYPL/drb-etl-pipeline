import os
import re 
import logging 

from model import Work, Edition
from managers import DBManager
from Levenshtein import jaro_winkler
from logger import createLog
from sqlalchemy import or_, func

logger = createLog(__name__)

logging.basicConfig(filename='duplicateAgents.log', encoding='utf-8', level=logging.INFO)

def main(dryRun=True):

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
            
            logging.info('_________Work Duplicate Authors/Contributors Deletion_________')

            if work.authors and len(work.authors) > 1:
                work.authors = deleteDuplicateAgents(work.id, work.authors, countAuth, 'author')
            if work.contributors and len(work.contributors) > 1:
                work.contributors = deleteDuplicateAgents(work.id, work.contributors, countWorkContrib, \
                                                          'work contributor')
            dbManager.session.add(work)

    for edition in dbManager.session.query(Edition) \
        .filter(func.jsonb_array_length(Edition.contributors) > 1) \
        .yield_per(batchSize):
            if edition.contributors and len(edition.contributors) > 1:
                logging.info('_________Edition Duplicate Contributors Deletion_________')

                edition.contributors = deleteDuplicateAgents(edition.id, edition.contributors, \
                                                            countEditContrib, 'edition contributor')
                dbManager.session.add(edition)

    if dryRun == True:
        logging.info('________DRY RUN COMPLETED________')

        dbManager.rollbackChanges()
        dbManager.session.close()
        dbManager.engine.dispose()
    else:
        logging.info('________DELETION COMPLETED________')
        dbManager.closeConnection()


def deleteDuplicateAgents(agentID, agent, count, type):
    
    '''Deleting duplicate agents in works and editions'''
 
    for currIndex, currAgent in enumerate(agent):
                   
        if currIndex == len(agent)-1:
            break
                   
        cleanCurrAgent = re.sub(r'[.,:\(\)\-0-9]+', '', currAgent['name'].lower())
        logging.info(cleanCurrAgent)

        for nextAgent in agent[currIndex+1:]:
            cleanNextAgent = re.sub(r'[.,:\(\)\-0-9]+', '', nextAgent['name'].lower())
            logging.info(cleanNextAgent)

            if jaro_winkler(cleanCurrAgent, cleanNextAgent) > 0.74:
                logging.info(jaro_winkler(cleanCurrAgent, cleanNextAgent))
                logging.info(agentID)
                logging.info('___OLD AGENT___')
                logging.info(agent)

                mergeAgents(currAgent, nextAgent)
                agent.remove(nextAgent)

                logging.info('___NEW AGENT___')
                logging.info(agent)

                count+=1

                if type == 'author':
                    logging.info(f'Deleted {count} duplicate work author(s)')
                    
                elif type == 'work contributor':
                    logging.info(f'Deleted {count} duplicate work contributor(s)')
                    
                elif type == 'edition contributor':
                    logging.info(f'Deleted {count} duplicate edition contributor(s)')

                else: 
                    logging.info(agent)
                    raise Exception
                
    return agent

def mergeAgents(existing, new):
    if 'viaf' in new.keys() and new['viaf'] != '':
        existing['viaf'] = new['viaf']

    if 'lcnaf' in new.keys() and new['lcnaf'] != '':
        existing['lcnaf'] = new['lcnaf']
    
    if 'primary' in new.keys() and new['primary'] != '':
            existing['primary'] = new['primary']

    if 'role' in new.keys():
        roleSet = set(existing['roles'])
        roleSet.add(new['role'])
        existing['roles'] = list(roleSet)
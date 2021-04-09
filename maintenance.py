import csv
from datetime import datetime
from elasticsearch_dsl import Search
import gzip
import json
from Levenshtein import jaro_winkler
import os
import re
from sqlalchemy import update, text, func
import yaml

from managers import DBManager, RabbitMQManager, ElasticsearchManager
from model import Record, Link, Work, Item, Rights
from model.postgres.item import ITEM_RIGHTS

def main():
    try:
        with open('./config/local-qa.yaml') as envStream:
            try:
                envDict = yaml.full_load(envStream)
            except yaml.YAMLError as err:
                print('Invalid! Please review')
                raise err

    except FileNotFoundError as err:
        print('Missing config YAML file! Check directory')
        raise err

    if envDict:
        for key, value in envDict.items():
            os.environ[key] = value


    manager = DBManager()

    manager.generateEngine()
    manager.createSession()

    esManager = ElasticsearchManager()
    esManager.createElasticConnection()

    cleanupWorks(manager)
    # removeDeletedWorksFromIndex(manager, esManager)
    # fixRightsData(manager)
    # deleteProblemRecord(manager, esManager, 'd5f84b61-8e01-4864-af66-98d43862a29f')
    # fixHathiTrustLCCNs(manager)
    # setOWINumbersForCatalogRecords(manager)
    # updateNYPLMediaTypes(manager)
    # sendOCLCLinksForProcessing(manager)
    # updateFlagJSON(manager)

def fixHathiTrustLCCNs(manager):
    total = manager.session.query(Record)\
        .filter(Record.source == 'hathitrust')\
        .filter(func.substring(Record.identifiers[func.array_length(Record.identifiers, 1)], 'isbn$') == 'isbn')\
        .count()

    print(total)

    updates = []
    for hathiRec in manager.session.query(Record)\
        .filter(Record.source == 'hathitrust')\
        .filter(func.substring(Record.identifiers[func.array_length(Record.identifiers, 1)], 'isbn$') == 'isbn')\
        .limit(1000000)\
        .yield_per(1000):
        print(hathiRec.source_id)

        recIdentifiers = hathiRec.identifiers
        lastID = recIdentifiers[-1:][0]

        if lastID and lastID[-4:] == 'isbn' and not re.search(r'[\dX]{10,13}', lastID):
            print('{} Actually LCCN'.format(lastID))
            lastID = lastID.replace('isbn', 'lccn')
            recIdentifiers[-1] = lastID

            hathiRec.identifiers = recIdentifiers
            updates.append(hathiRec)
            
            # manager.session.query(Record).filter(Record.id == hathiRec.id)\
            #    .update({'identifiers': recIdentifiers})
    
    manager.session.bulk_save_objects(updates)
    manager.session.commit()
            

def setOWINumbersForCatalogRecords(manager):
    for classifyRec in manager.session.query(Record)\
        .filter(Record.source == 'oclcClassify')\
        .all():

        owiID = classifyRec.source_id
        print(owiID)
        oclcNos = list(filter(lambda x: x[-4:] == 'oclc', classifyRec.identifiers))
        print(oclcNos)

        recUpdate = update(Record)\
            .where(Record.source_id.in_(oclcNos)).where(Record.date_modified < '2021-03-10T17:00:00')\
            .values(identifiers=text('array_append(identifiers, \'{}\')'.format(owiID)))

        manager.session.execute(recUpdate)
    manager.session.commit()
        
def updateNYPLMediaTypes(manager):
    nyplQuery = manager.session.query(Record).filter(Record.source == 'nypl').filter(Record.date_created >= datetime(2021, 3, 4, 0, 0, 0))

    recordUpdates = []
    for record in nyplQuery.yield_per(500):
        newParts = []
        print(record.source_id)
        for part in record.has_part:
            no, uri, source, mediaType, _ = tuple(part.split('|'))

            if mediaType == 'edd':
                newParts.append('|'.join([no, uri, source, 'application/html+edd', '{}']))
            elif mediaType == 'catalog':
                newParts.append('|'.join([no, uri, source, 'text/html', '{}']))
            else:
                newParts.append(part)
            
            record.has_part = newParts
            recordUpdates.append(record)

    manager.bulkSaveObjects(recordUpdates)
    manager.closeConnection()
        

def sendOCLCLinksForProcessing(manager):
    rabbitmq = RabbitMQManager()
    rabbitmq.createRabbitConnection()
    rabbitmq.createOrConnectQueue(os.environ['OCLC_QUEUE'], os.environ['OCLC_ROUTING_KEY'])

    oclcQuery = manager.session.query(Record)\
        .filter(Record.source == 'oclcCatalog')\
        .filter(Record.has_part != [])

    for record in oclcQuery.all():
        oclcID = tuple(record.source_id.split('|'))[0]
        if len(list(filter(lambda x: 'catalog.hathitrust' in x, record.has_part))):
            print('Skipping {}'.format(oclcID))
            continue 
        print('Pushing {}'.format(oclcID))
        rabbitmq.sendMessageToQueue(os.environ['OCLC_QUEUE'], os.environ['OCLC_ROUTING_KEY'], {'oclcNo': oclcID})


def updateFlagJSON(manager):
    for link in manager.session.query(Link).all():
        if isinstance(link.flags, str):
            link.flags = json.loads(link.flags)
            manager.session.add(link)

    manager.closeConnection()


def insertOLCovers(manager):
    insertRecords = []
    with gzip.open('../../../Downloads/ol_dump_coverids_2011-03-31.txt.gz', 'rt') as coverFile:
        coverReader = csv.reader(coverFile, delimiter='\t')
        for coverLine in coverReader:
            if coverLine[0] not in ['isbn', 'oclc', 'lccn']: continue

            newRecord = OpenLibraryCover(
                value=coverLine[1],
                name=coverLine[0],
                olid=(coverLine[2].split('/'))[-1],
                cover_id=coverLine[3]
            )

            insertRecords.append(newRecord)

            if len(insertRecords) % 10000 == 0:
                print('SAVING BATCH {}'.format(int(len(insertRecords) / 10000)))
                manager.bulkSaveObjects(insertRecords)
                insertRecords = []

    manager.bulkSaveObjects(insertRecords)
    manager.closeConnection()

def updateEpubPaths(manager):
    updatedRecords = []
    for rec in manager.session.query(Record).filter(Record.source == 'doab').all():
        newParts = []
        updated = False
        for part in rec.has_part:
            if 'meta-inf' in part:
                newParts.append(part.replace('meta-inf', 'META-INF'))
                updated = True
            else:
                newParts.append(part)

        if updated is True:
            print('Updating {}'.format(rec.source_id))
            rec.has_part = newParts
            updatedRecords.append(rec)

    manager.bulkSaveObjects(updatedRecords)
    manager.closeConnection()

def deleteProblemRecord(manager, esManager, uuid):
    manager.session.query(Work).filter(Work.uuid == uuid).delete()
    
    resp = Search(index=esManager.index).query('match', uuid=uuid)
    resp.delete()
    
    manager.session.commit()
    manager.session.close()

def removeDeletedWorksFromIndex(manager, esManager):
    allDocs = Search(index=esManager.index).query('match_all')

    for doc in allDocs.scan():
        work = manager.session.query(Work).filter(Work.uuid == doc.uuid).one_or_none()

        if work is None:
            print('DELETING {}'.format(doc))
            delDoc = Search(index=esManager.index).query('match', uuid=doc.uuid)
            delDoc.delete()


def fixRightsData(manager):
    rightsQuery = manager.session.query(Rights)\
        .join(ITEM_RIGHTS).join(Item)\
        .filter(Rights.source != 'hathitrust')\
        .filter(Item.source == 'hathitrust')

    rightsUpdates = []
    for rights in windowedQuery(Rights, rightsQuery, windowSize=1000):
        license = rights.source
        reason = rights.license
        statement = rights.rights_reason
        rDate = rights.rights_statement

        updateRights = {
            'id': rights.id,
            'source': 'hathitrust',
            'license': license,
            'rights_reason': reason,
            'rights_statement': statement,
            'rights_date': rDate
        }

        rightsUpdates.append(updateRights)

        if len(rightsUpdates) >= 1000:
            print('Committing Batch')
            manager.session.bulk_update_mappings(Rights, rightsUpdates)
            rightsUpdates = []
            manager.session.commit()

    manager.session.bulk_update_mappings(Rights, rightsUpdates)
    manager.session.commit()

    print('Fixing Gutenberg Records')
    gutenbergQuery = manager.session.query(Record).filter(Record.source == 'gutenberg')
    gutenbergUpdates = []
    for rec in windowedQuery(Record, gutenbergQuery, windowSize=1000):
        if rec.rights[:2] == '{"':
            rec.rights = rec.rights[2:-2]
            gutenbergUpdates.append(rec)

        if len(gutenbergUpdates) >= 1000:
            print('Committing Batch')
            manager.session.bulk_save_objects(gutenbergUpdates)
            gutenbergUpdates = []

    manager.session.bulk_save_objects(gutenbergUpdates)
    manager.session.commit()

    print('Fixing HathiTrust Records')
    hathiQuery = manager.session.query(Record).filter(Record.source == 'hathitrust')

    hathiUpdates = []
    for rec in windowedQuery(Record, hathiQuery, windowSize=1000):
        if rec.rights[:10] != 'hathitrust':
            rec.rights = 'hathitrust|{}'.format(rec.rights)
            hathiUpdates.append(rec)

        if len(hathiUpdates) >= 1000:
            print('Committing Batch')
            manager.session.bulk_save_objects(hathiUpdates)
            hathiUpdates = []
            manager.session.commit()

    manager.session.bulk_save_objects(hathiUpdates)
    manager.session.commit()
    manager.session.close()

def windowedQuery(table, query, windowSize=100):
    singleEntity = query.is_single_entity
    query = query.add_columns(table.id).order_by(table.id)

    lastID = None
    totalFetched = 0

    while True:
        subQuery = query

        if lastID is not None:
            subQuery = subQuery.filter(table.id > lastID)

        queryChunk = subQuery.limit(windowSize).all()
        totalFetched += windowSize

        if not queryChunk: break

        lastID = queryChunk[-1][-1]

        for row in queryChunk:
            yield row[0] if singleEntity else row[0:-1]


def cleanupWorks(manager):
    workUpdates = []
    workQuery = manager.session.query(Work).filter(Work.date_created > datetime(2021, 3, 29))
    for work in windowedQuery(Work, workQuery):
        updateFlag = False
        newAuthors = agentParser(work.authors)
        if work.authors != newAuthors:
            print(work.authors, newAuthors)
            work.authors = newAuthors
            updateFlag = True

        newContribs = agentParser(work.contributors)
        if newContribs != work.contributors:
            print(work.contributors, newContribs)
            work.contributors = newContribs
            updateFlag = True

        newSubjects = subjectParser(work.subjects)
        if newSubjects != work.subjects:
            print(work.subjects, newSubjects)
            work.subjects = newSubjects
            updateFlag = True

        newLangs = list(filter(None, work.languages))
        if len(newLangs) != len(work.languages):
            print(work.languages, newLangs)
            work.languages = newLangs
            updateFlag = True

        for ed in work.editions:
            newLangs = list(filter(None, ed.languages))
            if len(newLangs) != len(ed.languages):
                print('EDITION', ed.languages, newLangs)
                ed.languages = newLangs
                workUpdates.append(ed)

        if updateFlag is True:
            print(work.title)
            workUpdates.append(work)

        if len(workUpdates) >= 100:
            print('Committing Batch')
            manager.session.bulk_save_objects(workUpdates)
            workUpdates = []
            manager.session.commit()

    manager.session.bulk_save_objects(workUpdates)
    workUpdates = []
    manager.session.commit()
    manager.session.close()


def agentParser(agents):
    outAgents = {}

    for rec in agents:
        recKey = re.sub(r'[.,:\(\)]+', '', rec['name'].lower())

        if rec['name'] == '' and rec['viaf'] == '' and rec['lcnaf'] == '':
            continue
        
        existingMatch = False
        for oaKey, oa in outAgents.items():
            for checkField in ['viaf', 'lcnaf']:
                if rec[checkField] and rec[checkField] != '' and rec[checkField] == oa[checkField]:
                    existingMatch = True
                    mergeAgents(oa, rec)
                    break

            if existingMatch is False:
                if jaro_winkler(oaKey, recKey) > 0.9:
                    mergeAgents(oa, rec)
                    existingMatch = True
                    break

        if existingMatch is False:
            if 'role' in rec.keys():
                rec['roles'] = list(set([rec['role']]))
                del rec['role']
            outAgents[recKey] = rec

    return [a for _, a in outAgents.items()]


def subjectParser(subjects):
    cleanSubjects = {}
    for subj in subjects:
        heading = subj['heading']
        auth = subj['authority']
        authNo = subj['controlNo']

        if heading == '': continue

        cleanHeading = heading.strip(',.')
        headingKey = cleanHeading.lower()

        if headingKey in cleanSubjects.keys():
            if cleanSubjects[headingKey]['authority'] == '' and auth != '':
                cleanSubjects[headingKey]['authority'] = auth
                cleanSubjects[headingKey]['controlNo'] = authNo
        else:
            cleanSubjects[headingKey] = {
                'heading': cleanHeading,
                'authority': auth,
                'controlNo': authNo
            }

    return [s for _, s in cleanSubjects.items()]


def mergeAgents(existing, new):
        if new['viaf'] != '':
            existing['viaf'] = new['viaf']

        if new['lcnaf'] != '':
            existing['lcnaf'] = new['lcnaf']

        if 'role' in new.keys():
            roleSet = set(existing['roles'])
            roleSet.add(new['role'])
            existing['roles'] = list(roleSet)


if __name__ == '__main__':
    main()

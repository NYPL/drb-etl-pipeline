import os
import re

from model import Work, Item, Edition, ESWork
from main import loadEnvFile
from managers import DBManager, ElasticsearchManager


def main():
    '''
    Updating NYPL catalog records with new link to replace text/html link
    '''

    loadEnvFile('local-qa', fileString='config/{}.yaml')

    dbManager = DBManager(
        user=os.environ.get('POSTGRES_USER', None),
        pswd=os.environ.get('POSTGRES_PSWD', None),
        host=os.environ.get('POSTGRES_HOST', None),
        port=os.environ.get('POSTGRES_PORT', None),
        db=os.environ.get('POSTGRES_NAME', None)
    )

    esManager = ElasticsearchManager()
    esManager.createElasticConnection()

    dbManager.generateEngine()

    dbManager.createSession()

    catalogLinkQuery = dbManager.session.query(Work) \
        .join(Edition)\
        .join(Item)\
        .filter(Item.source == 'nypl')

    for work in catalogLinkQuery.all():
        workEdFormats = {}
        print(work.uuid)
        for edition in work.editions:
            workEdFormats[edition.id] = getEditionFormats(edition.items)

        workRec = ESWork.get(work.uuid, index=esManager.index)
        saveWork = False

        for edition in workRec.editions:
            if edition.formats != workEdFormats[edition.edition_id]:
                print('REPLACE')
                edition.formats = workEdFormats[edition.edition_id]
                saveWork = True
            else:
                print('SKIP')
        
        if saveWork:
            workRec.save()

    dbManager.closeConnection()


def getEditionFormats(items):
    formats = set()

    for item in items:
        links = [(l.media_type, l.flags) for l in item.links]
        htmlReadable = linkCriteriaChecker(item.links, 'catalog', False)
        htmlCatalog = linkCriteriaChecker(item.links, 'catalog', True)

        if htmlReadable and htmlCatalog:
            formats.add('text/html')
            formats.add('application/html+catalog')
        elif htmlReadable:
            formats.add('text/html')
        elif htmlCatalog:
            formats.add('application/html+catalog')

        for link in links:
            if link[0] not in ['text/html', 'application/html+catalog']:
                formats.add(link[0])

    return list(formats) if len(formats) > 0 else None


def linkCriteriaChecker(links, flag, value):
    return len(list(filter(lambda x: x.flags[flag] == value and x.media_type == 'text/html', links))) > 0


if __name__ == '__main__':
    main()
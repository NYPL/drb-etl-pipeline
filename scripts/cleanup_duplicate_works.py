import os
from elasticsearch.exceptions import NotFoundError

from managers import DBManager, ElasticsearchManager
from model import Work


TITLES = [
    'Thoughts and things at home and abroad. By Elihu Burritt ... With a memoir, by Mary Howitt',
    'Legends of the sea. 39 men for one woman: an episode of the colonization of Canada. Tr. from the French of H. Émile Chevalier, by E. I. Sears'
]
BATCH_SIZE = 100

def main():
    db_manager = DBManager()
    es_manager = ElasticsearchManager()

    db_manager.createSession()
    es_manager.createElasticConnection()

    for title in TITLES:
        print(f'Deleting duplicate works with title: {title}')

        works = (
            db_manager.session.query(Work)
                .filter(Work.title == title)
                .order_by(Work.date_created.desc())
                .yield_per(100)
        )

        first_work = True
        number_of_works_deleted = 0
        
        for work in works:
            if first_work:
                first_work = False
                continue

            db_manager.session.delete(work)
            
            try:
                es_manager.client.delete(
                    index=os.environ['ELASTICSEARCH_INDEX'],
                    id=str(work.uuid)
                )
            except NotFoundError: 
                print(f'No work document found for work uuid {work.uuid}')

            if number_of_works_deleted % BATCH_SIZE == 0:
                db_manager.session.commit()

        db_manager.session.commit()

    db_manager.close_connection()

if __name__ == '__main__':
    main()

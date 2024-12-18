import os
from sqlalchemy import delete

from managers import DBManager, ElasticsearchManager
from model import Work


TITLES = [
    'Thoughts and things at home and abroad. By Elihu Burritt ... With a memoir, by Mary Howitt',
    'Legends of the sea. 39 men for one woman: an episode of the colonization of Canada. Tr. from the French of H. Émile Chevalier, by E. I. Sears'
]

def main():
    db_manager = DBManager()
    es_manager = ElasticsearchManager()

    db_manager.createSession()
    es_manager.createElasticConnection()

    for title in TITLES:
        work_uuids = (
            db_manager.session.query(Work.uuid)
                .filter(Work.title == title)
                .order_by(Work.date_created.desc())
                .all()
        )

        work_uuids = [uuid[0] for uuid in work_uuids]

        for work_uuid in work_uuids[1:]:
            delete_work = delete(Work).where(Work.uuid == work_uuid)

            db_manager.session.execute(delete_work)
            
            es_manager.client.delete(
                index=os.environ['ELASTICSEARCH_INDEX'],
                id=str(work_uuid)
            )

        db_manager.session.commit()

    db_manager.close_connection()

if __name__ == '__main__':
    main()

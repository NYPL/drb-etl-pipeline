from datetime import datetime, timedelta, date
from sqlalchemy.orm import joinedload, sessionmaker
from sqlalchemy.sql import text
from uuid import uuid4

from model import Work, Edition, Link, Item, Record, Collection
from .utils import APIUtils


class DBClient():
    def __init__(self, engine):
        self.engine = engine

    def createSession(self):
        self.session = sessionmaker(bind=self.engine)()

    def closeSession(self):
        self.session.close()

    def fetchSearchedWorks(self, ids):
        uuids = [i[0] for i in ids]
        editionIds = list(set(APIUtils.flatten([i[1] for i in ids])))

        return self.session.query(Work)\
            .join(Edition)\
            .options(
                joinedload(Work.editions, Edition.links),
                joinedload(Work.editions, Edition.items),
                joinedload(
                    Work.editions, Edition.items, Item.links, innerjoin=True
                ),
                joinedload(Work.editions, Edition.items, Item.rights),
            )\
            .filter(Work.uuid.in_(uuids), Edition.id.in_(editionIds))\
            .all()

    def fetchSingleWork(self, uuid):
        return self.session.query(Work)\
            .options(
                joinedload(Work.editions),
                joinedload(Work.editions, Edition.rights),
                joinedload(Work.editions, Edition.items),
                joinedload(
                    Work.editions, Edition.items, Item.links, innerjoin=True
                )
            )\
            .filter(Work.uuid == uuid).first()

    def fetchSingleEdition(self, editionID, showAll=False):
        return self.session.query(Edition)\
            .options(
                joinedload(Edition.links),
                joinedload(Edition.items),
                joinedload(Edition.items, Item.links),
                joinedload(Edition.items, Item.rights)
            )\
            .filter(Edition.id == editionID).first()

    def fetchSingleLink(self, linkID):
        return self.session.query(Link).filter(Link.id == linkID).first()

    def fetchRecordsByUUID(self, uuids):
        return self.session.query(Record).filter(Record.uuid.in_(uuids)).all()

    def fetchRowCounts(self):
        countQuery = text("""SELECT relname AS table, reltuples AS row_count
            FROM pg_class c JOIN pg_namespace n ON (n.oid = c.relnamespace)
            WHERE nspname NOT IN ('pg_catalog', 'information_schema')
            AND relkind = 'r'
            AND relname IN ('records', 'works', 'editions', 'items', 'links')
        """)

        return self.session.execute(countQuery)

    def fetchNewWorks(self, page=0, size=50):
        offset = page * size

        createdSince = datetime.utcnow() - timedelta(days=1)

        baseQuery = self.session.query(Work)\
            .filter(Work.date_created >= createdSince)

        return (baseQuery.count(), baseQuery.offset(offset).limit(size).all())

    def fetchSingleCollection(self, uuid):
        return self.session.query(Collection)\
            .options(joinedload(Collection.editions))\
            .filter(Collection.uuid == uuid).first()

    def createCollection(
        self, title, creator, description, workUUIDs=[], editionIDs=[]
    ):
        newCollection = Collection(
            uuid=uuid4(),
            title=title,
            creator=creator,
            description=description
        )

        collectionEditions = []
        if len(workUUIDs) > 0:
            collectionWorks = self.session.query(Work)\
                .join(Work.editions)\
                .filter(Work.uuid.in_(workUUIDs))\
                .all()

            for work in collectionWorks:
                editions = list(sorted(
                    [ed for ed in work.editions],
                    key=lambda x: x.publication_date
                    if x.publication_date else date.today()
                ))

                for edition in editions:
                    if len(edition.items) > 0:
                        collectionEditions.append(edition)
                        break

        if len(editionIDs) > 0:
            collectionEditions.extend(
                self.session.query(Edition)
                .filter(Edition.id.in_(editionIDs))
                .all()
            )

        newCollection.editions = collectionEditions

        self.session.add(newCollection)

        return newCollection

    def deleteCollection(self, uuid):
        return self.session.query(Collection)\
            .filter(Collection.uuid == uuid).delete()

from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload, contains_eager, sessionmaker
from sqlalchemy.sql import text

from model import Work, Edition, Link, Item, Record
from .utils import APIUtils

class DBClient():
    def __init__(self, engine):
        self.engine = engine

    def fetchSearchedWorks(self, ids):
        uuids = [i[0] for i in ids]
        editionIds = list(set(APIUtils.flatten([i[1] for i in ids])))

        session = sessionmaker(bind=self.engine)()

        return session.query(Work)\
            .join(Edition)\
            .options(
                contains_eager(Work.editions),
                joinedload(Work.editions, Edition.links),
                joinedload(Work.editions, Edition.rights),
                joinedload(Work.editions, Edition.items),
                joinedload(Work.editions, Edition.items, Item.links, innerjoin=True)
            )\
            .filter(Work.uuid.in_(uuids), Edition.id.in_(editionIds))\
            .all()

    def fetchSingleWork(self, uuid):
        session = sessionmaker(bind=self.engine)()

        return session.query(Work)\
            .options(
                joinedload(Work.editions),
                joinedload(Work.editions, Edition.rights),
                joinedload(Work.editions, Edition.items),
                joinedload(Work.editions, Edition.items, Item.links, innerjoin=True)
            )\
            .filter(Work.uuid == uuid).first()

    def fetchSingleEdition(self, editionID, showAll=False):
        session = sessionmaker(bind=self.engine)()

        return session.query(Edition)\
            .options(
                joinedload(Edition.links),
                joinedload(Edition.rights)
            )\
            .filter(Edition.id == editionID).first()

    def fetchSingleLink(self, linkID):
        session = sessionmaker(bind=self.engine)()

        return session.query(Link)\
            .options(joinedload(Link.items, Item.edition, Edition.work))\
            .filter(Link.id == linkID).first()

    def fetchRecordsByUUID(self, uuids):
        session = sessionmaker(bind=self.engine)()

        return session.query(Record).filter(Record.uuid.in_(uuids)).all()

    def fetchRowCounts(self):
        session = sessionmaker(bind=self.engine)()

        countQuery = text("""SELECT relname AS table, reltuples AS row_count
            FROM pg_class c JOIN pg_namespace n ON (n.oid = c.relnamespace)
            WHERE nspname NOT IN ('pg_catalog', 'information_schema')
            AND relkind = 'r'
            AND relname IN ('records', 'works', 'editions', 'items', 'links')
        """)

        return session.execute(countQuery)

    def fetchNewWorks(self, page=0, size=50):
        session = sessionmaker(bind=self.engine)()

        offset = page * size

        createdSince = datetime.utcnow() - timedelta(days=1)

        baseQuery = session.query(Work).filter(Work.date_created >= createdSince)

        return (baseQuery.count(), baseQuery.offset(offset).limit(size).all())

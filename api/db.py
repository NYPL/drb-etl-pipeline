from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text

from model import Work, Edition, Link
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
            .filter(Work.uuid.in_(uuids), Edition.id.in_(editionIds))\
            .all()

    def fetchSingleWork(self, uuid):
        session = sessionmaker(bind=self.engine)()

        return session.query(Work).filter(Work.uuid == uuid).first()

    def fetchSingleEdition(self, editionID, showAll=False):
        session = sessionmaker(bind=self.engine)()

        return session.query(Edition).filter(Edition.id == editionID).first()

    def fetchSingleLink(self, linkID):
        session = sessionmaker(bind=self.engine)()

        return session.query(Link).filter(Link.id == linkID).first()

    def fetchRowCounts(self):
        session = sessionmaker(bind=self.engine)()

        countQuery = text("""SELECT relname AS table, reltuples AS row_count
            FROM pg_class c JOIN pg_namespace n ON (n.oid = c.relnamespace)
            WHERE nspname NOT IN ('pg_catalog', 'information_schema')
            AND relkind = 'r'
            AND relname IN ('records', 'works', 'editions', 'items', 'links')
        """)

        return session.execute(countQuery)

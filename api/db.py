from sqlalchemy.orm import sessionmaker

from model import Work, Edition, Item, Link, Rights, Identifier
from model.postgres.item import ITEM_LINKS
from .utils import APIUtils

class DBClient():
    def __init__(self, engine):
        self.engine = engine

    def fetchSearchedWorks(self, ids):
        uuids = [i[0] for i in ids]
        editionIds = list(set(APIUtils.flatten([i[1] for i in ids])))

        session = sessionmaker(bind=self.engine)()

        query = session.query(Work)\
            .join(Edition)\
            .join(Item, ITEM_LINKS, Link)\
            .filter(Work.uuid.in_(uuids), Edition.id.in_(editionIds))

        return query.all()

    def fetchSingleWork(self, uuid):
        session = sessionmaker(bind=self.engine)()

        return session.query(Work)\
            .join(Edition)\
            .join(Item, ITEM_LINKS, Link)\
            .filter(Work.uuid == uuid).first()

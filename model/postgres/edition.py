from sqlalchemy import Date, Unicode, Integer, Column, Table, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, ARRAY, UUID
from sqlalchemy.orm import relationship

from .base import Base, Core

EDITION_IDENTIFIERS = Table('edition_identifiers', Base.metadata,
    Column('edition_id', Integer, ForeignKey('editions.id')),
    Column('identifier_id', Integer, ForeignKey('identifiers.id'))
)

EDITION_LINKS = Table('edition_links', Base.metadata,
    Column('edition_id', Integer, ForeignKey('editions.id')),
    Column('link_id', Integer, ForeignKey('links.id'))
)

EDITION_RIGHTS = Table('edition_rights', Base.metadata,
    Column('edition_id', Integer, ForeignKey('editions.id')),
    Column('rights_id', Integer, ForeignKey('rights.id'))
)

class Edition(Base, Core):
    __tablename__ = 'editions'

    id = Column(Integer, primary_key=True)
    title = Column(Unicode)
    sub_title = Column(Unicode)
    alt_titles = Column(ARRAY(Unicode, dimensions=1))
    edition = Column(Integer)
    edition_statement = Column(Unicode)
    publication_place = Column(Unicode)
    publication_date = Column(Date)
    volume = Column(Unicode)
    table_of_contents = Column(Unicode)
    extent = Column(Unicode)
    summary = Column(Unicode)
    publishers = Column(JSONB)
    contributors = Column(JSONB)
    dates = Column(JSONB)
    measurements = Column(JSONB)
    languages = Column(JSONB)
    dcdw_uuids = Column(ARRAY(UUID, dimensions=1))

    work_id = Column(Integer, ForeignKey('works.id'))
    items = relationship('Item', backref='edition', cascade='all, delete-orphan')

    identifiers = relationship('Identifier', secondary=EDITION_IDENTIFIERS, backref='editions')
    links = relationship('Link', secondary=EDITION_LINKS, backref='editions')
    rights = relationship('Rights', secondary=EDITION_RIGHTS, backref='editions')

    def __repr__(self):
        return '<Edition(place={}, date={}, publisher={})>'.format(
            self.publication_place, self.publication_date, self.publishers
        )
    
    def __dir__(self):
        return [
            'title', 'sub_title', 'alt_titles', 'edition', 'edition_statement',
            'publication_place', 'publication_date', 'volume', 'table_of_contents',
            'extent', 'summary', 'publishers', 'contributors', 'dates',
            'measurements', 'languages'
        ]
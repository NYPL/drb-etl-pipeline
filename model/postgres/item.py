from sqlalchemy import DateTime, Unicode, Integer, Column, Table, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, ARRAY, UUID
from sqlalchemy.orm import relationship

from .base import Base, Core

ITEM_IDENTIFIERS = Table('item_identifiers', Base.metadata,
    Column('item_id', Integer, ForeignKey('items.id')),
    Column('identifier_id', Integer, ForeignKey('identifiers.id'))
)

ITEM_LINKS = Table('item_links', Base.metadata,
    Column('item_id', Integer, ForeignKey('items.id')),
    Column('link_id', Integer, ForeignKey('links.id'))
)

ITEM_RIGHTS = Table('item_rights', Base.metadata,
    Column('item_id', Integer, ForeignKey('items.id')),
    Column('rights_id', Integer, ForeignKey('rights.id'))
)

class Item(Base, Core):
    __tablename__ = 'items'

    id = Column(Integer, primary_key=True)
    source = Column(Unicode, nullable=False, index=True)
    content_type = Column(Unicode)
    contributors = Column(JSONB)
    modified = Column(DateTime)
    drm = Column(Unicode)
    measurements = Column(JSONB)

    edition_id = Column(Integer, ForeignKey('editions.id'))

    identifiers = relationship('Identifier', secondary=ITEM_IDENTIFIERS, backref='items')
    links = relationship('Link', secondary=ITEM_LINKS, backref='items')
    rights = relationship('Rights', secondary=ITEM_RIGHTS, backref='items')

    def __repr__(self):
        return '<Item(source={}, content_type={})>'.format(
            self.source, self.content_type
        )

    def __dir__(self):
        return [
            'source', 'content_type', 'contributors', 'modified', 'drm',
            'measurements'
        ]

from sqlalchemy import Unicode, Integer, Column, Table, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base, Core

COLLECTION_EDITIONS = Table(
    'collection_editions', Base.metadata,
    Column(
        'collection_id',
        Integer,
        ForeignKey('collections.id', ondelete='CASCADE')
    ),
    Column(
        'edition_id',
        Integer,
        ForeignKey('editions.id', ondelete='CASCADE')
    )
)


class Collection(Base, Core):
    __tablename__ = 'collections'

    id = Column(Integer, primary_key=True)
    uuid = Column(UUID(as_uuid=True), index=True)
    title = Column(Unicode, index=True)
    creator = Column(Unicode, index=True)
    description = Column(Unicode)

    editions = relationship(
        'Edition',
        secondary=COLLECTION_EDITIONS,
        backref='collections',
        cascade='all, delete'
    )

    def __repr__(self):
        return '<Collection(uuid={}, title={}, creator={}, items={})>'.format(
            self.uuid, self.title, self.creator, len(self.editions)
        )

    def __dir__(self):
        return ['uuid', 'title', 'creator']

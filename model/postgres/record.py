from datetime import datetime
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Unicode,
    Table,
    Boolean,
    Index
)
from sqlalchemy.dialects.postgresql import JSON, ARRAY, UUID, ENUM

from .base import Base, Core


class Record(Base, Core):
    __tablename__ = 'records'
    id = Column(Integer, primary_key=True)
    uuid = Column(UUID(as_uuid=True), nullable=False, index=True)
    frbr_status = Column(
        Unicode,
        ENUM('to_do', 'in_progress', 'complete', name='status_enum', create_type=False),
        nullable=False,
        index=True
    )
    cluster_status = Column(Boolean, default=False, nullable=False, index=True)
    source = Column(Unicode, index=True) # dc:source, Non-Repeating
    source_id = Column(Unicode, index=True) # dc:identifier, Non-Repeating
    title = Column(Unicode) # dc:title, Non-Repeating
    alternative = Column(ARRAY(Unicode, dimensions=1)) # dc:alternative, Repeating
    medium = Column(Unicode) # dc:medium, Non-Repeating
    is_part_of = Column(Unicode) # dc:isPartOf, Repeating, Format "string|int|type"
    subjects = Column(ARRAY(Unicode, dimensions=1)) # dc:subject, Repeating, Format "string|authority|controlno"
    authors = Column(ARRAY(Unicode, dimensions=1)) # dc:creator, Repeating, Format "string|viaf|lcnaf|primary"
    contributors = Column(ARRAY(Unicode, dimensions=1)) # dc:contributor, Repeating, Format "string|viaf|lcnaf|role"
    languages = Column(ARRAY(Unicode, dimensions=1)) # dc:language, Repeating, Format "string|iso_2|iso_3"
    dates = Column(ARRAY(Unicode, dimensions=1)) # dc:date, Repeating, Format "string|type"
    rights = Column(Unicode) # dc:rights, Non-Repeating, Format "license|reason|statement|date"
    identifiers = Column(ARRAY(Unicode, dimensions=1)) # dc:identifier, Format "string|authority"
    date_submitted = Column(DateTime) # dc:dateSubmitted, Non-Repeating
    requires = Column(ARRAY(Unicode, dimensions=1)) # dc:requires, Repeating, Format "value|type"
    spatial = Column(Unicode) # dc:spatial, Non-Repeating
    publisher = Column(Unicode) # dc:publisher, Repeating, Format "name|viaf|lcnaf"
    has_version = Column(Unicode) # dc:hasVersion, Non-Repeating, Format "string|edition_no"
    table_of_contents = Column(Unicode) # dc:tableOfContents, Non-Repeating
    extent = Column(Unicode) # dc:extent, Non-Repeating
    abstract = Column(Unicode) # dc:abstract, Non-Repeating
    has_part = Column(ARRAY(Unicode, dimensions=1)) # dc:hasPart, Repeating, Format "itemNo|uri|source|type|flags"
    coverage = Column(ARRAY(Unicode, dimensions=1)) # dc:coverage, non-Repeating, Format "locationCode|locationName|itemNo"

    # edition_id = Column(Integer, ForeignKey('editions.id'))

    __tableargs__ = (Index('ix_record_identifiers', identifiers, postgresql_using="gin"))

    def __repr__(self):
        return '<Record(title={}, uuid={}, authors={})>'.format(
            self.title, self.uuid, self.authors
        )
    
    def __dir__(self):
        return ['uuid', 'frbr_status', 'cluster_status', 'source', 'source_id',
            'title', 'alternative', 'medium', 'is_part_of', 'subjects', 'authors',
            'contributors', 'languages', 'dates', 'rights', 'identifiers',
            'date_submitted', 'requires', 'spatial', 'publisher', 'has_version',
            'table_of_contents', 'extent', 'abstract', 'has_part', 'coverage'
        ]
    
    def __iter__(self):
        for attr in dir(self):
            yield attr, getattr(self, attr)

from datetime import datetime
from sqlalchemy import Column, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Core(object):
    """A mixin for other SQLAlchemy ORM classes. Includes a date_craeted and
    date_updated field for all database tables."""
    date_created = Column(
        DateTime,
        default=datetime.utcnow(),
        index=True
    )

    date_modified = Column(
        DateTime,
        default=datetime.utcnow(),
        onupdate=datetime.utcnow(),
        index=True
    )

    def __iter__(self):
        for key in dir(self):
            yield (key, getattr(self, key))
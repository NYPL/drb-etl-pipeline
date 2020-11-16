from datetime import datetime
from string import Formatter
from uuid import uuid4

from .abstractMapping import AbstractMapping
from model import Record


class Core(AbstractMapping):
    def __init__(self, source, statics):
        self.mapping = {}
        self.source = source
        self.record = None
        self.staticValues = statics

        self.formatter = CustomFormatter()

    def initEmptyRecord(self):
        return Record(
            uuid=uuid4(),
            date_created=datetime.utcnow(),
            date_modified=datetime.utcnow(),
            frbr_status='to_do',
            cluster_status=False
        )

    def applyMapping(self):
        return self.initEmptyRecord()

    def applyFormatting(self):
        return self.record

    def updateExisting(self, existing):
        for attr, value in self.record:
            if attr == 'uuid': continue
            setattr(existing, attr, value)
        
        existing.frbr_status = 'to_do'
        existing.cluster_status = False


class CustomFormatter(Formatter):
    def __init__(self):
        super().__init__()
    
    def get_value(self, key, args, kwargs):
        if isinstance(key, str) or str(key) in kwargs.keys():
            return kwargs.get(key, '')
        
        try:
            return args[key]
        except IndexError:
            return ''

    def check_unused_args(self, used_args, args, kwargs):
        if len(args) > 0\
            and len(list(filter(lambda x: x != '', args))) == 0:
            raise IndexError

        usedKeys = used_args & {key for key in kwargs.keys()}
        if len(kwargs.keys()) > 0\
            and len(list(filter(lambda x: kwargs[x] != '', list(usedKeys)))) == 0:
            raise KeyError
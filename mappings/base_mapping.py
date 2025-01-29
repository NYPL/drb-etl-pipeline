from datetime import datetime, timezone
from string import Formatter
from uuid import uuid4

from .record_mapping import RecordMapping
from model import Record


class BaseMapping(RecordMapping):
    def __init__(self, source, constants):
        self.mapping = {}
        self.source = source
        self.record = None
        self.constants = constants

        self.formatter = CustomFormatter()

    def initEmptyRecord(self):
        return Record(
            uuid=uuid4(),
            date_created=datetime.now(timezone.utc).replace(tzinfo=None),
            date_modified=datetime.now(timezone.utc).replace(tzinfo=None),
            frbr_status='to_do',
            cluster_status=False
        )

    def applyMapping(self):
        return self.initEmptyRecord()

    def applyFormatting(self):
        return self.record
    
    def format_identifiers(self, identifiers):
        for index, identifier in enumerate(identifiers):
            count_digits = 0
            if '/' not in identifier:
                for char in identifier:
                    if char.isdigit():
                        count_digits += 1
                if count_digits == 8:
                    identifiers[index] = f'{identifier}|issn'
                if count_digits == 10 or count_digits == 13:
                    identifiers[index] = f'{identifier}|isbn'
            else:
                identifiers[index] = f'{identifier}|clacso'
        return identifiers

    def updateExisting(self, existing):
        for attr, value in self.record:
            if attr == 'uuid': continue
            setattr(existing, attr, value)
        
        existing.cluster_status = False
        if existing.source not in ['oclcClassify', 'oclcCatalog']:
            existing.frbr_status = 'to_do'

    def raiseMappingError(self, message):
        raise MappingError(message)


class MappingError(Exception):
    def __init__(self, message):
        self.message = message


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
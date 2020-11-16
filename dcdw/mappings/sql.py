from datetime import datetime
from string import Formatter

from .core import Core


class SQLMapping(Core):
    def __init__(self, source, statics):
        super().__init__(source, statics)
    
    def applyMapping(self):
        newRecord = self.initEmptyRecord()

        for field, structure in self.mapping.items():
            if isinstance(structure, tuple):
                sourceValue = self.source.get(structure[0], None)
                fieldData = self.getFieldData(sourceValue, structure[1])
            else:
                fieldData = list(filter(None, [
                    self.getFieldData(self.source.get(s[0], None), s[1])
                    for s in structure
                ]))
                
            setattr(newRecord, field, fieldData)

        self.record = newRecord
        self.applyFormatting()
    
    def getFieldData(self, sourceValue, structure):
        if isinstance(sourceValue, list):
            return [self.getFieldData(s, structure) for s in sourceValue]
        elif isinstance(sourceValue, dict):
            try:
                return self.formatter.format(structure, **sourceValue)
            except KeyError:
                pass
            except IndexError:
                print(structure, sourceValue)
                raise IndexError
            except TypeError as err:
                print(structure, sourceValue)
                for key, value in sourceValue.items():
                    print(key, value, type(value))
                raise err
        elif sourceValue != None:
            try:
                return self.formatter.format(structure, sourceValue)
            except IndexError:
                pass
    

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
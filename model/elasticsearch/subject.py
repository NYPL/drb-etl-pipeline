from elasticsearch_dsl import Keyword, Text


from .base import BaseInner, plain_ascii

class Subject(BaseInner):
    authority = Keyword()
    control_number = Keyword()
    subject = Text(analyzer=plain_ascii, fields={'keyword': Keyword()})

    @classmethod
    def getFields(cls):
        return ['uri', 'authority', 'subject']
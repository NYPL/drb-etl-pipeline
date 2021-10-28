from elasticsearch_dsl import Keyword

from .base import BaseInner, PerLanguageField


class Subject(BaseInner):
    authority = Keyword()
    control_number = Keyword()
    subject = PerLanguageField()

    @classmethod
    def getFields(cls):
        return ['uri', 'authority', 'subject']
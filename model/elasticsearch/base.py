from elasticsearch_dsl import InnerDoc, Document, Date, analyzer


plain_ascii = analyzer(
    'plain_ascii',
    tokenizer='standard',
    filter=['lowercase', 'stop', 'asciifolding']
)


class BaseDoc(Document):
    date_created = Date()
    date_modified = Date()

    def save(self, **kwargs):
        for rel in dir(self):
            if isinstance(getattr(self, rel), set):
                setattr(self, rel, list(getattr(self, rel)))
        return super().save(**kwargs)


class BaseInner(InnerDoc):
    date_created = Date()
    date_modified = Date()

    def save(self, **kwargs):
        for rel in dir(self):
            if isinstance(getattr(self, rel), set):
                setattr(self, rel, list(getattr(self, rel)))
        return super().save(**kwargs)
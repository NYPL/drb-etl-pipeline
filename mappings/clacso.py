from .json import JSONMapping

class CLACSOMapping(JSONMapping):
    def __init__(self, source):
        super().__init__(source, {})
        self.mapping = self.createMapping()
    
    def createMapping(self):
        return {
            'title': ('title', '{0}'),
            'authors': ('authors', '{0}|||true'),
            'abstract': ('description', '{0}'),
            'dates': [('publication_date', '{0}|publication_date')],
            'identifiers': 
                [('isbn', '{0}|isbn')]
            ,
            'spatial': ('edition_location', '{0}'),
            'has_part': [('url', '1|{0}|clacso|application/pdf|{{"catalog": false, "download": true, "reader": false, "embed": false}}')] 
        }

    def applyFormatting(self):
        self.record.source = 'clacso'
        self.record.source_id = f'{self.record.source}'

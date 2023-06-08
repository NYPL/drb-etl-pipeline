from .json import JSONMapping

class UofSCMapping(JSONMapping):
    def __init__(self, source):
        super().__init__(source, {})
        self.mapping = self.createMapping()
    

    def createMapping(self):
        return {
            'title': ('title', '{0}'),
            'authors': [('authors', '{0}|||true')],
            'dates': [('publicationDate', '{0}|publication_date')],
            'publisher': [('publisher', '{0}')],
            'spatial': ('publisherLocation', '{0}|publisherLocation'),
            'identifiers': 
                [('isbn', '{0}|isbn')]
            ,
            'subjects': [('subject', '{0}||')],
            'has_part': [('pdf_link', '1|{0}|UofSC|application/pdf|{{"catalog": false, "download": true, "reader": false, "embed": false}}')] 
        }

    def applyFormatting(self):
        self.record.source = 'UofSC'

        source_id = self.record.identifiers[0].split('|')[0]
        self.record.source_id = f'UofSC_{source_id}'
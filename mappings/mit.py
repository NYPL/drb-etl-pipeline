from .json import JSONMapping

class MITMapping(JSONMapping):
    def __init__(self, source):
        super().__init__(source, {})
        self.mapping = self.createMapping()
    
    def createMapping(self):
        return {
            'title': ('title', '{0}'),
            'authors': [('titleauthorname', '{0}|||true')],
            'dates': [('pubDate', '{0}|publication_date')],
            'publisher': [('publisher', '{0}')],
            'identifiers': 
            [
                ('identifier', '{0}'),
                ('hcIsbn', '{0}|isbn'),
                ('pbIsbn', '{0}|isbn')
            ],
            'has_part': [('url', '1|{0}|mit|application/pdf|{{"catalog": false, "download": true, "reader": false, "embed": false}}')] 
        }

    def applyFormatting(self):
        self.record.source = 'mit'
        self.record.source_id = f'mit_{self.record.identifiers[0]}'
        self.record.spatial = 'Massachusetts'
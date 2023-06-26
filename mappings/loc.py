from .json import JSONMapping

class LOCMapping(JSONMapping):
    def __init__(self, source):
        super().__init__(source, {})
        self.mapping = self.createMapping()
    
    def createMapping(self):
        return {
            'title': ('title', '{0}'),
            'alternate': [('other_title', '{0}')], #One other_title in items block and one outside of it 
            'medium': [('medium', '{0}')],
            'authors': [('contributor', '{0}|||true')],
            'languages': [('language', '{0}||')],
            'dates': [('dates', '{0}|publication_date')], #Apply formatting because dates in a list
            'publisher': [('created_published', '{0}')],
            'identifiers': [
                ('number_lccn', '{0}|loc'),
                ('call_number', '{0}|callNumber'),
            ],
            'contributors': [
                ('contributors', '{0}|||contributor'),
            ],
            'extent': [('medium', '{0}')],
            'is_part_of': [('partof', '{0}|collection')],
            'spatial': ('created_published', '{0}'),#publisherLocation to be in apply formatting
            'abstract': [
                ('description', '{0}')
            ],
            'subjects': [('subjects', '{0}||')],
            'rights': (['rights_advisory', 'copyra', 'copyri'], 'met|{0}|{1}|{2}|'),
            'has_part': [('pdf', '1|{0}|loc|application/pdf|{{"catalog": false, "download": true, "reader": false, "embed": false}}')]
        }

    def applyFormatting(self):
        self.record.source = 'loc'
        self.record.source_id = self.record.identifiers[0]
        self.record.medium = self.record.medium[0]
        self.record.spatial = self.record.spatial.split(':')[0].strip(' ')

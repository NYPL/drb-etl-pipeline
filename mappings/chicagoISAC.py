from .json import JSONMapping

class ChicagoISACMapping(JSONMapping):
    def __init__(self, source):
        super().__init__(source, {})
        self.mapping = self.createMapping()
    
    def createMapping(self):
        return {
            'title': ('title', '{0}'),
            #'alternate': [('titlea', '{0}')],
            'authors': ('authors', '{0}|||true'),
            #'languages': [('langua', '{0}||')],
            'dates': ('publicationDate', '{0}|publication_date'),
            'publisher': ('publisher', '{0}'),
            'identifiers': 
                #('dmrecord', '{0}|met'),
                #('identi', '{0}|met'),
                #('digiti', '{0}|met'),
                ('isbn', '{0}|isbn')
            ,
            # 'contributors': [
            #     ('contri', '{0}|||contributor'),
            #     ('physic', '{0}|||repository'),
            #     ('source', '{0}|||provider')
            # ],
            'extent': ('extent', '{0}'),
            #'is_part_of': [('relatig', '{0}|collection')],
            # 'abstract': [
            #     ('transc', '{0}'),
            #     ('descri', '{0}')
            # ],
            # 'subjects': [('subjec', '{0}||')],
            # 'rights': (['rights', 'copyra', 'copyri'], 'met|{0}|{1}|{2}|'),
            'has_part': ('url', '1|{0}|isac|application/pdf|{{"catalog": false, "download": true, "reader": false, "embed": false}}')
        }

    def applyFormatting(self):
        self.record.source = 'isac'
        #if self.record.identifiers[0]:
        print(type(self.record.identifiers[0].split('|')[0]))
        self.record.source_id = f'isac_{self.record.identifiers[0]}'


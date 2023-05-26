from .json import JSONMapping

class ChicagoISACMapping(JSONMapping):
    def __init__(self, source):
        super().__init__(source, {})
        self.mapping = self.createMapping()
    
    def createMapping(self):
        return {
            'title': ('title', '{0}'),
            'authors': ('authors', '{0}|||true'),
            'dates': [('publicationDate', '{0}|publication_date')],
            'publisher': ('publisher', '{0}'),
            'identifiers': 
                [('isbn', '{0}|isbn')]
            ,
            'is_part_of': ('series', '{0}|series'),
            'spatial': ('publisherLocation', '{0}|publisherLocation'),
            'extent': ('extent', '{0}'),
            'has_part': [('url', '1|{0}|isac|application/pdf|{{"catalog": false, "download": true, "reader": false, "embed": false}}')] 
        }

    def applyFormatting(self):
        self.record.source = 'isac'

        #Formatting for multiple isbns
        if ',' in self.record.identifiers[0]:
            identifierArray = self.record.identifiers[0].split(', ')
            updatedIdentifierArray = []
            i = 0
            while len(updatedIdentifierArray) < len(identifierArray):
                if i == len(identifierArray)-1:
                    updatedIdentifierArray.append(identifierArray[i].strip())
                else:
                    updatedIdentifierArray.append(f'{identifierArray[i].strip()}|isbn')
                i += 1

            self.record.identifiers = updatedIdentifierArray

        source_id = self.record.identifiers[0].split('|')[0]
        self.record.source_id = f'isac_{source_id}'


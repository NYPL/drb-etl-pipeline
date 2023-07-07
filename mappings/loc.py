from .json import JSONMapping
import ast

class LOCMapping(JSONMapping):
    def __init__(self, source):
        super().__init__(source, {})
        self.mapping = self.createMapping()
    
    def createMapping(self):
        return {
            'title': ('title', '{0}'),
            'alternative': [('other_title', '{0}')], #One other_title in items block and one outside of it 
            'medium': [('original_format', '{0}')],
            'authors': ('contributor', '{0}|||true'),
            'languages': ('item', '||{0}'),
            'dates': ('dates', '{0}|publication_date'),
            'publisher': ('item', '{0}'),
            'identifiers': [
                ('number_lccn', '{0}|loc'),
                ('item', '{0}'),
            ],
            'contributors': 
                ('contributor', '{0}|||contributor'),
            'extent': [('item', '{0}')],
            'is_part_of': ('partof', '{0}|collection'),
            'abstract': 
                ('description', '{0}')
            ,
            'subjects': [('item', '{0}')],
        }

    def applyFormatting(self):
        self.record.has_part = []
        self.record.source = 'loc'
        self.record.medium = self.record.medium[0]

        #Convert string repr of list to actual list
        itemList = ast.literal_eval(self.record.identifiers[1])

        #Identifier Formatting
        newIdentifier = itemList
        newIdentifier['call_number'][0] = f'{newIdentifier["call_number"][0]}|call_number'
        lccnNumber = self.record.identifiers[0][0]  #lccnNumber comes in as an array and we need the string inside the array
        self.record.identifiers[0] = lccnNumber
        self.record.identifiers[1] = newIdentifier['call_number'][0].strip(' ')
        self.record.source_id = self.record.identifiers[0].split('|')[0]

        #Publisher/Spatial Formatting
        pubArray = []
        spatialArray = []
        for i, elem in enumerate(itemList['created_published']):
            if ':' not in elem:
                createdPublishedList = elem.split(',', 1)
                pubLocation = createdPublishedList[0].strip(' ')
                if ',' in createdPublishedList[1]:
                    pubOnly = createdPublishedList[1].split(',')[0].strip(' ')
                    pubArray.append(pubOnly)
                else: 
                    pubArray.append(pubOnly)
                spatialArray.append(pubLocation)
            else:
                pubLocatAndPubInfo = elem.split(':', 1)
                pubLocation = pubLocatAndPubInfo[0].strip()
                pubInfo = pubLocatAndPubInfo[1]
                pubOnly = pubInfo.split(',', 1)[0].strip()
                pubArray.append(pubOnly)
                spatialArray.append(pubLocation)

        self.record.publisher = pubArray
        self.record.spatial = spatialArray

        #Extent Formatting
        if 'medium' in itemList:
            for i, elem in enumerate(itemList['medium']):
                self.record.extent[i] = elem
        else:
            self.record.extent = []

        #Subjects Formatting
        if 'subjects' in itemList:
            subjectArray = []
            for i, elem in enumerate(itemList['subjects']):
                subjectArray.append(f'{elem}||')
            self.record.subjects = subjectArray
        else:
            self.record.subjects = []

        #Rights Formatting
        if 'rights_advisory' in itemList:
            rightsArray = []
            for i, elem in enumerate(itemList['rights_advisory']):
                rightsArray.append(f'loc|{elem}|||')
            self.record.rights = rightsArray
        else:
            self.record.rights = []

        #Languages Formatting
        if 'language' in itemList:
            languageArray = []
            for i, elem in enumerate(itemList['language']):
                languageArray.append(f'||{elem}')
            self.record.languages = languageArray
        else:
            self.record.languages = []

        

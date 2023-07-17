from .json import JSONMapping
import ast
import json

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
        }

    def applyFormatting(self):
        self.record.has_part = []
        self.record.source = 'loc'
        self.record.medium = self.record.medium[0]

        #Convert string repr of list to actual list
        itemList = ast.literal_eval(self.record.identifiers[1])

        self.record.identifiers[0], self.record.identifiers[1], self.record.source_id = self.formatIdentifierSourceID(itemList)

        self.record.publisher, self.record.spatial = self.formatPubSpatial(itemList)

        self.record.extent = self.formatExtent(itemList)

        self.record.subjects = self.formatSubjects(itemList)

        self.record.rights = self.formatRights(itemList)

        self.record.languages = self.formatLanguages(itemList)

    #Identifier/SourceID Formatting
    def formatIdentifierSourceID(self, itemList):
        newIdentifier = itemList
        newIdentifier['call_number'][0] = f'{newIdentifier["call_number"][0]}|call_number'
        lccnNumber = self.record.identifiers[0][0]  #lccnNumber comes in as an array and we need the string inside the array
        callNumber = newIdentifier['call_number'][0].strip(' ')
        sourceID = lccnNumber
        return (lccnNumber, callNumber, sourceID)
    
    #Publisher/Spatial Formatting
    def formatPubSpatial(self, itemList):
        pubArray = []
        spatialArray = []
        for elem in itemList['created_published']:
            if ':' not in elem:
                createdPublishedList = elem.split(',', 1)
                pubLocation = createdPublishedList[0].strip(' ')
                if ',' in createdPublishedList[1]:
                    pubOnly = createdPublishedList[1].split(',')[0].strip(' ')
                    pubArray.append(pubOnly)
                spatialArray.append(pubLocation)
            else:
                pubLocatAndPubInfo = elem.split(':', 1)
                pubLocation = pubLocatAndPubInfo[0].strip()
                pubInfo = pubLocatAndPubInfo[1]
                pubOnly = pubInfo.split(',', 1)[0].strip()
                pubArray.append(pubOnly)
                spatialArray.append(pubLocation)
        return (pubArray, spatialArray)
    
    #Extent Formatting
    def formatExtent(self, itemList):
        extentArray = []

        if 'medium' in itemList:
            extentArray.extend(itemList['medium'])

        return extentArray
    
    #Subjects Formatting
    def formatSubjects(self, itemList):
        subjectArray = []

        if 'subjects' in itemList:
            for elem in itemList['subjects']:
                subjectArray.append(f'{elem}||')
        
        return subjectArray
    
    #Rights Formatting
    def formatRights(self, itemList):
        rightsArray = []

        if 'rights_advisory' in itemList:
            for elem in itemList['rights_advisory']:
                rightsArray.append(f'loc|{elem}|||')

        return rightsArray
    
    #Languages Formatting
    def formatLanguages(self, itemList):
        languageArray = []

        if 'language' in itemList:
            for elem in itemList['language']:
                languageArray.append(f'||{elem}')

        return languageArray

        

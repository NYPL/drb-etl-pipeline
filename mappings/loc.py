from .json import JSONMapping
import ast
import json

from model import Part, FileFlags, Source

class LOCMapping(JSONMapping):
    def __init__(self, source):
        super().__init__(source, {})
        self.mapping = self.createMapping()
    
    def createMapping(self):
        return {
            'title': ('title', '{0}'),
            'alternative': ('other_title', '{0}'),
            'medium': ('original_format', '{0}'),
            'authors': ('contributor', '{0}|||true'),
            'dates': ('dates', '{0}|publication_date'),
            'publisher': ('item', '{0}'),
            'identifiers': [
                ('number_lccn', '{0}|lccn'),
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
        self.add_has_part_mapping()

        self.record.source = 'loc'
        if self.record.medium:
            self.record.medium = self.record.medium[0]
        if self.record.is_part_of and len(self.record.is_part_of) == 0:
            self.record.is_part_of = None
        if self.record.abstract and len(self.record.abstract) == 0:
            self.record.abstract = None

        #Convert string repr of list to actual list
        itemList = ast.literal_eval(self.record.identifiers[1])

        self.record.identifiers[0], self.record.identifiers[1], self.record.source_id = self.formatIdentifierSourceID(itemList)

        if self.record.identifiers[1] == None:
            del self.record.identifiers[1]

        self.record.publisher, self.record.spatial = self.formatPubSpatial(itemList)

        self.record.extent = self.formatExtent(itemList)

        self.record.subjects = self.formatSubjects(itemList)

        self.record.rights = self.formatRights(itemList)

        self.record.languages = self.formatLanguages(itemList)

    #Identifier/SourceID Formatting to return (string, string, string)
    def formatIdentifierSourceID(self, itemList):
        newIdentifier = itemList
        lccnNumber = self.record.identifiers[0][0]  #lccnNumber comes in as an array and we need the string inside the array
        sourceID = lccnNumber
        if 'call_number' in newIdentifier.keys():
            if not isinstance(newIdentifier['call_number'], list):
                    newIdentifier['call_number'] = list(newIdentifier['call_number'])

            newIdentifier['call_number'][0] = f'{newIdentifier["call_number"][0]}|call_number'
            callNumber = newIdentifier['call_number'][0].strip(' ')
        else: 
            callNumber = None
        return (lccnNumber, callNumber, sourceID)
    
    #Publisher/Spatial Formatting to return (array, string)
    def formatPubSpatial(self, itemList):
        pubArray = []
        spatialString = None
        if 'created_published' in itemList.keys():
            for elem in itemList['created_published']:
                if ':' not in elem:
                    createdPublishedList = elem.split(',', 1)
                    pubLocation = createdPublishedList[0].strip(' ')
                    if len(createdPublishedList) >= 2 and ',' in createdPublishedList[1]:
                        pubOnly = createdPublishedList[1].split(',')[0].strip(' ')
                        pubArray.append(pubOnly)
                    spatialString = pubLocation
                else:
                    pubLocatAndPubInfo = elem.split(':', 1)
                    pubLocation = pubLocatAndPubInfo[0].strip()
                    pubInfo = pubLocatAndPubInfo[1]
                    pubOnly = pubInfo.split(',', 1)[0].strip()
                    pubArray.append(pubOnly)
                    spatialString = pubLocation
            return (pubArray, spatialString)
        else:
            return ([], None)
    
    #Extent Formatting to return string
    def formatExtent(self, itemList):
        extentString = ''

        if 'medium' in itemList:
            if itemList['medium']:
                extentString = itemList['medium'][0]
                return extentString
            
        return None
    
    #Subjects Formatting to return array
    def formatSubjects(self, itemList):
        subjectArray = []

        if 'subjects' in itemList:
            for elem in itemList['subjects']:
                subjectArray.append(f'{elem}||')
        
        return subjectArray
    
    #Rights Formatting to return string
    def formatRights(self, itemList):
        rightsString = ''

        if 'rights_advisory' in itemList:
            if itemList['rights_advisory']:
                rightsString = f'loc|{itemList["rights_advisory"][0]}|||'
                return rightsString
            
        return None
        
    #Languages Formatting to return array
    def formatLanguages(self, itemList):
        languageArray = []

        if 'language' in itemList:
            for elem in itemList['language']:
                languageArray.append(f'||{elem}')

        return languageArray
    
    def add_has_part_mapping(self):
        if not self.source.get('resources'):
            return

        if 'pdf' in self.source['resources'][0].keys():
            self.record.has_part.append(Part(
                index=1,
                url=self.source['resources'][0]['pdf'],
                source=Source.LOC.value,
                file_type='application/pdf',
                flags=FileFlags(download=True).to_string()
            ).to_string())

        if 'epub_file' in self.source['resources'][0].keys():
            self.record.has_part.append(Part(
                index=1,
                url=self.source['resources'][0]['epub_file'],
                source=Source.LOC.value,
                file_type='application/pdf',
                flags=FileFlags(download=True).to_string()
            ).to_string())

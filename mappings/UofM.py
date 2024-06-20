from .json import JSONMapping
import logging

class UofMMapping(JSONMapping):
    def __init__(self, source, statics):
        super().__init__(source, statics)
        self.mapping = self.createMapping() 

    def createMapping(self):
        return {
            'title': ('Title', '{0}'),
            'authors': ('Author(s)', '{0}'),
            'dates': [('Pub Date', '{0}|publication_date')],
            'publisher': [('Publisher (from Projects)', '{0}||')],
            'identifiers': [
                ('ISBN', '{0}|isbn'),
                ('OCLC', '{0}|oclc')
            ],
            'rights': ('Rights status (from Rights status linked record)', '{0}||||'),
            'contributors': [('Contributors', '{0}|||contributor')],
            'subjects': ('Subject 1', '{0}'),
        }

    def applyFormatting(self):
        self.record.has_part = []
        self.record.spatial = 'Michigan'
        self.record.source = 'UofM'

        if self.record.authors:
            self.record.authors = self.formatAuthors()

        if self.record.subjects:
            self.record.subjects = self.formatSubjects()

        if self.record.identifiers:
            if len(self.record.identifiers) == 1:
                source_id = self.record.identifiers[0].split('|')[0]
            else:
                source_id = self.record.identifiers[1].split('|')[0]

        if self.record.rights:
            self.record.rights - self.formatRecords()

            self.record.source_id = f'UofM_{source_id}'
            self.record.identifiers = self.formatIdentifiers()

    def formatAuthors(self):
        authorList = []

        if ';' in self.record.authors:
            authorList = self.record.authors.split('; ')
            newAuthorList = [f'{author}|||true' for author in authorList] 
            return newAuthorList
        else:
            authorList.append(f'{self.record.authors}|||true)')
            return authorList
        
    def formatSubjects(self):
        subjectList = []

        if '|' in self.record.subjects:
            subjectList = self.record.subjects.split('|')
            newSubjectList = [f'{subject}||' for subject in subjectList] 
            return newSubjectList
        else:
            subjectList.append(f'{self.record.subjects}||')
            return subjectList
        
    def formatIdentifiers(self):
        if 'isbn' in self.record.identifiers[0]:
            isbnString = self.record.identifiers[0].split('|')[0]
            if ';' in isbnString:
                isbnList = isbnString.split('; ')
                newISBNList = [f'{isbn}|isbn' for isbn in isbnList]
                if len(self.record.identifiers) > 1 and 'oclc' in self.record.identifiers[1]:
                    newISBNList.append(f'{self.record.identifiers[1]}')
                    return newISBNList
                else:
                    return newISBNList
                
        return self.record.identifiers
    
    def formatRecords(self):
        # Parse rights codes
        rightsElements = self.record.rights.split('|') if self.record.rights else [''] * 5
        rightsMetadata = rightsElements[0]
        print(rightsMetadata)
        if rightsMetadata in self.staticValues['rightsValues'].keys():
            licenseMeta = self.staticValues['rightsValues']['rightsMetadata']['license']
            statementMeta = self.staticValues['rightsValues']['rightsMetadata']['statement']
            self.record.rights = 'UofM|{}|{}|{}|{}'.format(
                licenseMeta,
                self.staticValues['hathitrust']['rightsReasons'],
                statementMeta,
                rightsElements[4]
            ) 


            
        

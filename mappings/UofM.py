from .json import JSONMapping

class UofMMapping(JSONMapping):
    def __init__(self, source):
        super().__init__(source, {})
        self.mapping = self.createMapping()
    

    def createMapping(self):
        return {
            'title': ('Title', '{0}'),
            'authors': ('Author(s)', '{0}'),
            'dates': [('Pub Date', '{0}|publication_date')],
            'publisher': [('Publisher (from Projects)', '{0}')],
            'spatial': ('Michigan', '{0}'),
            'identifiers': [
                ('ISBN', '{0}|isbn'),
                ('OCLC', '{0}|oclc')
            ],
            'contributors': [('Contributors', '{0}|||contributor')],
            'subjects': [('Subject 1', '{0}||')],
        }

    def applyFormatting(self):
        self.record.source = 'UofM'

        source_id = self.record.identifiers[1].split('|')[0]
        self.record.source_id = f'UofM_{source_id}'

        if self.record.authors:
            self.record.authors = self.formatAuthors()
        if self.record.subjects:
            self.record.subjects = self.formatSubjects()
        if self.record.identifiers:
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
            subjectListList = self.record.subjects.split('; ')
            newSubjectList = [f'{author}|||true' for author in subjectList] 
            return newSubjectList
        else:
            subjectList.append(f'{self.record.authors}|||true)')
            return subjectList
        
    def formatIdentifiers(self):
        if 'isbn' in self.record.identifiers[0]:
            isbnString = self.record.identifiers[0].split('|')[0]
            if ';' in isbnString:
                isbnList = isbnString.split('; ')
                newISBNList = [f'{isbn}|isbn' for isbn in isbnList]
                if len(self.record.identifiers) > 1 and 'oclc' in self.record.identifiers[1]:
                    newISBNList.append(f'{self.record.identifiers[1]}|oclc')
                    return newISBNList
                else:
                    return newISBNList


            
        

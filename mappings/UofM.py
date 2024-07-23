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
            'publisher': [('Publisher (from Projects)', '{0}||')],
            'identifiers': [
                ('ISBN', '{0}|isbn'),
                ('OCLC', '{0}|oclc')
            ],
            'rights': ('DRB Rights Classification', '{0}||||'),
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
                self.record.source_id = f'UofM_{source_id}'
                self.record.identifiers = self.formatIdentifiers()
            else:
                source_id = self.record.identifiers[1].split('|')[0]
                self.record.source_id = f'UofM_{source_id}'
                self.record.identifiers = self.formatIdentifiers()

        self.record.rights = self.formatRights()

    def formatAuthors(self):
        authorList = []

        if ';' in self.record.authors:
            authorList = self.record.authors.split('; ')
            newAuthorList = [f'{author}|||true' for author in authorList] 
            return newAuthorList
        else:
            authorList.append(f'{self.record.authors}|||true)')
            return authorList
        
        
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
    
    def formatSubjects(self):
        subjectList = []

        if '|' in self.record.subjects:
            subjectList = self.record.subjects.split('|')
            newSubjectList = [f'{subject}||' for subject in subjectList] 
            return newSubjectList
        else:
            subjectList.append(f'{self.record.subjects}||')
            return subjectList
    
    def formatRights(self):
        '''
        The pipe delimiter is to separate the Rights table attributes into this format:
        source|license|reason|statement|date 
        which makes it easy to place the right data into the columns when clustered
        '''

        if not self.record.rights: 
            return None

        rightsElements = self.record.rights.split('|')
        rightsStatus = rightsElements[0]

        if rightsStatus == 'in copyright':
            return 'UofM|{}||{}|'.format('in_copyright', 'In Copyright') 
        
        if rightsStatus == 'public domain':
            return 'UofM|{}||{}|'.format('public_domain', 'Public Domain') 
        
        return None




            
        

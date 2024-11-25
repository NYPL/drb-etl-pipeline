from .json import JSONMapping

class PublisherBacklistMapping(JSONMapping):
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
            'source': ('Projects', '{0}'),
            'publisher_project_source': ('Publisher (from Projects)', '{0}')
        }

    def apply_formatting(self):
        self.record.has_part = []

        if self.record.source:
            source_list = self.record.source.split(' ')
            print(source_list)
            self.record.source = source_list[0]

        if self.record.publisher_project_source:
            publisher_source = self.record.publisher_project_source[0]
            self.record.publisher_project_source = publisher_source

        if self.record.authors:
            self.record.authors = self.format_authors()

        if self.record.subjects:
            self.record.subjects = self.format_subjects()

        if self.record.identifiers:
            if len(self.record.identifiers) == 1:
                source_id = self.record.identifiers[0].split('|')[0]
                self.record.source_id = f'{self.record.source}_{source_id}'
                self.record.identifiers = self.format_identifiers()
            else:
                source_id = self.record.identifiers[1].split('|')[0]
                self.record.source_id = f'{self.record.source}_{source_id}'
                self.record.identifiers = self.format_identifiers()

        self.record.rights = self.format_rights()

    def format_authors(self):
        authorList = []

        if ';' in self.record.authors:
            authorList = self.record.authors.split('; ')
            newAuthorList = [f'{author}|||true' for author in authorList] 
            return newAuthorList
        else:
            authorList.append(f'{self.record.authors}|||true)')
            return authorList
        
        
    def format_identifiers(self):
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
    
    def format_subjects(self):
        subjectList = []

        if '|' in self.record.subjects:
            subjectList = self.record.subjects.split('|')
            newSubjectList = [f'{subject}||' for subject in subjectList] 
            return newSubjectList
        else:
            subjectList.append(f'{self.record.subjects}||')
            return subjectList
    
    def format_rights(self):
        if not self.record.rights: 
            return None

        rightsElements = self.record.rights.split('|')
        rightsStatus = rightsElements[0]

        if rightsStatus == 'in copyright':
            return '{}|{}||{}|'.format('self.record.source', 'in_copyright', 'In Copyright') 
        
        if rightsStatus == 'public domain':
            return '{}|{}||{}|'.format('self.record.source', 'public_domain', 'Public Domain') 
        
        return None

from .json import JSONMapping
import re

AUTHOR_DIGITS = r"\d+-*."

class PublisherBacklistMapping(JSONMapping):
    def __init__(self, source):
        super().__init__(source, {})
        self.mapping = self.createMapping()

    def createMapping(self):
        return {
            'title': ('Title', '{0}'),
            'authors': ('Author(s)', '{0}'),
            'dates': [('Pub Date', '{0}|publication_date')],
            'publisher': ('Publisher (from Project)', '{0}||'),
            'identifiers': [
                ('OCLC', '{0}|oclc'),
                ('Hathi ID', '{0}|hathi'),
            ],
            'abstract': ('Content Provider', 'Book digitized by library {0}'),
            'rights': ('DRB Rights Classification', '{0}||||'),
            'contributors': [('Contributors', '{0}|||contributor')],
            'subjects': ('Subject 1', '{0}'),
            'source': ('Project Name (from Project)', '{0}'),
            'source_id': ('DRB_Record ID', '{0}'),
            'publisher_project_source': ('Publisher (from Project)', '{0}')
        }

    def applyFormatting(self):
        self.record.has_part = []
        if self.record.source:
            self.record.source = 'Schomburg'
            #self.record.source = self.record.source[0]

        if self.record.publisher_project_source:
            publisher_source = self.record.publisher_project_source[0]
            self.record.publisher_project_source = publisher_source

        if self.record.authors:
            self.record.authors = self.format_authors()

        if self.record.subjects:
            self.record.subjects = self.format_subjects()

        if self.record.identifiers:
            self.record.identifiers = self.format_identifiers()

        self.record.rights = self.format_rights()

    def format_authors(self):
        author_list = []

        if ';' in self.record.authors:
            author_list = self.record.authors.split('; ')
            author_list = [f'{author}|||true' for author in author_list] 
            return author_list
        else:
            self.record.authors = re.sub(AUTHOR_DIGITS, "", self.record.authors).rstrip()
            if self.record.authors[-1] == ',':
                new_authors = self.record.authors[:-1]
                author_list.append(f'{new_authors}|||true)')
            else:
                author_list.append(f'{self.record.authors}|||true)')
        return author_list
        
    def format_identifiers(self):
        if 'isbn' in self.record.identifiers[0]:
            isbn_string = self.record.identifiers[0].split('|')[0]
            isbns = []

            if ';' in isbn_string:
                isbns = isbn_string.split('; ')    
            elif ',' in isbn_string:
                isbns = isbn_string.split(', ')
 
            if isbns:
                formatted_isbns = [f'{isbn}|isbn' for isbn in isbns]
                if len(self.record.identifiers) > 1 and 'oclc' in self.record.identifiers[1]:
                    formatted_isbns.append(f'{self.record.identifiers[1]}')
                    return formatted_isbns
                else:
                    return formatted_isbns
        elif 'oclc' in self.record.identifiers[0]:
            oclc_string = self.record.identifiers[0].split('|')[0]
            oclcs = []

            if ';' in oclc_string:
                oclcs = oclc_string.split('; ')    
            elif ',' in oclc_string:
                oclcs = oclc_string.split(', ')
 
            if oclcs:
                formatted_oclcs = [f'{oclc}|oclc' for oclc in oclcs]
                if len(self.record.identifiers) > 1 and 'hathi' in self.record.identifiers[1]:
                    formatted_oclcs.append(f'{self.record.identifiers[1]}')
                    return formatted_oclcs
                else:
                    return formatted_oclcs
                
        return self.record.identifiers
    
    def format_subjects(self):
        subject_list = []

        if '|' in self.record.subjects:
            subject_list = self.record.subjects.split('|')
            return [f'{subject}||' for subject in subject_list]
        else:
            subject_list.append(f'{self.record.subjects}||')
            return subject_list
    
    def format_rights(self):
        if not self.record.rights: 
            return None

        rights_elements = self.record.rights.split('|')
        rights_status = rights_elements[0]

        if rights_status == 'in copyright':
            return '{}|{}||{}|'.format(self.record.source, 'in_copyright', 'In Copyright') 
        elif rights_status == 'public domain':
            return '{}|{}||{}|'.format(self.record.source, 'public_domain', 'Public Domain') 
        
        return None

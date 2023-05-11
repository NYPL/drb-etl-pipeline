from .json import JSONMapping

class ChicagoISACMapping(JSONMapping):
    def __init__(self, source):
        super().__init__(source, {})
        self.mapping = self.createMapping()
    
    def createMapping(self):
        return {
            'title': ('title', '{0}'),
            'alternate': [('titlea', '{0}')],
            'authors': [('creato', '{0}|||true')],
            'languages': [('langua', '{0}||')],
            'dates': [('date', '{0}|publication_date')],
            'publisher': [('publis', '{0}')],
            'identifiers': [
                ('dmrecord', '{0}|met'),
                ('identi', '{0}|met'),
                ('digiti', '{0}|met'),
                ('dmcoclcno', '{0}|oclc')
            ],
            'contributors': [
                ('contri', '{0}|||contributor'),
                ('physic', '{0}|||repository'),
                ('source', '{0}|||provider')
            ],
            'extent': ('format', '{0}'),
            'is_part_of': [('relatig', '{0}|collection')],
            'abstract': [
                ('transc', '{0}'),
                ('descri', '{0}')
            ],
            'subjects': [('subjec', '{0}||')],
            'rights': (['rights', 'copyra', 'copyri'], 'met|{0}|{1}|{2}|'),
            'has_part': [('link', '1|{0}|met|text/html|{{"catalog": false, "download": false, "reader": false, "embed": true}}')]
        }

    def applyFormatting(self):
        self.record.source = 'chicagoISAC'
        self.record.source_id = self.record.identifiers[0]

        # Clean up subjects
        try:
            subjString = self.record.subjects[0].split('|')[0]
            subjects = subjString.split(';')
            self.record.subjects = ['{}||'.format(s.strip()) for s in subjects]
        except IndexError:
            self.record.subjects = None

        # Select best abstract
        try:
            abstracts = self.record.abstract
            self.record.abstract = list(filter(lambda x: x != '', abstracts))[0]
        except IndexError:
            self.record.abstract = None

        # Set PDF download link
        pdfURL = self.PDF_LINK.format(self.source['dmrecord'])
        self.record.has_part.append(
            '|'.join(['1', pdfURL, 'chicagoISAC', 'application/pdf', '{}'])
        )

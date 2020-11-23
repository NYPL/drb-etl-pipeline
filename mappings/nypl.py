from .sql import SQLMapping

class NYPLMapping(SQLMapping):
    def __init__(self, source, statics):
        super().__init__(source, statics)
        self.mapping = self.createMapping()
    
    def createMapping(self):
        return {
            'title': ('title', '{0}'),
            'alternative': [
                ('246', '{a} {b} {p}'),
                ('247', '{a} {f}')
            ],
            'authors': [('author', '{0}|||true')],
            'languages': [('lang', '{name}||{code}')],
            'dates': [
                ('publish_year', '{0}|publication_date'),
                ('catalog_date', '{0}|catalog_date')
            ],
            'spatial': ('country', '{name}'),
            'identifiers': [
                ('id', '{0}|nypl'),
                ('issn', '{0}|issn'),
                ('lccn', '{0}|lccn'),
                ('oclc', '{0}|oclc'),
                ('isbn', '{0}|isbn'),
                ('010', '{a}|lccn'),
                ('020', '{a}|isbn'),
                ('022', '{a}|issn'),
                ('028', '{a}|{b}'),
                ('035', '{a}|scn'),
                ('050', '{a} {b}|lcc'),
                ('060', '{a}|nlmcn'),
                ('074', '{a}|gpoin'),
                ('086', '{a}|gdcn')
            ],
            'publisher': ('260', '{b}||'),
            'contributors': [
                ('260', '{f}|||manufacturer'),
                ('700', '{a}|||{e}'),
                ('710', '{a} {b}|||{e}'),
                ('711', '{a} {b}|||{e}')
            ],
            'has_version': ('250', '{a}|'),
            'extent': ('300', '{a}{b}{c}'),
            'is_part_of': [
                ('440', '{a}|{v}|volume'),
                ('490', '{a}|{v}|volume')
            ],
            'abstract': [
                ('500', '{a}'),
                ('520', '{a} {b}')
            ],
            'table_of_contents': ('505', '{a}'),
            'subjects': [
                ('600', '{a} {d} -- {t} -- {v}|lcsh|{0}'),
                ('610', '{a} -- {b} -- {v} -- {x} -- {z}|lcsh|{0}'),
                ('611', '{a} -- {v}|lcsh|{0}'),
                ('630', '{a} -- {p} -- {v}|lcsh|{0}'),
                ('650', '{a} -- {b} -- {v} -- {x} -- {z}|lcsh|{0}'),
                ('651', '{a} -- {b} -- {v} -- {x} -- {z}|lcsh|{0}'),
                ('655', '{a}|{2}|'),
                ('656', '{a}|{2}|'),
                ('690', '{a} -- {b} -- {v} -- {x} -- {z}|lcsh|{0}'),
            ],
            'has_part': ('856', '1|{u}|nypl|catalog|{z}')
        }
    
    def applyMapping(self):
        self.parseFixedFields()
        super().applyMapping()
    
    def parseFixedFields(self):
        self.source = dict(self.source)
        for value in self.source['var_fields']:
            marcField = {
                'ind1': value['ind1'],
                'ind2': value['ind2'],
                'content': value['content']
            }
            try:
                for sub in value['subfields']:
                    marcField[sub['tag']] = sub['content']
            except TypeError:
                continue
            self.source[value['marcTag']] = marcField
    
    def applyFormatting(self):
        self.record.source = 'nypl'
        self.record.source_id = self.record.identifiers[0]

        # Parse identifiers and de-duplicate
        cleanIdentifiers = set()
        for iden in self.record.identifiers:
            if isinstance(iden, list):
                cleanIdentifiers.update(iden)
            elif '(OCoLC)' in iden:
                oclcIden = iden.replace('(OCoLC)', '').replace('scn', 'oclc')
                cleanIdentifiers.add(oclcIden)
        self.record.identifiers = list(cleanIdentifiers)
        

        # Clean up subjects
        for i, subject in enumerate(self.record.subjects):
            subjComponents = subject.split('|')
            subjParts = list(filter(lambda x: x.strip() != '', subjComponents[0].split('--')))
            self.record.subjects[i] = '{}|{}|{}'.format(
                ' -- '.join(subjParts), *subjComponents[1:]
            )
        
        # Parse contributors to set proper roles
        for i, contributor in enumerate(self.record.contributors):
            contribComponents = contributor.split('|')
            lcRelation = self.staticValues['lc']['relators'].get(contribComponents[-1], 'Contributor')
            self.record.contributors[i] = '{}|{}|{}|{}'.format(
                *contribComponents[:-1], lcRelation
            )

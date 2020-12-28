import json
import re

from .csv import CSVMapping


class HathiMapping(CSVMapping):
    def __init__(self, source, statics):
        super(HathiMapping, self).__init__(source, statics)
        self.mapping = self.createMapping()
    
    def createMapping(self):
        return {
            'identifiers': [
                ('{}|hathi', 0),
                ('{}|hathi', 3),
                ('{}({})|generic', 6, 5),
                ('{}|oclc', 7),
                ('{}|isbn', 8),
                ('{}|issn', 9),
                ('{}|isbn', 10)
            ],
            'rights': ('hathitrust|{}|{}||{}', 2, 13, 14),
            'is_part_of': [('{}|volume', 4)],
            'title': ('{}', 11),
            'dates': [('{}|publication_date', 12), ('{}|copyright_date', 16)],
            'requires': [('{}|government_document', 15)],
            'spatial': ('{}', 17),
            'languages': [('||{}', 18)],
            'contributors': [
                ('{}|||provider', 21),
                ('{}|||responsible', 22),
                ('{}|||digitizer', 23)
            ],
            'authors': [('{}|||true', 25)]
        }
    
    def applyFormatting(self):
        # Set source metadata
        self.record.source = 'hathitrust'
        self.record.source_id = self.record.identifiers[0]

        # Parse publisher from publication date
        pubDate = self.record.dates[0]
        try:
            pubDateExtract = re.search(r'[0-9]{4}', pubDate).group(0)
            self.record.dates[0] = '{}|publication_date'.format(pubDateExtract)
        except AttributeError:
            self.record.dates.pop(0)
            pubDateExtract = ''
        publisher = pubDate.replace(pubDateExtract, '').split('|')[0].strip('[], .;')
        self.record.publisher = '{}||'.format(publisher)

        
        # Parse contributers into full names
        for i, contributor in enumerate(self.record.contributors):
            contribElements = contributor.lower().split('|')
            fullContribName = self.staticValues['hathitrust']['sourceCodes'].get(contribElements[0], contribElements[0])
            self.record.contributors[i] = contributor.replace(contribElements[0], fullContribName)

        # Parse rights codes
        rightsElements = self.record.rights.split('|')
        rightsMetadata = self.staticValues['hathitrust']['rightsValues'].get(rightsElements[1], {'license': 'und', 'statement': 'und'}) 
        self.record.rights = '{}|{}|{}|{}'.format(
            rightsMetadata['license'],
            self.staticValues['hathitrust']['rightsReasons'].get(rightsElements[2], rightsElements[2]),
            rightsMetadata['statement'],
            rightsElements[4]
        )

        # Add Read Online links
        readOnlineLink = '{}|{}|{}|{}|{}'.format(
            1,
            'https://babel.hathitrust.org/cgi/pt?id={}'.format(self.source[0]),
            'hathitrust',
            'text/html',
            json.dumps({'reader': False, 'download': False, 'catalog': False})
        )
        downloadLink = '{}|{}|{}|{}|{}'.format(
            1,
            'https://babel.hathitrust.org/cgi/imgsrv/download/pdf?id={}'.format(self.source[0]),
            'hathitrust',
            'application/pdf',
            json.dumps({'reader': False, 'download': True, 'catalog': False})
        ) 
        self.record.has_part = [readOnlineLink, downloadLink]

        # Parse spatial (pub place) codes
        self.record.spatial = self.staticValues['marc']['countryCodes'].get(self.record.spatial.strip(), 'xx')
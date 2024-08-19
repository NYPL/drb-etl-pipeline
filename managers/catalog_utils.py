import fasttext
import re

ANTHOLOGY_TOKENS = [
        'collection', 'collected', 'selected', 'anthology', 'complete'
    ]

TITLE_STOPWORDS = [
        'a', 'an', 'the', 'at', 'on', 'and', 'of', 'from', 'to'
    ]

# This is a compressed 917kb file that contains a language detection model
LANG_MODEL = fasttext.load_model('lid.176.ftz')

def clean_str(string):
        """Removes return and line break characters from the current work's
        title. This allows for better matching and cleaner results.
        """
        return ' '.join(string.replace('\r', ' ').replace('\n', ' ').split())

def clean_title(title):
    wordTokens = re.split(r'\s+', title)
    return list(filter(
        lambda x: x not in TITLE_STOPWORDS and x != '',
        [re.sub(r'[^\w]+', '', token.lower()) for token in wordTokens]
    ))

def clean_identifier(identifier):
    return re.sub(r'[\D]+', '', identifier)

def get_queryable_identifiers(identifiers):
    return list(filter(
        lambda x: re.search(r'\|(?:isbn|issn|oclc)$', x) != None,
            identifiers
        ))

def getStrLang(string):
    try:
        langPredict = LANG_MODEL.predict(string, threshold=0.5)
        langCode = langPredict[0][0].split('__')[2]
    except (AttributeError, IndexError, ValueError):
        # TODO: How/where should this be logged if this remains in the utils
        # instead of being a class method?
        langCode = 'unk'
    return langCode

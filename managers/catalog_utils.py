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
    word_tokens = re.split(r'\s+', title)
    return list(filter(
        lambda x: x not in TITLE_STOPWORDS and x != '',
        [re.sub(r'[^\w]+', '', token.lower()) for token in word_tokens]
    ))

def clean_identifier(identifier):
    return re.sub(r'[\D]+', '', identifier)

def get_queryable_identifiers(identifiers):
    return list(filter(
        lambda x: re.search(r'\|(?:isbn|issn|oclc)$', x) != None,
            identifiers
        ))

def get_str_lang(string):
    try:
        lang_predict = LANG_MODEL.predict(string, threshold=0.5)
        lang_code = lang_predict[0][0].split('__')[2]
    except (AttributeError, IndexError, ValueError):
        # TODO: How/where should this be logged if this remains in the utils
        # instead of being a class method?
        lang_code = 'unk'
    return lang_code

def check_title(source_title, authority_title):
        authority_code = get_str_lang(authority_title)
        source_code = get_str_lang(source_title)
        if authority_code == source_code:
            clean_authority_title = clean_title(authority_title)
            authority_anthology = True if len(set(clean_authority_title) & set(ANTHOLOGY_TOKENS)) > 0 else False
            clean_source_title = clean_title(source_title)
            source_anthology = True if len(set(clean_source_title) & set(ANTHOLOGY_TOKENS)) > 0 else False
            if (
                len(set(clean_authority_title) & set(clean_source_title)) > 0
                and authority_anthology == source_anthology
            ):
                return True
            else:
                return False
        return True

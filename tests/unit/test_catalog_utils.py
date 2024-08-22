from managers.catalog_utils import clean_identifier, check_title, clean_str, clean_title, get_str_lang, get_queryable_identifiers
from unittest.mock import call, patch

class TestCatalogUtils:
    def test_clean_str(self):
        assert clean_str('hello\n line\r') == 'hello line'

    # n.b. Stacked patch decorators apply bottom up in params
    @patch('managers.catalog_utils.get_str_lang')
    @patch('managers.catalog_utils.clean_title')
    def test_check_title_lang_match_same(self, clean_title_patch, get_str_lang_patch):
        get_str_lang_patch.side_effect = ['te', 'te']
        clean_title_patch.side_effect = [['oclc', 'title'], ['test', 'title']]

        assert check_title('testTitle', 'oclcTitle') is True
        get_str_lang_patch.assert_has_calls([call('oclcTitle'),call('testTitle')],
                                            any_order=True)
        clean_title_patch.assert_has_calls([call('oclcTitle'), call('testTitle')],
                                           any_order=True)

    @patch('managers.catalog_utils.get_str_lang')
    @patch('managers.catalog_utils.clean_title')
    def test_check_title_lang_match_different(self, clean_title_patch, get_str_lang_patch):
        get_str_lang_patch.side_effect = ['te', 'te']
        clean_title_patch.side_effect = [['oclc', 'collected'], ['test', 'title']]

        assert check_title('testTitle', 'oclcCollected') is False
        get_str_lang_patch.assert_has_calls([call('oclcCollected'), call('testTitle')],
                                            any_order=True)
        clean_title_patch.assert_has_calls([call('oclcCollected'), call('testTitle')],
                                        any_order=True)

    @patch('managers.catalog_utils.get_str_lang')
    @patch('managers.catalog_utils.clean_title')
    def test_check_title_no_lang_match(self, clean_title_patch, get_str_lang_patch):
        get_str_lang_patch.side_effect = ['te', 'ot']

        assert check_title('testTitle','oclcLanguage') is True
        get_str_lang_patch.assert_has_calls([call('oclcLanguage'), call('testTitle')],
                                            any_order=True)
        clean_title_patch.assert_not_called

    def test_get_str_lang_success(self):
        assert get_str_lang('English') == 'en'

    def test_get_str_lang_non_latin(self):
        assert get_str_lang('わかりません') == 'ja'

    def test_get_str_lang_error(self):
        assert get_str_lang('01234') == 'unk'

    def test_get_str_land_not_a_string_error(self):
        assert get_str_lang(34) == 'unk'

    def test_clean_title(self):
        assert clean_title('The Real Title()') == ['real', 'title']

    def test_clean_identifier(self):
        assert clean_identifier('no1234') == '1234'

    def test_get_queryable_identifiers(self):
        assert get_queryable_identifiers(['1|isbn', '2|test']) == ['1|isbn']
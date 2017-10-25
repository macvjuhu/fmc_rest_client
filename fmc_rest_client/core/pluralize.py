"""
From - http://code.activestate.com/recipes/577781-pluralize-word-convert-singular-word-to-its-plural/
New Link - https://github.com/ActiveState/code/tree/3b27230f418b714bc9a0f897cb8ea189c3515e99/recipes/Python/577781_Pluralize_word__convert_singular_word_its
See License.pluralize for license details.

Add any resource name which doesn't follow the plural logic. 
"""
ABERRANT_PLURAL_MAP = {
    'appendix': 'appendices',
    'index': 'indices',
}
VOWELS = set('aeiou')


def pluralize(singular):
    """Return plural form of given lowercase singular word (English only). Based on
    ActiveState recipe http://code.activestate.com/recipes/413172/
    """
    if not singular:
        return ''
    plural = ABERRANT_PLURAL_MAP.get(singular)
    if plural:
        return plural
    root = singular
    try:
        if singular[-1] == 'y' and singular[-2] not in VOWELS:
            root = singular[:-1]
            suffix = 'ies'
        elif singular[-1] == 's':
            if singular[-2] in VOWELS:
                if singular[-3:] == 'ius':
                    root = singular[:-2]
                    suffix = 'i'
                else:
                    root = singular[:-1]
                    suffix = 'ses'
            else:
                suffix = 'es'
        elif singular[-2:] in ('ch', 'sh'):
            suffix = 'es'
        else:
            suffix = 's'
    except IndexError:
        suffix = 's'
    plural = root + suffix
    return plural

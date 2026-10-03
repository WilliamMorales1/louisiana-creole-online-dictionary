import unicodedata


def fold(text):
    """fold lowercases text in NFC form, keeping accents."""
    return unicodedata.normalize('NFC', text or '').lower()


def plain(text):
    """plain lowercases text and strips its accents."""
    decomposed = unicodedata.normalize('NFD', text or '')
    stripped = ''.join(c for c in decomposed if unicodedata.category(c) != 'Mn')
    return unicodedata.normalize('NFC', stripped).lower()

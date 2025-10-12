import re
import unicodedata
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

def strip_accents(s):
    """Return a version of s with combining marks removed (NFD -> remove Mn)."""
    return ''.join(
        c for c in unicodedata.normalize('NFD', s)
        if unicodedata.category(c) != 'Mn'
    )

@register.filter
def highlight(text, opts):
    """
    opts is expected to be a dict with keys:
      - 'search' or 'query': query text
      - 'whole_word': bool
      - 'match_accents': bool
    """
    if not text:
        return text

    if not opts or not isinstance(opts, dict):
        return text

    # accept both keys for backward compatibility
    search = opts.get("search") or opts.get("query") or ""
    whole_word = bool(opts.get("whole_word", False))
    match_accents = bool(opts.get("match_accents", False))

    if not search:
        return text

    # Build regex pattern (escape special chars in search)
    pattern = re.escape(search)
    if whole_word:
        pattern = fr"\b{pattern}\b"

    flags = re.IGNORECASE

    # If we should match accents, just run regex on original text
    if match_accents:
        try:
            result = ""
            last_end = 0
            for m in re.finditer(pattern, text, flags=flags):
                s, e = m.span()
                result += text[last_end:s]
                result += f"<mark>{text[s:e]}</mark>"
                last_end = e
            result += text[last_end:]
            return mark_safe(result)
        except re.error:
            return text

    # --- Otherwise, match without accents ---
    # We'll create a normalized (accent-stripped) version of text,
    # but we must map normalized indexes back to original text indexes.
    normalized_chars = []
    norm_to_orig = []  # for each normalized-char index, store original-char index
    for orig_idx, ch in enumerate(text):
        # NFD normalization may expand a char into base + combining marks
        nfd = unicodedata.normalize('NFD', ch)
        for c in nfd:
            if unicodedata.category(c) == 'Mn':
                # skip combining marks (removes accents)
                continue
            normalized_chars.append(c)
            norm_to_orig.append(orig_idx)

    normalized_text = ''.join(normalized_chars)
    normalized_search = strip_accents(search)

    # Build normalized pattern (escape normalized_search)
    norm_pattern = re.escape(normalized_search)
    if whole_word:
        norm_pattern = fr"\b{norm_pattern}\b"

    try:
        result = ""
        last_orig_end = 0

        for m in re.finditer(norm_pattern, normalized_text, flags=flags):
            s_norm, e_norm = m.span()
            # map normalized indices back to original indices
            orig_start = norm_to_orig[s_norm]
            # e_norm is exclusive index in normalized. norm_to_orig[e_norm-1] gives
            # the original index of the last normalized char matched; we want exclusive end:
            orig_end = norm_to_orig[e_norm - 1] + 1

            result += text[last_orig_end:orig_start]
            result += f"<mark>{text[orig_start:orig_end]}</mark>"
            last_orig_end = orig_end

        result += text[last_orig_end:]
        return mark_safe(result)
    except (IndexError, re.error):
        # fallback: return original text unchanged
        return text

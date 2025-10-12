from django.shortcuts import render
from django.db.models import Q, Prefetch
from .models import Entry, Variant, Source, POS
import unicodedata
import re

# --- Utility Functions ---
def normalize_text(text):
    """Normalize text to NFD (decomposed) form."""
    return unicodedata.normalize('NFD', text or '')

def strip_accents(text):
    """Remove all accent marks from the text."""
    text = normalize_text(text)
    return ''.join(c for c in text if unicodedata.category(c) != 'Mn')

def whole_word_match(text, search, match_accents):
    """
    Return True if `text` contains a word that exactly equals `search`,
    respecting `match_accents` toggle, using the same logic as the highlight filter.
    """
    if not text or not search:
        return False

    # Normalize text and search if we ignore accents
    if not match_accents:
        # Create normalized (accent-stripped) text and map back to original
        normalized_chars = []
        for ch in text:
            nfd = unicodedata.normalize('NFD', ch)
            for c in nfd:
                if unicodedata.category(c) != 'Mn':
                    normalized_chars.append(c)
        text_to_search = ''.join(normalized_chars)
        search_text = strip_accents(search)
    else:
        text_to_search = text
        search_text = search

    # Case-insensitive match
    text_to_search = text_to_search.lower()
    search_text = search_text.lower()

    # Match as whole words using regex
    try:
        pattern = fr"\b{re.escape(search_text)}\b"
        return bool(re.search(pattern, text_to_search, flags=re.UNICODE))
    except re.error:
        return False

# --- Main Search View ---
def search_dictionary(request):
    query = request.GET.get('q', '').strip()
    field = request.GET.get('field', 'headword')
    whole_word = 'whole_word' in request.GET
    match_accents = 'match_accents' in request.GET
    include_examples = 'include_examples' in request.GET
    selected_pos = request.GET.get('part_of_speech', '')
    selected_source = request.GET.get('source', '')

    display_query = query
    search_query = strip_accents(query) if not match_accents else query

    # Prefetch related objects to avoid N+1 queries
    variants_prefetch = Prefetch('variants', queryset=Variant.objects.prefetch_related('sources'))
    results = Entry.objects.all().prefetch_related(
        'definitions', 'parts_of_speech', 'sources', variants_prefetch
    ).distinct()

    # --- Populate dropdowns ---
    all_pos = POS.objects.exclude(part_of_speech__isnull=True).exclude(part_of_speech='') \
        .values_list('part_of_speech', flat=True).distinct().order_by('part_of_speech')

    all_sources = Source.objects.filter(
        Q(entry__isnull=False) | Q(variant__isnull=False)
    ).exclude(text__isnull=True).exclude(text='') \
        .values_list('text', flat=True).distinct().order_by('text')

    # --- Apply search query ---
    if search_query:
        search_norm = search_query.lower() if match_accents else strip_accents(search_query).lower()
        filtered = []

        for entry in results:
            definitions_match = False
            head_matches = False
            variant_matches = False

            # --- Definitions search ---
            if field == 'definitions':
                for definition in entry.definitions.all():
                    gloss = definition.gloss or ''
                    examples = definition.examples or ''
                    text_to_search = f"{gloss} {examples}" if include_examples else gloss

                    if whole_word:
                        if whole_word_match(text_to_search, query, match_accents):
                            definitions_match = True
                            break
                    else:
                        text_norm = text_to_search if match_accents else strip_accents(text_to_search)
                        if search_norm in text_norm.lower():
                            definitions_match = True
                            break
            else:
                # --- Headword match ---
                head = entry.headword or ''
                if whole_word:
                    head_matches = whole_word_match(head, query, match_accents)
                else:
                    head_norm = head if match_accents else strip_accents(head)
                    head_matches = search_norm in head_norm.lower()

                # --- Variant match ---
                if whole_word:
                    variant_matches = any(whole_word_match(v.text or '', query, match_accents) for v in entry.variants.all())
                else:
                    variant_matches = any(search_norm in (v.text if match_accents else strip_accents(v.text)).lower() for v in entry.variants.all())

            # --- POS filter ---
            pos_matches = True
            if selected_pos:
                pos_matches = any(p.part_of_speech == selected_pos for p in entry.parts_of_speech.all())

            # --- Source filter ---
            source_matches = True
            if selected_source:
                entry_sources = [s.text.strip() for s in entry.sources.all() if s.text]
                variant_sources = [s.text.strip() for v in entry.variants.all() for s in v.sources.all() if s.text]
                source_matches = selected_source in entry_sources or selected_source in variant_sources

            # --- Include entry if it passes filters ---
            if (definitions_match or head_matches or variant_matches) and pos_matches and source_matches:
                filtered.append(entry)

        results = filtered

    # --- Apply POS & Source filters for remaining results ---
    if selected_pos:
        results = results.filter(parts_of_speech__part_of_speech=selected_pos)
    if selected_source:
        results = results.filter(
            Q(sources__text=selected_source) |
            Q(variants__sources__text=selected_source)
        ).distinct()

    # --- Prepare sources for display ---
    processed_results = []
    for entry in results:
        # --- Entry-level sources only ---
        entry_sources = [
            s.text.strip() 
            for s in entry.sources.all() 
            if s.text and s.text.strip() and s.variant_id is None
        ]
        entry.sources_display = ', '.join(entry_sources) if entry_sources else "No sources"

        variants_list = []
        for variant in entry.variants.all():
            variant_sources = [s.text.strip() for s in variant.sources.all() if s.text]
            variant.sources_display = ', '.join(variant_sources) if variant_sources else "No sources"
            variants_list.append(variant)

        entry.variants_display = variants_list
        processed_results.append(entry)

    context = {
        'query': display_query,
        'field': field,
        'whole_word': whole_word,
        'match_accents': match_accents,
        'include_examples': include_examples,
        'results': processed_results,
        'all_pos': all_pos,
        'selected_pos': selected_pos,
        'all_sources': all_sources,
        'selected_source': selected_source,
        'highlight_opts': {
            'query': display_query,
            'whole_word': whole_word,
            'match_accents': match_accents,
        },
    }

    return render(request, 'search.html', context)

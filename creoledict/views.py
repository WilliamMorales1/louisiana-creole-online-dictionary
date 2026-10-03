import re

from django.core.paginator import Paginator
from django.db import connection
from django.db.models import Prefetch, Q
from django.shortcuts import render

from .models import POS, Entry, Source, Variant
from .normalize import fold, plain

MAX_QUERY_LENGTH = 100
PAGE_SIZE = 50


def text_match(columns, query, whole_word, match_accents):
    """text_match builds an OR of lookups on the stored folded/plain copies of columns."""
    suffix = 'folded' if match_accents else 'plain'
    needle = fold(query) if match_accents else plain(query)
    if whole_word:
        # Postgres spells word boundaries \y; Django's SQLite REGEXP uses Python's re.
        boundary = r'\y' if connection.vendor == 'postgresql' else r'\b'
        lookup, value = 'regex', f'{boundary}{re.escape(needle)}{boundary}'
    else:
        lookup, value = 'contains', needle
    match = Q()
    for column in columns:
        match |= Q(**{f'{column}_{suffix}__{lookup}': value})
    return match


# --- Main Search View ---
def search_dictionary(request):
    query = request.GET.get('q', '').strip()[:MAX_QUERY_LENGTH]
    field = request.GET.get('field', 'headword')
    whole_word = 'whole_word' in request.GET
    match_accents = 'match_accents' in request.GET
    include_examples = 'include_examples' in request.GET
    selected_pos = request.GET.get('part_of_speech', '')
    selected_source = request.GET.get('source', '')

    display_query = query

    # --- Populate dropdowns ---
    all_pos = POS.objects.exclude(part_of_speech__isnull=True).exclude(part_of_speech='') \
        .values_list('part_of_speech', flat=True).distinct().order_by('part_of_speech')

    all_sources = Source.objects.filter(
        Q(entry__isnull=False) | Q(variant__isnull=False)
    ).exclude(text__isnull=True).exclude(text='') \
        .values_list('text', flat=True).distinct().order_by('text')

    # --- Apply search query and filters in the database ---
    entries = Entry.objects.all()
    if query:
        if field == 'definitions':
            columns = ['definitions__gloss']
            if include_examples:
                columns.append('definitions__examples')
        else:
            columns = ['headword', 'variants__text']
        entries = entries.filter(text_match(columns, query, whole_word, match_accents))
    if selected_pos:
        entries = entries.filter(parts_of_speech__part_of_speech=selected_pos)
    if selected_source:
        entries = entries.filter(
            Q(sources__text=selected_source) |
            Q(variants__sources__text=selected_source)
        )

    variants_prefetch = Prefetch('variants', queryset=Variant.objects.prefetch_related('sources'))
    results = entries.distinct().order_by('headword_folded', 'id').prefetch_related(
        'definitions', 'parts_of_speech', 'sources', variants_prefetch
    )
    page = Paginator(results, PAGE_SIZE).get_page(request.GET.get('page'))

    # --- Prepare sources for display ---
    processed_results = []
    for entry in page:
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
        'result_count': page.paginator.count,
        'page': page,
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

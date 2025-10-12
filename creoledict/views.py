from django.shortcuts import render
from .models import Entry, POS, Source
import unicodedata
from django.db.models import Q

def search_dictionary(request):
    query = request.GET.get('q', '')
    field = request.GET.get('field', 'headword')
    whole_word = 'whole_word' in request.GET
    match_accents = 'match_accents' in request.GET
    selected_pos = request.GET.get('part_of_speech', '')
    selected_source = request.GET.get('source', '')

    # Base queryset
    results = Entry.objects.all().prefetch_related(
        'definitions', 'parts_of_speech', 'sources', 'variants__sources'
    )

    # Populate POS dropdown
    all_pos = (
        POS.objects.exclude(part_of_speech__isnull=True)
        .exclude(part_of_speech__exact='')
        .values_list('part_of_speech', flat=True)
        .distinct()
        .order_by('part_of_speech')
    )

    # Populate Sources dropdown (include entry and variant sources, no duplicates)
    all_sources = (
        Source.objects.filter(
            Q(entry__isnull=False) | Q(variant__isnull=False)
        )
        .exclude(text__isnull=True)
        .exclude(text__exact='')
        .values_list('text', flat=True)
        .distinct()
        .order_by('text')
    )

    # --- Apply search filter only if query is given ---
    if query.strip():
        search_query = query

        # Handle accent normalization
        if not match_accents:
            def strip_accents(s):
                return ''.join(
                    c for c in unicodedata.normalize('NFD', s)
                    if unicodedata.category(c) != 'Mn'
                )
            search_query = strip_accents(search_query)

        if field == 'definitions':
            results = results.filter(definitions__text__icontains=search_query)
        else:
            if whole_word:
                all_entries = results
                matched_ids = []
                for entry in all_entries:
                    value = getattr(entry, field, '') or ''
                    comp_value = value
                    comp_search = search_query
                    if not match_accents:
                        comp_value = ''.join(
                            c for c in unicodedata.normalize('NFD', comp_value)
                            if unicodedata.category(c) != 'Mn'
                        )
                        comp_search = ''.join(
                            c for c in unicodedata.normalize('NFD', comp_search)
                            if unicodedata.category(c) != 'Mn'
                        )
                    words = comp_value.split()
                    if any(w.lower() == comp_search.lower() for w in words):
                        matched_ids.append(entry.id)
                results = results.filter(id__in=matched_ids)
            else:
                results = results.filter(**{f'{field}__icontains': search_query})

    # --- Apply part_of_speech filter ---
    if selected_pos:
        results = results.filter(parts_of_speech__part_of_speech=selected_pos)

    # --- Apply source filter ---
    if selected_source:
        results = results.filter(
            Q(sources__text=selected_source) | Q(variants__sources__text=selected_source)
        )

    # Process sources for display
    processed_results = []
    for entry in results:
        # Only sources directly tied to the entry (exclude variant sources)
        entry_sources = [
            s.text.strip() for s in entry.sources.all()
            if s.text and s.text.strip() and getattr(s, 'variant', None) is None
        ]
        entry.sources_display = ', '.join(entry_sources) if entry_sources else "No sources"

        # Variant sources
        entry.variants_display = []
        for variant in entry.variants.all():
            variant_sources = [
                s.text.strip() for s in variant.sources.all()
                if s.text and s.text.strip()
            ]
            variant.sources_display = ', '.join(variant_sources) if variant_sources else "No sources"
            entry.variants_display.append(variant)

        processed_results.append(entry)

    context = {
        'query': query,
        'field': field,
        'whole_word': whole_word,
        'match_accents': match_accents,
        'results': processed_results,
        'all_pos': all_pos,
        'selected_pos': selected_pos,
        'all_sources': all_sources,
        'selected_source': selected_source,
        'highlight_opts': {
            'query': query,
            'whole_word': whole_word,
            'match_accents': match_accents,
        },
    }

    return render(request, 'search.html', context)

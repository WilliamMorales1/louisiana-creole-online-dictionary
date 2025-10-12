from django.shortcuts import render
from .models import Entry, POS
import unicodedata

def search_dictionary(request):
    query = request.GET.get('q', '')
    field = request.GET.get('field', 'headword')
    whole_word = 'whole_word' in request.GET
    match_accents = 'match_accents' in request.GET
    selected_pos = request.GET.get('part_of_speech', '')

    # Base queryset
    results = Entry.objects.all().prefetch_related('definitions', 'parts_of_speech')

    # Populate POS dropdown (from related table)
    all_pos = (
        POS.objects.exclude(part_of_speech__isnull=True)
        .exclude(part_of_speech__exact='')
        .values_list('part_of_speech', flat=True)
        .distinct()
        .order_by('part_of_speech')
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
                        def strip_accents(s):
                            return ''.join(
                                c for c in unicodedata.normalize('NFD', s)
                                if unicodedata.category(c) != 'Mn'
                            )
                        comp_value = strip_accents(comp_value)
                        comp_search = strip_accents(comp_search)
                    words = comp_value.split()
                    if any(w.lower() == comp_search.lower() for w in words):
                        matched_ids.append(entry.id)
                results = results.filter(id__in=matched_ids)
            else:
                results = results.filter(**{f'{field}__icontains': search_query})

    # --- Apply part_of_speech filter ---
    if selected_pos:
        results = results.filter(parts_of_speech__part_of_speech=selected_pos)

    context = {
        'query': query,
        'field': field,
        'whole_word': whole_word,
        'match_accents': match_accents,
        'results': results.distinct(),
        'all_pos': all_pos,
        'selected_pos': selected_pos,
        'highlight_opts': {
            'query': query,
            'whole_word': whole_word,
            'match_accents': match_accents,
        },
    }

    return render(request, 'search.html', context)

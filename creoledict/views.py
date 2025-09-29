from django.shortcuts import render
from .models import Entry
from django.db.models import Q

def search_dictionary(request):
    query = request.GET.get('q', '')
    field = request.GET.get('field', 'headword')
    whole_word = 'whole_word' in request.GET
    match_accents = 'match_accents' in request.GET

    results = []

    if query:
        search_query = query

        # If not matching accents, normalize text to remove accents
        if not match_accents:
            import unicodedata
            def strip_accents(s):
                return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
            search_query = strip_accents(search_query)
            # Note: In real use, you might also strip accents from model fields during filtering

        # Construct lookup
        if whole_word:
            lookup = f'{field}__regex'
            regex = fr'\b{search_query}\b'  # \b = word boundary
            results = Entry.objects.filter(**{lookup: regex})
        else:
            lookup = f'{field}__icontains'
            results = Entry.objects.filter(**{lookup: search_query})

    context = {
        'query': query,
        'field': field,
        'whole_word': whole_word,
        'match_accents': match_accents,
        'results': results
    }
    return render(request, 'search.html', context)

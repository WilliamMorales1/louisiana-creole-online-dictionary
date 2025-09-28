from django.shortcuts import render
from .models import Entry

def search_dictionary(request):
    query = request.GET.get('q', '')
    field = request.GET.get('field', 'headword')  # default search in headword
    results = []

    if query:
        if field == 'headword':
            results = Entry.objects.filter(headword__icontains=query)
        elif field == 'content':
            results = Entry.objects.filter(content__icontains=query)
    
    context = {
        'query': query,
        'field': field,
        'results': results,
    }
    return render(request, 'search.html', context)
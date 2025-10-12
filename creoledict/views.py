from django.shortcuts import render
from .models import Entry, Variant, Source, Definition, POS
from django.db.models import Q, Prefetch
import unicodedata

def normalize_text(text):
    # Normalize to NFD (decomposed) form
    return unicodedata.normalize('NFD', text)

def strip_accents(text):
    text = unicodedata.normalize('NFD', text)
    return ''.join(c for c in text if unicodedata.category(c) != 'Mn')

def search_dictionary(request):
    query = request.GET.get('q', '').strip()
    field = request.GET.get('field', 'headword')
    whole_word = 'whole_word' in request.GET
    match_accents = 'match_accents' in request.GET
    selected_pos = request.GET.get('part_of_speech', '')
    selected_source = request.GET.get('source', '')

    if not match_accents:
        # Normalize and strip accents from query
        query = strip_accents(query)

    # Prefetch related objects to avoid N+1 queries
    variants_prefetch = Prefetch('variants', queryset=Variant.objects.prefetch_related('sources'))
    results = Entry.objects.all().prefetch_related(
        'definitions',
        'parts_of_speech',
        'sources',
        variants_prefetch
    ).distinct()

    # --- Populate POS dropdown ---
    all_pos = POS.objects.exclude(part_of_speech__isnull=True).exclude(part_of_speech='') \
        .values_list('part_of_speech', flat=True).distinct().order_by('part_of_speech')

    # --- Populate Sources dropdown (entry + variant sources) ---
    all_sources = Source.objects.filter(
        Q(entry__isnull=False) | Q(variant__isnull=False)
    ).exclude(text__isnull=True).exclude(text='') \
        .values_list('text', flat=True).distinct().order_by('text')

    # --- Apply search query ---
    if query:
        search_query = query
        if not match_accents:
            search_query = strip_accents(search_query)

        if field == 'definitions':
            results = results.filter(definitions__text__icontains=search_query)
        else:
            if whole_word:
                # Whole-word search across headword and variants
                matched_ids = []
                for entry in results:
                    # Check headword
                    value = entry.headword
                    comp_value = value if match_accents else strip_accents(value)
                    comp_search = search_query
                    if any(w.lower() == comp_search.lower() for w in comp_value.split()):
                        matched_ids.append(entry.id)
                        continue

                    # Check variants
                    for variant in entry.variants.all():
                        v_text = variant.text or ''
                        comp_variant = v_text if match_accents else strip_accents(v_text)
                        if any(w.lower() == comp_search.lower() for w in comp_variant.split()):
                            matched_ids.append(entry.id)
                            break
                results = results.filter(id__in=matched_ids)
            else:
                matched_ids = []
                for entry in results:
                    head = entry.headword or ''
                    comp_head = head if match_accents else strip_accents(head)
                    if search_query.lower() in comp_head.lower():
                        matched_ids.append(entry.id)
                        continue

                    for variant in entry.variants.all():
                        v_text = variant.text or ''
                        comp_variant = v_text if match_accents else strip_accents(v_text)
                        if search_query.lower() in comp_variant.lower():
                            matched_ids.append(entry.id)
                            break

                results = results.filter(id__in=matched_ids)

    # --- Filter by Part of Speech ---
    if selected_pos:
        results = results.filter(parts_of_speech__part_of_speech=selected_pos)

    # --- Filter by Source (entry or variant) ---
    if selected_source:
        results = results.filter(
            Q(sources__text=selected_source) |
            Q(variants__sources__text=selected_source)
        ).distinct()

    # --- Process sources for display ---
    processed_results = []

    for entry in results:
        # --- Entry-level sources only ---
        entry_sources = [
            s.text.strip() 
            for s in entry.sources.all() 
            if s.text and s.text.strip() and s.variant_id is None
        ]
        entry.sources_display = ', '.join(entry_sources) if entry_sources else "No sources"

        # --- Variants with their own sources ---
        variants_list = []
        for variant in entry.variants.all():
            # Only get sources linked to this variant
            variant_sources = [
                s.text.strip() 
                for s in variant.sources.all() 
                if s.text and s.text.strip() and s.variant_id == variant.id
            ]
            variant.sources_display = ', '.join(variant_sources) if variant_sources else "No sources"
            variants_list.append(variant)

        entry.variants_display = variants_list
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

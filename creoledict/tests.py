from django.test import TestCase

from .models import POS, Definition, Entry, Source, Variant


class SearchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.bel = Entry.objects.create(headword='bèl')
        Definition.objects.create(entry=cls.bel, def_number=1, gloss='beautiful', examples='Li bèl.')
        POS.objects.create(entry=cls.bel, part_of_speech='adj')
        Source.objects.create(entry=cls.bel, text='CA')

        cls.manje = Entry.objects.create(headword='manjé')
        Definition.objects.create(entry=cls.manje, def_number=1, gloss='to eat', examples=None)
        variant = Variant.objects.create(entry=cls.manje, text='manzhé')
        Source.objects.create(entry=cls.manje, variant=variant, text='PC')

        cls.tobe = Entry.objects.create(headword='été')
        Definition.objects.create(entry=cls.tobe, def_number=1, gloss='summer; tomato season')

    def search(self, **params):
        response = self.client.get('/', params)
        self.assertEqual(response.status_code, 200)
        return {entry.headword for entry in response.context['results']}

    def test_search_fields_follow_saves(self):
        entry = Entry.objects.create(headword='Éklè')
        self.assertEqual((entry.headword_folded, entry.headword_plain), ('éklè', 'ekle'))
        entry.headword = 'Zozo'
        entry.save()
        entry.refresh_from_db()
        self.assertEqual((entry.headword_folded, entry.headword_plain), ('zozo', 'zozo'))

    def test_headword_ignores_accents_by_default(self):
        self.assertEqual(self.search(q='bel'), {'bèl'})
        self.assertEqual(self.search(q='BÈL'), {'bèl'})

    def test_match_accents(self):
        self.assertEqual(self.search(q='bel', match_accents='on'), set())
        self.assertEqual(self.search(q='bèl', match_accents='on'), {'bèl'})

    def test_variant_matches_headword_search(self):
        self.assertEqual(self.search(q='manzh'), {'manjé'})

    def test_definitions_and_examples(self):
        self.assertEqual(self.search(q='li', field='definitions'), set())
        self.assertEqual(self.search(q='li', field='definitions', include_examples='on'), {'bèl'})

    def test_whole_word(self):
        self.assertEqual(self.search(q='to', field='definitions'), {'manjé', 'été'})
        self.assertEqual(self.search(q='to', field='definitions', whole_word='on'), {'manjé'})

    def test_filters(self):
        self.assertEqual(self.search(part_of_speech='adj'), {'bèl'})
        self.assertEqual(self.search(source='PC'), {'manjé'})

    def test_pages_keep_filters_and_order(self):
        Entry.objects.bulk_create(Entry(headword=f'zz{n:03}', headword_folded=f'zz{n:03}', headword_plain=f'zz{n:03}') for n in range(120))
        first = self.client.get('/', {'q': 'zz'})
        self.assertEqual(first.context['result_count'], 120)
        self.assertEqual([e.headword for e in first.context['results']], [f'zz{n:03}' for n in range(50)])
        self.assertContains(first, '?q=zz&amp;page=2')

        last = self.client.get('/', {'q': 'zz', 'page': 3})
        self.assertEqual([e.headword for e in last.context['results']], [f'zz{n:03}' for n in range(100, 120)])
        self.assertNotContains(last, 'Next')

        for bad_page in ('0', '999', 'abc', "1' OR 1=1"):
            with self.subTest(page=bad_page):
                self.assertEqual(self.client.get('/', {'q': 'zz', 'page': bad_page}).status_code, 200)

    def test_hostile_input_is_literal(self):
        for query in ["'; DROP TABLE dictionary_entries; --", "' OR '1'='1", '%', '_', '\\', '.*', '(', '[a-z]+']:
            for whole_word in ({}, {'whole_word': 'on'}):
                with self.subTest(query=query, **whole_word):
                    self.assertEqual(self.search(q=query, **whole_word), set())
        self.assertEqual(Entry.objects.count(), 3)

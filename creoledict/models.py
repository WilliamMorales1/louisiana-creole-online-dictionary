from django.db import models

from .normalize import fold, plain


def search_field():
    return models.TextField(blank=True, default='', editable=False)


class SearchableModel(models.Model):
    """SearchableModel keeps <field>_folded and <field>_plain copies of SEARCHABLE fields for DB-side search."""

    SEARCHABLE = ()

    class Meta:
        abstract = True

    def refresh_search_fields(self):
        for name in self.SEARCHABLE:
            value = getattr(self, name)
            setattr(self, f'{name}_folded', fold(value))
            setattr(self, f'{name}_plain', plain(value))

    def save(self, *args, **kwargs):
        self.refresh_search_fields()
        super().save(*args, **kwargs)


class Entry(SearchableModel):
    SEARCHABLE = ('headword',)

    headword = models.CharField(max_length=255)
    headword_folded = search_field()
    headword_plain = search_field()

    class Meta:
        db_table = 'dictionary_entries'  # Must match your existing table name

    def __str__(self):
        return self.headword


class Variant(SearchableModel):
    SEARCHABLE = ('text',)

    entry = models.ForeignKey(Entry, on_delete=models.CASCADE, related_name="variants")
    text = models.TextField()
    text_folded = search_field()
    text_plain = search_field()

    class Meta:
        db_table = 'variants'  # Must match your existing table name

    def __str__(self):
        return f"{self.entry.headword} ({self.text})"


class Source(models.Model):
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE, related_name="sources")
    variant = models.ForeignKey(
        Variant, on_delete=models.CASCADE, related_name="sources", null=True, blank=True
    )
    text = models.TextField()

    class Meta:
        db_table = 'sources'  # Must match your existing table name

    def __str__(self):
        # Only access variant.text if variant exists
        if self.variant_id:  # safer than self.variant
            return f"{self.variant.text} ({self.text})"
        else:
            return f"{self.entry.headword} ({self.text})"


class Definition(SearchableModel):
    SEARCHABLE = ('gloss', 'examples')

    entry = models.ForeignKey(Entry, on_delete=models.CASCADE, related_name="definitions")
    def_number = models.PositiveIntegerField()
    gloss = models.TextField()
    examples = models.TextField(blank=True, null=True)
    gloss_folded = search_field()
    gloss_plain = search_field()
    examples_folded = search_field()
    examples_plain = search_field()

    class Meta:
        db_table = 'definitions'  # Must match your existing table name

    def __str__(self):
        return f"{self.entry.headword} ({self.def_number})"


class POS(models.Model):
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE, related_name="parts_of_speech")
    part_of_speech = models.TextField()

    class Meta:
        db_table = 'entry_parts_of_speech'  # Must match your existing table name

    def __str__(self):
        return f"{self.entry.headword} ({self.part_of_speech})"

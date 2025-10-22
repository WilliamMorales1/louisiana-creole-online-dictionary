from django.db import models

class Entry(models.Model):
    headword = models.CharField(max_length=255)

    class Meta:
        managed = False  # Don't let Django try to create the table
        db_table = 'dictionary_entries'  # Must match your existing table name

    def __str__(self):
        return self.headword


class Variant(models.Model):
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE, related_name="variants")
    text = models.TextField()

    class Meta:
        managed = False  # Don't let Django try to create the table
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
        managed = False  # Don't let Django try to create the table
        db_table = 'sources'  # Must match your existing table name

    def __str__(self):
        # Only access variant.text if variant exists
        if self.variant_id:  # safer than self.variant
            return f"{self.variant.text} ({self.text})"
        else:
            return f"{self.entry.headword} ({self.text})"


class Definition(models.Model):
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE, related_name="definitions")
    def_number = models.PositiveIntegerField()
    gloss = models.TextField()
    examples = models.TextField(blank=True)

    class Meta:
        managed = False  # Don't let Django try to create the table
        db_table = 'definitions'  # Must match your existing table name

    def __str__(self):
        return f"{self.entry.headword} ({self.def_number})"


class POS(models.Model):
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE, related_name="parts_of_speech")
    part_of_speech = models.TextField()

    class Meta:
        managed = False  # Don't let Django try to create the table
        db_table = 'entry_parts_of_speech'  # Must match your existing table name

    def __str__(self):
        return f"{self.entry.headword} ({self.part_of_speech})"

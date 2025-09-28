from django.db import models

class Entry(models.Model):
    headword = models.CharField(max_length=200)
    content = models.TextField()

    class Meta:
        managed = False  # Don't let Django try to create the table
        db_table = 'entries'  # Must match your existing table name

    def __str__(self):
        return self.headword
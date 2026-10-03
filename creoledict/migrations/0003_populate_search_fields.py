from django.db import migrations

from creoledict.normalize import fold, plain

SEARCHABLE = {
    'Entry': ('headword',),
    'Variant': ('text',),
    'Definition': ('gloss', 'examples'),
}


def populate(apps, schema_editor):
    for model_name, sources in SEARCHABLE.items():
        model = apps.get_model('creoledict', model_name)
        targets = [f'{name}_{kind}' for name in sources for kind in ('folded', 'plain')]
        rows = list(model.objects.all())
        for row in rows:
            for name in sources:
                value = getattr(row, name)
                setattr(row, f'{name}_folded', fold(value))
                setattr(row, f'{name}_plain', plain(value))
        model.objects.bulk_update(rows, targets, batch_size=500)


class Migration(migrations.Migration):

    dependencies = [
        ('creoledict', '0002_search_fields'),
    ]

    operations = [
        migrations.RunPython(populate, migrations.RunPython.noop),
    ]

from django.contrib import admin
from .models import Entry, Definition, POS

# --- Inline for Definitions inside Entry ---
class DefinitionInline(admin.TabularInline):
    model = Definition
    extra = 1  # number of empty forms to show

# --- Entry Admin ---
@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_display = ("headword",)
    search_fields = ("headword", "definitions__gloss")
    inlines = [DefinitionInline]

# --- Definition Admin (optional standalone view) ---
@admin.register(Definition)
class DefinitionAdmin(admin.ModelAdmin):
    list_display = ("entry", "gloss", "examples")
    search_fields = ("gloss", "entry__headword")

@admin.register(POS)
class POSAdmin(admin.ModelAdmin):
    list_display = ("entry", "part_of_speech")
    search_fields = ("part_of_speech", "entry__headword")


# login: wsm52, kourivini
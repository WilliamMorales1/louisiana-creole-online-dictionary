from django.contrib import admin
from .models import Entry, Definition, POS, Variant, Source

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
    ordering = ("headword", "definitions__gloss")

@admin.register(Definition)
class DefinitionAdmin(admin.ModelAdmin):
    list_display = ("entry", "gloss", "examples")
    search_fields = ("gloss", "entry__headword")
    ordering = ("gloss",)

@admin.register(POS)
class POSAdmin(admin.ModelAdmin):
    list_display = ("entry", "part_of_speech")
    search_fields = ("part_of_speech", "entry__headword")
    ordering = ("part_of_speech", "entry")

class SourceInline(admin.TabularInline):
    model = Source
    extra = 0

@admin.register(Variant)
class VariantAdmin(admin.ModelAdmin):
    list_display = ("text", "entry",)
    search_fields = ("text", "entry__headword", "sources__text")
    inlines = [SourceInline]
    ordering = ("text",)

# login: wsm52, kourivini
# Louisiana Creole Online Dictionary

**Live at [creole-dictionary.fly.dev](https://creole-dictionary.fly.dev/)**

A searchable web edition of the Valdman *Dictionary of Louisiana Creole* for Kouri-Vini, a critically endangered language. Built with members of the LSU Creole Club.

- 5,139 entries, 6,519 senses and 5,055 spelling variants, each with its source attestations
- Search headwords and variants, or glosses and example sentences
- Accent-insensitive by default (`manje` finds `manjé`), with optional exact-accent and whole-word matching
- Filter by part of speech or source

## Running locally

1. Download files and open folder in VSCode.
2. Install Python if you don't already have it.
3. Open terminal and run the following commands:
   1. git clone https://github.com/WilliamMorales1/louisiana-creole-online-dictionary
   2. cd louisiana-creole-online-dictionary
   3. pip install -r requirements.txt
   4. DJANGO_DEBUG=1 python manage.py migrate --fake-initial
   5. DJANGO_DEBUG=1 python manage.py runserver
4. Go to http://127.0.0.1:8000/.

Local dev uses the bundled `dictionary_entries.db` (SQLite). `DJANGO_DEBUG=1` is required locally; without it the app runs in production mode and refuses to start unless `DJANGO_SECRET_KEY` is set.

## Configuration

| Variable | Purpose |
| --- | --- |
| `DJANGO_SECRET_KEY` | Required in production. |
| `DJANGO_DEBUG` | `1` for local development only. |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated hostnames, e.g. `creole-dictionary.fly.dev`. |
| `DATABASE_URL` | Postgres URL in production; falls back to SQLite when unset. |

## Deploying (Fly.io)

```sh
fly launch --no-deploy --copy-config
fly secrets set DJANGO_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(50))")
fly secrets set DATABASE_URL=postgres://...
fly deploy
```

`fly deploy` runs migrations automatically. To copy the dictionary from SQLite into an empty Postgres database:

```sh
DJANGO_DEBUG=1 python manage.py dumpdata creoledict -o dict.json.gz
DJANGO_DEBUG=1 DATABASE_URL=postgres://... python manage.py loaddata dict.json.gz
fly ssh console -C "python manage.py createsuperuser"
```



TODO:

1. fix typos/formatting in definition.gloss and definition.examples
2. update kouri-vini orthography in definition.examples
3. add documentation for abbreviations and other langauge info
4. make installation easier

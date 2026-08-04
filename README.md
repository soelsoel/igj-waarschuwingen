# IGJ Waarschuwingen

Overzicht van waarschuwingen over medische hulpmiddelen van de [Inspectie Gezondheidszorg en Jeugd](https://www.igj.nl), als statische site op GitHub Pages:

**https://soelsoel.github.io/igj-waarschuwingen/**

Installeerbaar op Android/iOS via "Toevoegen aan startscherm"; het archief blijft offline beschikbaar.

## Hoe het werkt

De RSS-feed van igj.nl stuurt geen CORS-headers en bevat altijd maar de laatste 20 items. De browser kan hem dus niet zelf ophalen, en een archief bestaat alleen als iemand de items opspaart. Daarom:

1. `.github/workflows/update-feed.yml` draait elke dag (en op knopdruk via **Actions → Update feed → Run workflow**).
2. `scripts/build_data.py` haalt de feed op met `feed_parser.py` en voegt nieuwe items toe aan `data/warnings.json`, ontdubbeld op `guid`.
3. Zijn er nieuwe waarschuwingen, dan commit de workflow het bestand. Zo niet, dan gebeurt er niets.
4. `index.html` + `app.js` lezen die JSON en verzorgen overzicht, zoeken, archief en detailpagina's (hash-routing, want GitHub Pages kan geen URL-rewrites).

Lokaal bekijken:

```bash
python -m http.server 8000
```

> GitHub schakelt geplande workflows uit na 60 dagen zonder repo-activiteit. Staat de data stil, kijk dan bij **Actions** of de workflow nog aanstaat en klik zo nodig op *Enable workflow*.

## Flask-versie (niet meer in gebruik)

`app.py`, `database.py`, `wsgi.py`, `templates/` en `DEPLOY.md` zijn de oude serverversie die op PythonAnywhere draaide, met SQLite (`igj_warnings.db`) als opslag. Die blijft hier als referentie staan; het archief in `data/warnings.json` is eruit overgenomen.

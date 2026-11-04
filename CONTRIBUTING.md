# Contribuer à Who Did It

## Ajouter une traduction (nouvelle langue)

Le système de traduction multilingue repose sur le mécanisme standard de Home Assistant :

- `custom_components/who_did_it/strings.json` : source en anglais (ne pas modifier les clés).
- `custom_components/who_did_it/translations/<lang>.json` : une traduction par langue, où `<lang>` est le code ISO 639-1 (ex. `fr`, `en`, `de`, `es`...).

Pour ajouter une langue :

1. Copiez `custom_components/who_did_it/translations/en.json` vers `custom_components/who_did_it/translations/<lang>.json`.
2. Traduisez **uniquement les valeurs** (titres, descriptions, noms). **Ne modifiez jamais les clés** (`config`, `services`, `entity`, `name`, `icon`, etc.), elles doivent rester identiques à la source anglaise.
3. Validez le JSON localement :
   ```bash
   python -c "import json; json.load(open('custom_components/who_did_it/translations/<lang>.json'))"
   ```
4. Ouvrez une pull request sur GitHub. La CI validera automatiquement le JSON et la syntaxe.

Toute contribution de traduction se fait donc directement via Git, par simple ajout d'un fichier dans `translations/`.

## Modifier le code

- Le code Python est linté avec Ruff (`ruff.toml` à la racine) : `ruff check custom_components/who_did_it`.
- Les fichiers Python, JSON et YAML sont validés par la CI à chaque push / pull request.
- Gardez le vocabulaire générique : Who Did It ne doit pas faire référence à un appareil précis (lave-vaisselle, lave-linge, animaux...).

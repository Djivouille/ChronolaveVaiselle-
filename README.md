# Woodydit

[![CI](https://github.com/Djivouille/ChronolaveVaiselle-/actions/workflows/ci.yml/badge.svg)](https://github.com/Djivouille/ChronolaveVaiselle-/actions/workflows/ci.yml)

Custom integration Home Assistant générique pour suivre **qui a fait quoi** dans la maison :

- **Suivi des tâches** : comptabilise qui a réalisé chaque tâche, avec anti-triche (cooldown entre deux réalisations).
- **Multi-tâches** : une entrée par tâche — « Lave-vaisselle », « Lave-linge », « Chien »... chacune avec sa propre icône.

Exemples d'utilisation : qui a vidé le lave-vaisselle, qui a sorti le lave-linge, qui a donné à manger au chien.

## Installation

### Via HACS

1. Ajoutez ce dépôt comme dépôt personnalisé dans HACS (catégorie *Integration*).
2. Installez **Woodydit** puis redémarrez Home Assistant.

### Manuelle

1. Copiez le dossier `custom_components/woodydit/` dans le dossier `custom_components/` de votre installation Home Assistant.
2. Redémarrez Home Assistant.

## Configuration

Ajoutez l'intégration via **Paramètres > Appareils et services > Ajouter une intégration > Woodydit** (autant de fois que de tâches à suivre) :

- **Nom** : nom de la tâche (ex. `Lave-vaisselle`, `Lave-linge`, `Chien`).
- **Icône** : icône Material Design affichée sur toutes les entités de la tâche (ex. `mdi:dishwasher`, `mdi:washing-machine`, `mdi:dog`).
- **Capteur binaire déclencheur** (optionnel) : ex. `binary_sensor.lave_linge_en_cours`. Quand il passe de `on` à `off`, la tâche est marquée « à faire ».
- **Personnes** : membres de la famille, séparés par des virgules (ex. `Chloe, Axel, Joelle, Jv`). Un compteur est créé par personne.
- **Délai minimum entre deux réalisations (heures)** : cooldown anti-triche (6 h par défaut).

Tout est modifiable ensuite via **Options** de l'intégration.

## Entités créées

| Entité | Description |
|---|---|
| `binary_sensor.<nom>_pending` | `on` quand la tâche est « à faire » |
| `sensor.<nom>_last_by` | Dernière personne ayant réalisé la tâche |
| `sensor.<nom>_last_at` | Date/heure de la dernière réalisation |
| `sensor.<nom>_<personne>` | Compteur de réalisations par personne (`state_class: total_increasing`) |

Toutes les entités d'une même tâche partagent l'icône configurée. Tous les états sont restaurés après un redémarrage de Home Assistant.

## Services

- `woodydit.done` : enregistre qu'une personne a réalisé la tâche (champ `person`, doit être une personne configurée). Le service s'applique à toutes les entrées où cette personne est configurée.

Règles du service `done` :

- Si la tâche n'est pas « à faire » → refus.
- Si la dernière réalisation date de moins que le cooldown → refus avec `retry_at`.
- Sinon → incrément du compteur de la personne, mise à jour du dernier acteur/date, tâche plus « à faire ».

## Événements

- `woodydit_pending` : la tâche vient d'être marquée « à faire » (capteur déclencheur passé `on` → `off`).
- `woodydit_done` : réalisation validée (`entry_id`, `person`, `count`).
- `woodydit_denied` : réalisation refusée (`entry_id`, `person`, `reason` = `nothing_pending` ou `cooldown`, `retry_at` si cooldown).

## Exemples d'automatisations

Notifier la famille quand le lave-linge a fini (la tâche « Lave-linge » passe « à faire ») :

```yaml
automation:
  - alias: "Lave-linge terminé : prévenir la famille"
    triggers:
      - trigger: event
        event_type: woodydit_pending
        event_data:
          entry_id: !secret entry_id_lave_linge
    actions:
      - action: notify.telegram_maison
        data:
          title: "🧺 Lave-linge 🍽️"
          message: "Cycle terminé, il y a du linge à sortir !"
```

Bouton Telegram « fait ! » pour Chloe (tâche « Lave-vaisselle ») :

```yaml
automation:
  - alias: "Telegram : tâche faite (Chloe)"
    triggers:
      - trigger: event
        event_type: telegram_callback
        event_data:
          command: /tache_faite_chloe
    actions:
      - action: woodydit.done
        data:
          person: Chloe
```

Alerter en cas de tentative de triche (cooldown non respecté) :

```yaml
automation:
  - alias: "Woodydit : tentative de triche"
    triggers:
      - trigger: event
        event_type: woodydit_denied
        event_data:
          reason: cooldown
    actions:
      - action: notify.telegram_maison
        data:
          message: "Tentative de triche détectée ! Réessaie à {{ trigger.event.data.retry_at }}."
```

## Traductions

L'intégration est traduite en **français** et **anglais** (`custom_components/woodydit/translations/`). Pour ajouter une langue, consultez [CONTRIBUTING.md](CONTRIBUTING.md) : il suffit d'ajouter un fichier `translations/<lang>.json` via une pull request Git.

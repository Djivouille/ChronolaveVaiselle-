# Who Did It  <img src="custom_components/who_did_it/logo.png" alt="Logo Who Did It" width="50">

Icône de l'intégration : `mdi:account-question`

[![CI](https://github.com/Djivouille/who_did_it/actions/workflows/ci.yml/badge.svg)](https://github.com/Djivouille/who_did_it/actions/workflows/ci.yml)

Custom integration Home Assistant générique pour suivre **qui a fait quoi** dans la maison :

- **Suivi des tâches** : comptabilise qui a réalisé chaque tâche, avec anti-triche (cooldown entre deux réalisations).
- **Multi-tâches** : une entrée par tâche — « Lave-vaisselle », « Lave-linge », « Chien »... chacune avec sa propre icône.

Exemples d'utilisation : qui a vidé le lave-vaisselle, qui a sorti le lave-linge, qui a donné à manger au chien.

## Installation

### Via HACS (recommandé)

Prérequis : [HACS](https://hacs.xyz/installation/prerequisites/) déjà installé.

1. Dans Home Assistant, ouvrez **HACS** dans le menu latéral.
2. Cliquez sur les **trois points** en haut à droite, puis **Dépôts personnalisés** (*Custom repositories*).
3. Collez l'URL du dépôt et choisissez la catégorie **Integration** :
   - URL : `https://github.com/Djivouille/who_did_it`
   - Catégorie : `Integration`
4. Cliquez sur **Ajouter**, puis fermez la fenêtre.
5. Recherchez **Who Did It** dans HACS, ouvrez la fiche et cliquez sur **Télécharger** (*Download*).
6. **Redémarrez Home Assistant** (Paramètres > Système > Redémarrer).
7. Ajoutez l'intégration : **Paramètres > Appareils et services > Ajouter une intégration**, recherchez **Who Did It** et suivez l'assistant (voir [Configuration](#configuration)).

### Manuelle

1. Copiez le dossier `custom_components/who_did_it/` dans le dossier `custom_components/` de votre installation Home Assistant.
2. Redémarrez Home Assistant.

## Configuration

Ajoutez l'intégration via **Paramètres > Appareils et services > Ajouter une intégration > Who Did It** (autant de fois que de tâches à suivre) :

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

## Carte Lovelace intégrée

L'intégration fournit une carte personnalisée **`custom:who-did-it-card`**, enregistrée automatiquement comme ressource Lovelace (mode storage, aucun ajout manuel nécessaire).

Ajoutez-la depuis l'interface : **Ajouter une carte > Who Did It**. Tout se règle graphiquement :

- **Titre de la carte** (optionnel).
- **Capteur binaire « À faire »** : détecté automatiquement (premier capteur binaire de l'intégration).
- **Afficher le statut** : « à faire » ou « rien à faire ».
- **Afficher la dernière réalisation** : qui et quand.
- **Afficher les compteurs par personne** : détectés automatiquement depuis l'appareil.
- **Afficher les boutons « C'est fait ! »** : chaque bouton appelle le service `who_did_it.done` pour la personne concernée (cooldown anti-triche inclus).

Exemple en YAML :

```yaml
type: custom:who-did-it-card
entity: binary_sensor.lave_vaisselle_pending
name: Lave-vaisselle
show_status: true
show_last_done: true
show_counters: true
show_done_buttons: true
```

> En mode YAML de Lovelace, ajoutez manuellement la ressource `/who_did_it/who_did_it-card.js` de type `module`.

## Services

- `who_did_it.done` : enregistre qu'une personne a réalisé la tâche (champ `person`, doit être une personne configurée). Le service s'applique à toutes les entrées où cette personne est configurée.

Règles du service `done` :

- Si la tâche n'est pas « à faire » → refus.
- Si la dernière réalisation date de moins que le cooldown → refus avec `retry_at`.
- Sinon → incrément du compteur de la personne, mise à jour du dernier acteur/date, tâche plus « à faire ».

## Événements

- `who_did_it_pending` : la tâche vient d'être marquée « à faire » (capteur déclencheur passé `on` → `off`).
- `who_did_it_done` : réalisation validée (`entry_id`, `person`, `count`).
- `who_did_it_denied` : réalisation refusée (`entry_id`, `person`, `reason` = `nothing_pending` ou `cooldown`, `retry_at` si cooldown).

## Exemples d'automatisations

Notifier la famille quand le lave-linge a fini (la tâche « Lave-linge » passe « à faire ») :

```yaml
automation:
  - alias: "Lave-linge terminé : prévenir la famille"
    triggers:
      - trigger: event
        event_type: who_did_it_pending
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
      - action: who_did_it.done
        data:
          person: Chloe
```

Alerter en cas de tentative de triche (cooldown non respecté) :

```yaml
automation:
  - alias: "Who Did It : tentative de triche"
    triggers:
      - trigger: event
        event_type: who_did_it_denied
        event_data:
          reason: cooldown
    actions:
      - action: notify.telegram_maison
        data:
          message: "Tentative de triche détectée ! Réessaie à {{ trigger.event.data.retry_at }}."
```

## Traductions

L'intégration est traduite en **français** et **anglais** (`custom_components/who_did_it/translations/`). Pour ajouter une langue, consultez [CONTRIBUTING.md](CONTRIBUTING.md) : il suffit d'ajouter un fichier `translations/<lang>.json` via une pull request Git.

# ChronolaveVaiselle

Custom integration Home Assistant pour le lave-vaisselle :

1. **Chronomètre de cycle** : capteur du temps restant avant la fin du lavage.
2. **Suivi des vidages** : comptabilise qui vide le lave-vaisselle, avec anti-triche (cooldown entre deux vidages).

## Installation

### Via HACS

1. Ajoutez ce dépôt comme dépôt personnalisé dans HACS (catégorie *Integration*).
2. Installez **ChronolaveVaiselle** puis redémarrez Home Assistant.

### Manuelle

1. Copiez le dossier `custom_components/chronolavevaiselle/` dans le dossier `custom_components/` de votre installation Home Assistant.
2. Redémarrez Home Assistant.

## Configuration

Ajoutez l'intégration via **Paramètres > Appareils et services > Ajouter une intégration > ChronolaveVaiselle** :

- **Nom** : nom du lave-vaisselle.
- **Durée du cycle par défaut (minutes)** : durée utilisée par le service `start_cycle` quand aucune durée n'est fournie.
- **Capteur binaire de lavage en cours** (optionnel) : ex. `binary_sensor.lavage_vaiselle_en_cours`. Quand il passe de `on` à `off`, la vaisselle est marquée « à ranger ».
- **Personnes** : membres de la famille, séparés par des virgules (ex. `Chloe, Axel, Joelle, Jv`). Un compteur est créé par personne.
- **Délai minimum entre deux vidages (heures)** : cooldown anti-triche (6 h par défaut), comme ton ancien script (`21600 s`).

Tout est modifiable ensuite via **Options** de l'intégration.

## Entités créées

| Entité | Description |
|---|---|
| `sensor.<nom>_temps_restant` | Minutes restantes du cycle (attributs `running`, `cycle_end`) |
| `binary_sensor.<nom>_vaisselle_a_ranger` | `on` quand la vaisselle attend d'être vidée |
| `sensor.<nom>_dernier_vidage_par` | Dernière personne ayant vidé |
| `sensor.<nom>_dernier_vidage_le` | Date/heure du dernier vidage |
| `sensor.<nom>_<personne>` | Compteur de vidages par personne (`state_class: total_increasing`) |

Tous les états sont restaurés après un redémarrage de Home Assistant.

## Services

- `chronolavevaiselle.start_cycle` : démarre le chronomètre (champ optionnel `duration` en minutes).
- `chronolavevaiselle.empty` : enregistre qu'une personne a vidé le lave-vaisselle (champ `person`, doit être une personne configurée).

Règles du service `empty` (idem ton ancien script) :

- Si la vaisselle n'est pas « à ranger » → refus.
- Si le dernier vidage date de moins que le cooldown → refus avec `retry_at`.
- Sinon → incrément du compteur de la personne, mise à jour du dernier acteur/date, vaisselle plus « à ranger ».

## Événements

- `chronolavevaiselle_cycle_ended` : fin du lavage détectée (capteur configuré passé `on` → `off`).
- `chronolavevaiselle_cycle_finished` : chronomètre arrivé à 0.
- `chronolavevaiselle_emptied` : vidage validé (`person`, `count`).
- `chronolavevaiselle_empty_denied` : vidage refusé (`person`, `reason` = `no_dishes_pending` ou `cooldown`, `retry_at` si cooldown).

## Exemples d'automatisations

Notifier la famille à la fin du lavage (remplace l'ancien trigger sur `binary_sensor.lavage_vaiselle_en_cours`) :

```yaml
automation:
  - alias: "Fin de lavage : prévenir la famille"
    triggers:
      - trigger: event
        event_type: chronolavevaiselle_cycle_ended
    actions:
      - action: notify.telegram_maison
        data:
          title: "🔔 Lave-vaisselle 🍽️"
          message: "Cycle terminé, il y a de la vaisselle à sortir !"
          data:
            inline_keyboard: "😇 Vaiselle sorti !:/vaisselle_sorti"
```

Bouton Telegram « vaisselle sortie » pour Chloe (remplace l'ancien script `LaveVaiselle`) :

```yaml
automation:
  - alias: "Telegram : vaisselle sortie (Chloe)"
    triggers:
      - trigger: event
        event_type: telegram_callback
        event_data:
          command: /vaisselle_sorti_chloe
    actions:
      - action: chronolavevaiselle.empty
        data:
          person: Chloe
```

Alerter en cas de tentative de triche (cooldown non respecté) :

```yaml
automation:
  - alias: "Vidage refusé : tricheur !"
    triggers:
      - trigger: event
        event_type: chronolavevaiselle_empty_denied
    actions:
      - action: notify.telegram_maison
        data:
          title: "🔔 Lave Vaiselle 🍽️"
          message: >-
            {{ trigger.event.data.person }} tricheur ! 👿
            Prochain vidage possible à {{ trigger.event.data.retry_at }}.
```

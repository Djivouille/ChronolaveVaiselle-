# ChronolaveVaiselle

Custom integration Home Assistant qui fournit un chronomètre pour le lave-vaisselle : un capteur indique le temps restant avant la fin du cycle.

## Installation

### Via HACS

1. Ajoutez ce dépôt comme dépôt personnalisé dans HACS (catégorie *Integration*).
2. Installez **ChronolaveVaiselle** puis redémarrez Home Assistant.

### Manuelle

1. Copiez le dossier `custom_components/chronolavevaiselle/` dans le dossier `custom_components/` de votre installation Home Assistant.
2. Redémarrez Home Assistant.

## Configuration

Ajoutez l'intégration via **Paramètres > Appareils et services > Ajouter une intégration > ChronolaveVaiselle**, puis renseignez :

- **Nom** : le nom du lave-vaisselle.
- **Durée du cycle par défaut (minutes)** : durée utilisée quand aucune durée n'est fournie au service.

## Utilisation

- **Capteur** `sensor.<nom>_temps_restant` : minutes restantes avant la fin du cycle (0 quand aucun cycle n'est en cours ou terminé). Attributs : `running` (cycle en cours) et `cycle_end` (heure de fin prévue).
- **Service** `chronolavevaiselle.start_cycle` : démarre un cycle. Champ optionnel `duration` (minutes).
- **Événement** `chronolavevaiselle_cycle_finished` : déclenché une fois à la fin de chaque cycle (utile pour notifier ou vider le lave-vaisselle).

Exemple d'automatisation :

```yaml
automation:
  - alias: "Lave-vaisselle terminé"
    triggers:
      - trigger: event
        event_type: chronolavevaiselle_cycle_finished
    actions:
      - action: notify.mobile_app
        data:
          message: "Le lave-vaisselle est terminé !"
```

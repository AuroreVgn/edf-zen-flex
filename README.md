# ⚡ EDF Zen Flex

[![Version](https://img.shields.io/badge/version-0.0.1-blue)](https://github.com/AuroreVgn/edf-zen-flex/releases)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-intégration%20personnalisée-41BDF5?logo=homeassistant)](https://www.home-assistant.io/)
[![HACS](https://img.shields.io/badge/HACS-dépôt%20personnalisé-41BDF5)](https://www.hacs.xyz/)

Intégration personnalisée **Home Assistant** dédiée à l'offre d'électricité **EDF Zen Flex** : consultation des journées Éco, Sobriété et Bonus, suivi annuel, tarifs heures pleines/heures creuses et surveillance des grilles tarifaires.

> [!IMPORTANT]
> Projet communautaire non officiel, indépendant d'EDF. Les prix publics proposés par EDF ne correspondent pas nécessairement aux tarifs de votre contrat. Vérifiez toujours votre facture ou vos conditions contractuelles.

## 🏠 Mes projets Home Assistant

[Découvrir mes projets Home Assistant](https://gentle-suggestion-7c3.notion.site/Mes-projets-Home-Assistant-3eda02eefa8f81a48621c3caeef7fa8e)

## ☕ Soutenir le projet

Si cette intégration vous est utile, vous pouvez [soutenir son développement sur Ko-fi](https://ko-fi.com/aurorevgn).

## ✨ Fonctionnalités

- Consultation des journées **aujourd'hui** et **demain** via le service public EDF, sans compte ni identifiants.
- Distinction des jours **Éco**, **Sobriété** et **Bonus**.
- Historique local des journées récupérées, conservé après redémarrage.
- Décompte annuel des journées connues, Éco, Sobriété et Bonus, avec indication de fiabilité et des jours manquants.
- Saisie facultative d'un compteur initial pour les jours précédant l'installation.
- Quatre tarifs personnalisables : Éco HC/HP et Sobriété HC/HP.
- Calcul local de la période HP/HC et du prix du kWh en cours.
- Import facultatif de la grille publique EDF, **avec confirmation explicite**.
- Vérification quotidienne des tarifs EDF, notification persistante en cas de différence détectée, sans changement automatique des prix enregistrés.
- Capteurs de diagnostic relatifs aux tarifs et aux actualisations.
- Bouton d'actualisation manuelle.
- Compatibilité avec une [carte Lovelace dédiée](https://github.com/AuroreVgn/edf-zen-flex-card), maintenue dans un dépôt séparé.

## 📦 Installation

### Avec HACS (dépôt personnalisé)

1. Ouvrir **HACS** dans Home Assistant.
2. Ajouter `https://github.com/AuroreVgn/edf-zen-flex` comme **dépôt personnalisé** de catégorie **Intégration**.
3. Rechercher **EDF Zen Flex** et l'installer.
4. Redémarrer Home Assistant.
5. Aller dans **Paramètres → Appareils et services → Ajouter une intégration**, puis rechercher **EDF Zen Flex**.

> Les étapes HACS supposent que les fichiers de l'intégration sont bien publiés dans le dépôt. La première release GitHub `0.0.1` est à créer séparément.

### Installation manuelle

Copier le dossier `custom_components/edf_zen_flex` du dépôt dans `<config>/custom_components/edf_zen_flex`, puis redémarrer Home Assistant et ajouter l'intégration depuis **Appareils et services**.

## ⚙️ Configuration

L'assistant de configuration comprend trois étapes.

### 1. Connexion et actualisation

L'intégration utilise un point d'accès public EDF, sans connexion à un espace client. La fréquence d'interrogation est configurable de **5 à 1 440 minutes** (30 minutes par défaut).

### 2. Tarifs du contrat

Renseigner ou vérifier les quatre prix **TTC en €/kWh**, la date d'application, la source de référence et les plages horaires d'heures creuses.

Les plages préremplies sont :

- 00:00–08:00
- 13:00–18:00
- 20:00–24:00

Le reste de la journée est considéré en heures pleines. Les calculs utilisent le fuseau **Europe/Paris**.

Les valeurs initiales sont des références à vérifier, **pas une garantie sur votre contrat**. La date de référence actuellement préremplie est le **15 septembre 2026**.

Pour importer la grille publique EDF, cocher l'option d'import puis vérifier les nouveaux montants affichés. La confirmation des tarifs est obligatoire pour activer le prix actuel du kWh.

### 3. Historique et compteurs initiaux

Si l'intégration est installée en cours d'année, vous pouvez indiquer, jusqu'à une date donnée, les totaux vérifiés des jours **Sobriété** et **Bonus** antérieurs à l'installation.

Vous pouvez consulter les journées passées sur le [calendrier EDF Zen Flex de Hello Watt](https://www.hellowatt.fr/calendrier-zen-flex-edf/).

Le compteur initial est propre à l'année civile et n'est pas reporté sur l'année suivante.

## 📊 Entités créées

### Journées et suivi annuel

| Capteur | Rôle |
| --- | --- |
| Aujourd'hui | Type de journée EDF en cours |
| Demain | Type de journée annoncée pour le lendemain, si connue |
| Jours Éco observés | Jours Éco présents dans l'historique |
| Jours Sobriété observés | Jours Sobriété présents dans l'historique |
| Jours Bonus observés | Jours Bonus présents dans l'historique |
| Jours Sobriété consommés | Décompte annuel tenant compte du compteur initial |
| Jours Sobriété restants | Solde par rapport au quota annuel de 20 jours, sous réserve de fiabilité |
| Jours Éco passés | Décompte calculé des journées passées |
| Jours Éco restants minimum | Estimation minimale selon les règles de calcul actuelles |
| Jours Bonus passés | Décompte des jours Bonus passés |
| Jours à compléter | Jours manquants dans l'historique |

Les journées **Éco**, **Sobriété** et **Bonus** sont trois catégories distinctes. Sur une année intégralement connue, leur somme correspond à **365 jours**, ou **366 lors d'une année bissextile**.

Un historique incomplet ne doit pas être interprété comme un décompte annuel définitif. Les jours Bonus futurs ne sont pas prédits.

### Tarifs et période courante

| Capteur | Rôle |
| --- | --- |
| Tarif Éco heures creuses | Prix contractuel TTC en €/kWh |
| Tarif Éco heures pleines | Prix contractuel TTC en €/kWh |
| Tarif Sobriété heures creuses | Prix contractuel TTC en €/kWh |
| Tarif Sobriété heures pleines | Prix contractuel TTC en €/kWh |
| Période tarifaire | Heures pleines ou heures creuses |
| Prix actuel du kWh | Prix applicable à la période en cours selon la journée connue et les tarifs confirmés |

Les icônes différencient les périodes HC et HP, ainsi que les jours Éco et Sobriété.

### Diagnostics

| Capteur | Signification |
| --- | --- |
| Jours connus | Nombre de journées connues dans l'historique |
| Fiabilité du décompte | État de complétude/cohérence de l'historique |
| Dernière actualisation | Dernière récupération EDF réussie |
| Date d'application des tarifs du contrat | Date saisie et confirmée pour votre contrat |
| Date de la dernière grille EDF publiée | Date de la grille publique identifiée lors d'une vérification réussie |
| Dernière vérification des tarifs EDF | Horodatage de la dernière vérification réussie |

La date des **tarifs du contrat** et celle de la **dernière grille publique EDF** sont volontairement séparées. La seconde peut rester inconnue tant qu'aucune vérification publique n'a abouti.

## 🔔 Surveillance des tarifs EDF

Une vérification est lancée au démarrage, puis chaque jour à **10 h, heure de Paris**. Si la grille publique détectée diffère des tarifs enregistrés, une notification persistante Home Assistant est créée.

**Aucun tarif contractuel n'est modifié automatiquement.** Pour appliquer une nouvelle grille, ouvrir **Paramètres → Appareils et services → EDF Zen Flex → Configurer → Importer les tarifs**, puis contrôler et confirmer les valeurs.

Une vérification infructueuse ne remplace pas les tarifs existants.

## 🗓️ Carte Lovelace

La carte est distribuée dans un dépôt distinct : **[EDF Zen Flex Card](https://github.com/AuroreVgn/edf-zen-flex-card)**.

Elle permet notamment d'afficher le calendrier des journées, les compteurs et les prix de la période courante. Consultez son dépôt pour les instructions d'installation et de configuration.

## ℹ️ Fonctionnement et limites

- L'historique est constitué progressivement à partir des réponses EDF : l'intégration ne reconstitue pas automatiquement toutes les journées passées.
- Le service EDF peut être indisponible ou modifier le format de ses réponses.
- La disponibilité des informations concernant demain dépend des données effectivement publiées.
- Les périodes HP/HC sont définies localement et doivent correspondre à votre contrat.
- Les données et compteurs sont calculés sur l'année civile, en heure de Paris.
- La surveillance des grilles publiques n'est pas une confirmation de leur application à un contrat individuel.

## 🐞 Signaler un problème

Ouvrir une [issue GitHub](https://github.com/AuroreVgn/edf-zen-flex/issues) en indiquant la version de Home Assistant, la version de l'intégration, le comportement attendu et les journaux utiles **sans données personnelles**.

## 📄 Licence

Les informations de licence seront ajoutées au dépôt lors de la publication définitive.

---

**EDF Zen Flex** est un projet indépendant, développé pour la communauté Home Assistant.

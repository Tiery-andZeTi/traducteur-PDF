# Cahier des charges — Livrets pédagogiques bilingues

## But du projet

Produire un **PDF bilingue côte à côte** à partir des workbooks PDF de
ScottsBassLessons.com : chaque page originale (VO anglaise, avec ses
partitions, schémas et photos) est conservée **intacte en image**, et une
**page de traduction française épurée** est insérée en face.

L'objectif n'est PAS de reproduire la mise en page d'origine ni de replacer
le texte là où il était. C'est de fournir une **page de référence** vers
laquelle se tourner quand un mot de vocabulaire échappe au lecteur.

## Vision finale (cap, pas périmètre immédiat)

Flux **100 % local et headless** : une IA locale traduit, un script Python
assemble, le tout sans intervention manuelle ni application graphique. À
terme, piloté par un agent (« traduis ce PDF » → le résultat arrive rangé
dans son dossier). Tout choix technique doit rester compatible avec ce cap.

## Arbitrages déjà retenus (ne pas rediscuter)

1. **Pas de Photoshop.** Éditeur raster, GUI obligatoire, incompatible avec
   un flux agent headless. Abandonné au profit de la stack ci-dessous.

2. **Stack = Python + HTML/CSS.**
   - Génération d'une page HTML de traduction par page VO, depuis un JSON.
   - Rendu HTML → PDF via **WeasyPrint** (pur pip, pas de navigateur).
   - Assemblage / interfoliage VO+VF via **PyMuPDF** (déjà maîtrisé).

3. **Séparation des rôles.** L'extraction du texte et la traduction
   haute-fidélité (EN→FR) sont faites en amont par l'**IA locale**, qui
   produit le JSON. Le script Python ne traduit RIEN : il consomme du JSON
   déjà traduit.

## Invariant absolu (cœur du cahier des charges)

> **Une page VO ↔ une page VF. Une page de traduction ne déborde JAMAIS sur
> la suivante.**

Mécanisme retenu : page au format physique fixe (**A4 portrait** par
défaut). **Autofit par boucle de mesure** : on rend la VF à une taille de
police de départ, on mesure la hauteur du contenu, si ça dépasse la hauteur
utile → on réduit la police d'un cran → on re-rend, jusqu'à ce que ça tienne.
Le débordement devient impossible : c'est la condition d'arrêt de la boucle.

## Schéma JSON (décision d'architecte, à figer ensemble)

Une page VO = un objet. Chaque objet contient une liste de **blocs typés**.
Le gras/italique est porté **à l'intérieur** du texte (fragments), pas au
niveau du bloc.

```
Page
 └── blocks: [ Bloc, Bloc, ... ]

Bloc
 ├── type: "heading" | "paragraph" | "list"
 └── content: [ Fragment, Fragment, ... ]   (ou liste d'items pour "list")

Fragment
 ├── text:   "..."
 ├── bold:   true | false
 └── italic: true | false
```

Mapping HTML trivial : `heading`→`<h2>`, `paragraph`→`<p>`, `list`→`<ul><li>`,
fragment bold→`<strong>`, italic→`<em>`. (Détail exact à verrouiller en début
de session.)

## Ordre de construction (IMPORTANT)

**La première brique à écrire n'est PAS le générateur de pages — c'est un
VALIDATEUR DE JSON sévère.**

Raison : la partie fiable du projet, c'est le script. La variable, c'est la
régularité d'un modèle 12B local à produire du JSON valide et bien fermé sur
des dizaines de pages (virgule oubliée, accolade manquante, clé hallucinée).
Le validateur doit **refuser proprement** et localiser l'erreur (« page 7,
bloc 3, accolade manquante ») plutôt que planter 40 pages plus loin. C'est ce
qui rend le flux « je joue de la basse pendant que ça tourne » réellement
tenable.

Séquence proposée :
1. Validateur JSON (schéma + intégrité)
2. JSON → HTML (mapping des blocs et fragments)
3. CSS de la page de traduction (propre, titres, listes, gras/italique)
4. Autofit (boucle de mesure WeasyPrint)
5. Assemblage PyMuPDF (interfoliage VO/VF)

## Points à trancher avec l'utilisateur (pas du code)

- **Termes laissés en VO ?** Les anciennes règles (« Top Tip! », labels de
  diagrammes en anglais) venaient de la contrainte de boîtes à largeur fixe
  dans l'ancienne approche. Ici, sur une page VF séparée, cette contrainte
  n'existe plus → on PEUT tout traduire. Décision = préférence pédagogique de
  l'utilisateur (cohérence avec la vidéo anglaise vs traduction intégrale),
  à porter côté IA locale, pas côté script.
- **Impression vis-à-vis ?** Si reliure papier recto-VO / verso-VF un jour
  envisagée, l'ordre des pages à l'assemblage devra en tenir compte. Sinon,
  PDF écran simple.

## Contexte de travail de l'utilisateur

- Méthode : **analyse d'abord, validation, ensuite code.** Ne jamais exécuter
  de code sans accord préalable — présenter findings et propositions d'abord.
- Environnement : pas de MS Office, pas d'InDesign/Illustrator. Python +
  PyMuPDF déjà en place. Sensible au coût quota / aux solutions économes.
- Les digressions (souvent musicales) font partie du flux, pas du bruit.

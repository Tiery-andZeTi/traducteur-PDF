# Changelog — Traducteur PDF

Journal des évolutions du projet. Le plus récent en haut.
Format : date (AAAA-MM-JJ) puis changements regroupés par nature
(`Ajouté`, `Changé`, `Corrigé`, `Retiré`, `Décidé`).

> Démarré le 2026-06-26 ; les entrées antérieures sont reconstruites de mémoire
> (le projet n'avait pas de changelog avant cette date), donc les dates exactes
> d'avant le 24 juin sont approximatives.

---

## 2026-06-26

### Décidé
- **Qwen 3.5 9B devient le modèle principal de fait**, en remplacement de Gemma
  (qui ne sera probablement plus relancé). À confirmer après plusieurs
  traductions avant de figer quoi que ce soit dans le code.
- **Réorganisation du dossier projet** lancée : repartir sur une base saine
  (un README unique, ce changelog, un dossier par modèle, séparation
  code / doc / sorties). Code conservé à la racine. Git reporté.

### Décidé (architecture des consignes)
- **Une consigne autonome par modèle.** Chaque `modeles/<llm>/consigne.md` est
  complet et indépendant (le script lit un seul fichier, format 2-blocs). On
  assume la duplication du « contrat » car la vocation du projet est de TESTER
  des LLM : on veut pouvoir réécrire entièrement le prompt d'un modèle sans
  toucher aux autres. Bascule vers « contrat partagé + surcouche » repoussée à
  plus tard (seulement si beaucoup de modèles stables + schéma qui bouge souvent).
- **Anti-divergence** : extraire le contrat (schéma JSON + clés + règles, ce que
  `validateur.py` impose) dans `docs/contrat-sortie.md` = LA référence à recopier
  quand le schéma change.
- **`modeles/_gabarit/`** = prompt neutre (l'actuel `_minimal`) pour calibrer un
  nouveau LLM avant de lui dériver sa consigne dédiée.

### Fait (rangement du dossier)
- Arborescence : `modeles/<llm>/` (`consigne.md` + `README.md`), `docs/`, `_archive/`.
  Consignes déplacées : `_Qwen → modeles/qwen3.5/consigne.md`,
  `CONSIGNE_TRADUCTEUR → modeles/gemma/consigne.md`,
  `_minimal → modeles/_gabarit/consigne.md`, `REGLAGES-MODELES → modeles/COMPARATIF.md`.
- Doc regroupée dans `docs/` (cahier des charges, besoins, réglage LLM, démarrage,
  backlog) + **`docs/contrat-sortie.md`** (le schéma JSON de référence, extrait du
  validateur).
- **`README.md`** racine = point d'entrée unique (remplace les guides épars).
- `traduire_pdf.py` : défaut `--consigne` repointé vers `modeles/gemma/consigne.md`
  (seul changement de code ; les défauts de comportement — température, thinking —
  restent inchangés tant que Qwen n'est pas validé).
- Fichiers de test conservés dans `_archive/` (rien supprimé) ; `__pycache__` purgé.
- Sorties de traduction (PDF + JSON par cours) sorties du projet (dossier Musique).
- Vérifié : validateur OK, et les 3 consignes se chargent (system + rappel).

### Convention
- **Dossier modèle = version dans le nom** : `modeles/qwen3.5/` (et non `qwen/`),
  pour qu'un futur `modeles/qwen3.6/` coexiste sans ambiguïté. `gemma` reste tel
  quel (abandonné, unique).

### Reporté
- Option `--profil <llm>` dans `traduire_pdf.py` (une seule commande au lieu d'une
  par modèle) ; passage sous Git + `.gitignore`.

## 2026-06-24

### Changé
- Stratégie de reprise sur page qui boucle : au lieu de **doubler `max_tokens`**
  (inutile quand c'est une boucle de raisonnement déterministe, pas un manque de
  budget), le 2ᵉ essai **monte la température** via `--retry-temperature`
  (défaut 0.2). Vérifié : page 5 du Level-5 récupérée en passant à 0.2.

### Ajouté
- `CONSIGNE_TRADUCTEUR_Qwen.md` : prompt système court dédié à Qwen.
- `CONSIGNE_TRADUCTEUR_minimal.md`.

### Décidé
- **Principe « un modèle = ses propres réglages »** : les enseignements de Gemma
  (jamais temp 0, thinking off…) ne se transfèrent pas. Mesuré pour Qwen 3.5 9B :
  **thinking ON obligatoire** et **température 0 meilleure** — à l'inverse de Gemma.

## 2026-06-23

### Décidé
- **Réglage de référence Gemma figé** : Q8_0 + contexte 17k + temp 0.6 +
  thinking désactivé. Test de complexité passé.
- **Ministral écarté** comme traducteur : rapide mais classe à tort des pages de
  contenu en « couverture ».
- La qualité résiduelle (solfège) se joue sur le **glossaire**, pas sur les
  paramètres du modèle.

## ~2026-06-20 — Pivot d'architecture

### Changé
- **Abandon du round-trip DOCX.** Nouvelle stack : on rend chaque page VO en
  **image**, le modèle vision lit l'image et produit un **JSON structuré**,
  d'où l'on génère une page VF. Sortie = PDF bilingue (VO, VF, VO, VF…).

### Ajouté
- Cœur du pipeline : `traduire_pdf.py` (orchestrateur), `validateur.py`
  (fait respecter le schéma JSON figé), `json_to_html.py` + `build_pdf.py` +
  `pdf_engine.py` + `style.css` (rendu), `assembler.py` (réassemblage manuel),
  `lancer_traductions.ps1` (lot).
- Documentation initiale : `CAHIER_DES_CHARGES.md`, `BESOINS.md`,
  `DEMARRAGE_RAPIDE.md`, `FEATURES.md`.

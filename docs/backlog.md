# Idées / fonctionnalités à venir — traducteur PDF

Backlog des améliorations envisagées mais pas encore faites.

## À faire

### Sorties dans un sous-dossier dédié (lié à l'automatisation nocturne)
But : éviter d'éparpiller les fichiers de sortie à la racine du projet, et
rendre l'emplacement **prévisible** pour un run headless.

Constat (vérifié dans `traduire_pdf.py`) : aujourd'hui les `_page_NN.json`,
`_workbook.json` et `_raw.txt` sont écrits dans le **dossier courant** (la racine
quand on lance depuis le projet), tandis que le `_FINAL.pdf` se crée **à côté du
PDF source**. Donc si le PDF est ailleurs (ex. dossier surveillé « cours de
basse »), les sorties se retrouvent **scindées** entre deux endroits.

Pistes :
- Une modif d'une ligne : baser les chemins de sortie sur le **dossier du PDF
  source** (`os.path.dirname(args.source_pdf)`) plutôt que sur le dossier courant
  → toutes les sorties au même endroit que le PDF.
- Ou un dossier de travail dédié (`_work/<nom_du_pdf>/`), ignoré par git, où tout
  atterrit (pratique pour archiver ou jeter en bloc).
- Côté `.gitignore` : déjà couvert (`*.pdf`, `*_page_*.json`, `*_workbook.json`,
  `*_FINAL.pdf`, `*.raw.txt` sont ignorés à toute profondeur) → git ne clignote
  pas, ce point est purement du rangement, pas du versionnement.

Note : pour le **lot nocturne**, `lancer_traductions.ps1` règle déjà ce point — il
fait un `Push-Location` dans `traduit\` avant de lancer, donc FINAL + JSON
atterrissent là, et la source réussie part dans `fait\`. Le problème « sorties
éparpillées » ne concerne donc que les **lancements manuels** depuis la racine.

### Mettre à jour `lancer_traductions.ps1` pour Qwen (avant le 1er run nocturne)
Le bloc CONFIG est encore en **Gemma** (`$Model = "google/gemma-4-12b-qat"`) et le
script **ne passe ni `--temperature 0` ni `--consigne`**. Tel quel, un run nocturne
tournerait en Gemma, pas en Qwen. À faire quand l'automatisation sera reprise :
- `$Model = "qwen/qwen3.5-9b"` ;
- ajouter `--temperature 0` et `--consigne modeles\qwen3.5\consigne.md` à l'appel ;
- éventuellement renommer le dossier surveillé `a_traduire\` → « cours de basse »
  si c'est le nom voulu (variable `$DossierIn`).

⚠️ L'automatisation n'a **pas encore été testée** (2026-06-26, encore en phase de
test des LLM). À reprendre une fois Qwen validé. Voir aussi `--resume` ci-dessous
(un run nocturne interrompu doit pouvoir reprendre).

### `--resume` pour `traduire_pdf.py` (priorité : utile sur les longs PDF)
But : sur un PDF de 60–70 pages (~2 h de traitement), si le run s'interrompt
(plantage, veille Windows, coupure), pouvoir **reprendre sans tout refaire**.

Principe : avant d'envoyer une page au modèle, vérifier si son
`<nom>_page_NN.json` existe déjà sur le disque ; si oui, le **recharger** au lieu
de réinterroger le modèle. Ne traiter que les pages manquantes, puis fusionner +
valider + assembler normalement.

Notes :
- Les `_page_NN.json` sont déjà écrits au fur et à mesure → la matière est là,
  il ne manque que la logique « sauter si déjà fait ».
- Prévoir un drapeau `--force` pour ignorer le cache et tout refaire.

### ✅ FAIT (24/06/2026) — Reprise sur boucle : « budget épuisé → relancer avec un peu de température » (Qwen)
Implémenté dans `traduire_pdf.py` : nouvel argument `--retry-temperature` (défaut 0.2).
Sur `BudgetEpuise`, le 2e essai se fait désormais à cette température (au lieu de
doubler `max_tokens`), avec garantie d'une vraie hausse (+0.2 si ≤ `--temperature`).
Reste en backlog : escalade douce multi-paliers (0 → 0.2 → 0.4) si un seul rebond
ne suffit pas. Notes d'origine ci-dessous.

But : rendre les runs nocturnes robustes aux **boucles de raisonnement déterministes**.

Constat (test 12 pages Players-Path-Level-5, 24/06/2026) : avec **Qwen à temp 0**,
la page 5 (label de portée « J Dilla Style Hip Hop » + symbole *forte* 𝆑 + bémols
inline) a fait **boucler** le raisonnement greedy → `BudgetEpuise`. Le filet actuel
(« doubler `max_tokens` ») est **inutile dans ce cas** : la cause n'est pas un manque
de budget mais une boucle, et doubler le budget dans un contexte déjà plein ne fait
que prolonger l'agonie jusqu'au timeout (10 min) → page perdue, assemblage avorté.

Principe : sur `BudgetEpuise` (et/ou timeout), **réessayer la page avec un cheveu de
température** (ex. 0.2) plutôt que (ou en plus de) doubler les tokens — un peu de
hasard casse la boucle déterministe. Vérifié à la main : la page 5 relancée à 0.2 est
passée proprement. Idéal : escalade douce (0 → 0.2 → 0.4) plutôt que doublement du budget.

Lié : décision de fond à trancher pour l'automatisation → **temp 0.2 comme défaut Qwen**
(robuste, qualité « pas mal ») vs **temp 0** (meilleure qualité mais fragile). Voir
`modeles/COMPARATIF.md` et la fiche `modeles/qwen3.5/README.md`.

## Pistes (non engagées)

- **Tester d'autres modèles vision** sur le banc d'essai existant (`--model …`) :
  Pixtral 12B, Qwen2.5-VL (7B/32B), Gemma 3 (12B/27B). Objectif : un modèle qui
  obéit dès le premier jet → rapide ET propre (sans dépendre du thinking).
- **Titre de section pleine largeur** (CSS) : un heading de niveau « section »
  (ex. NOTES DE COURS) s'étale dans la colonne de marge et se coupe sur 2 lignes.
  Petit ajustement CSS si besoin un jour (cosmétique, non bloquant).

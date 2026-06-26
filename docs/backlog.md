# Idées / fonctionnalités à venir — traducteur PDF

Backlog des améliorations envisagées mais pas encore faites.

## À faire

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
`REGLAGES-MODELES.md` et la mémoire [[un-modele-un-reglage]].

## Pistes (non engagées)

- **Tester d'autres modèles vision** sur le banc d'essai existant (`--model …`) :
  Pixtral 12B, Qwen2.5-VL (7B/32B), Gemma 3 (12B/27B). Objectif : un modèle qui
  obéit dès le premier jet → rapide ET propre (sans dépendre du thinking).
- **Titre de section pleine largeur** (CSS) : un heading de niveau « section »
  (ex. NOTES DE COURS) s'étale dans la colonne de marge et se coupe sur 2 lignes.
  Petit ajustement CSS si besoin un jour (cosmétique, non bloquant).

# Réglages des modèles locaux — traducteur PDF

Fiche mémo des configurations testées pour la traduction/extraction des cours
(VO anglaise → JSON structuré français). Dernière mise à jour : **23 juin 2026**.

But : ne pas réapprendre ce qui a déjà marché si on revient sur les réglages plus tard.

> ⚠️ **PRINCIPE (rappel 2026-06-24) : un modèle = ses propres réglages.** Le projet
> a démarré sur Gemma puis a évolué vers le TEST de plusieurs LLM. Les enseignements
> et défauts de Gemma (temp 0.6 minimum, thinking off, « jamais temp 0 »…) **NE se
> transfèrent PAS** aux autres modèles : chaque modèle se recalibre de zéro. Ne pas
> appliquer un réglage Gemma à Qwen par réflexe.

---

## Réglage de référence actuel ✅

**Gemma 3 12B — Q8_0 + contexte 17k + temp 0.6 + thinking DÉSACTIVÉ**

- Se charge entièrement en VRAM (~15 Go).
- ~10× plus rapide que le Q4_0 en pratique.
- Style français plus naturel que le Q4.
- Structure JSON fiable, y compris sur une page complexe (gras + italique mêlés).
- Extraction propre : ignore en-têtes/pieds de page et les partitions, ne garde que le contenu.

---

## Comparatif des configurations Gemma 3 12B

| Réglage | Thinking | Contexte | Temp | Verdict |
|---|---|---|---|---|
| **Q4_0** | **OBLIGATOIRE** | — | — | Sans thinking, « racontait n'importe quoi ». Le thinking était une béquille pour compenser la quantif basse. Style moins naturel. Lent. |
| **Q8_0** | **À DÉSACTIVER** | 17k | 0.6 | Réglage retenu. En thinking → **boucle infinie** (à éviter). Sans thinking → réponse rapide et fiable. |

### Le point clé sur le « thinking »
- **Q4 : thinking ON = nécessaire** (rattrape les délires du modèle).
- **Q8 : thinking OFF = obligatoire** (inutile car le modèle est assez solide, et nuisible → boucle infinie).
- Autrement dit, **passer en Q8 a permis de supprimer le thinking** — ce qui compense en partie le coût mémoire/vitesse du Q8 (plus de tokens de raisonnement à générer).

### Température (testé sur Q8)
- **0.6** (valeur du script) vs **0.3** : **aucune différence sur le JSON** (structure et gras identiques).
- Sur la traduction, le 0.3 n'apporte rien, et est même légèrement moins bon sur des détails
  (laisse « (cont.) » non traduit, ajoute des majuscules après deux-points).
- → On garde **0.6**, plus rapide.
- `top_p` / `top_k` : non explorés à fond. Si un jour on veut resserrer, viser `top_p ~0.9` en plus d'une temp basse.

---

## Autres modèles

| Modèle | Rôle testé | Verdict |
|---|---|---|
| **Qwen 3.5 9B vision** (`qwen/qwen3.5-9b`, Q8_0) | traducteur/extraction | En cours d'itération. Solfège moins fautif que Gemma, traduction plus naturelle. **Thinking ON obligatoire** : OFF testé le 24/06/2026 = INUTILISABLE (bavures). **Température : 0 = meilleure traduction** (mesuré : 0.2 correct, 0.6 moins bon) — À L'INVERSE de Gemma. ⚠️ Le « JAMAIS temp 0 » du script est une cicatrice GEMMA, ne PAS l'appliquer à Qwen. Tendance à **boucler** le raisonnement sur les pages denses → peut épuiser le budget de tokens (cf. test 12 pages, page 5). Prompt dédié court (`CONSIGNE_TRADUCTEUR_Qwen.md`). |
| **Ministral** (Q8 / 32k) | traducteur | Écarté. Rapide (~45 tk/s) mais peu fiable : classe à tort des pages de contenu en « couverture ». |
| **Mistral Small 3.x** | traducteur | À TESTER. Modèle francophone de naissance → plus de chances de connaître le vocabulaire de solfège français. Test prévu : relancer la page Level 5 et comparer les 5 termes fautifs (voir plus bas). |

---

## Limites du modèle ≠ réglages (important)

Les erreurs résiduelles observées ne sont **pas** réglables par quantification / température / thinking.
Ce sont des **lacunes de culture du solfège français** → relèvent du **glossaire**, pas des paramètres.

Erreurs relevées sur la page **Players-Path-Level-5** (vérifiées contre le PNG original) :

| VO anglaise | Sortie fautive du modèle | Correct |
|---|---|---|
| sixteenth note (×3) | croche pointée | **double croche** |
| pickup measure | mesure de reprise | **anacrouse** (ou levée) |
| half note rest | demi-blanche | **demi-pause** (silence de 2 temps) |
| hammer on | comme un marteau | **hammer-on** (laisser en anglais) |
| this extra note | la note de reprise | « cette note supplémentaire » |

Bug récurrent indépendant : **« minim » → « minimin »** (bégaiement de syllabe).
Présent à l'identique en temp 0.6 ET 0.3 → systématique, pas un artefact d'échantillonnage → à corriger par règle de post-traitement/glossaire.

### Conclusion stratégique
- Le **réglage modèle est figé** (Q8 + 17k + temp 0.6 + thinking off) : test de complexité passé.
- La **qualité finale se joue sur le glossaire**, pas sur les paramètres.
- Le solfège est un **domaine fermé** : le glossaire converge vite (les premières leçons apportent
  beaucoup de termes, puis ça se tarit). Le construire en une fois depuis le PDF bilingue de l'ancien
  ordi plutôt que leçon par leçon.
- Un modèle francophone (Mistral Small) peut **réduire** les contresens techniques, mais **ne
  remplacera jamais** le glossaire (habitudes maison + non-traduction volontaire : slap, walking bass…).

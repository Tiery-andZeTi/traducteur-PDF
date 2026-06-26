# Gemma 3 12B vision — fiche modèle

**Statut : abandonné de fait (juin 2026)**, supplanté par [Qwen](../qwen/README.md).
Conservé comme référence historique et comme point de comparaison.
Reste la **consigne par défaut** du script (`--consigne` non précisé → ce fichier).

## Réglages validés

| Réglage | Valeur | Pourquoi |
|---|---|---|
| Quantification | Q8_0 | ~10× plus rapide que Q4 en pratique, style plus naturel. |
| Contexte | 17k | — |
| **Thinking** | **OFF** (obligatoire) | En Q8, thinking ON → boucle infinie. Le modèle est assez solide sans. |
| Température | 0.6 | 0.3 n'apporte rien ; **ne jamais mettre 0** (boucle de raisonnement). |

> ⚠️ Ces réglages sont **propres à Gemma** : ne pas les transférer aux autres
> modèles (cf. principe « un modèle = un réglage », `../COMPARATIF.md`).

## Commande (historique)

```powershell
.\.venv\Scripts\python.exe traduire_pdf.py "MON_FICHIER.pdf" --model google/gemma-4-12b-qat --consigne modeles\gemma\consigne.md
```

(La température 0.6 et le thinking OFF par défaut conviennent à Gemma — d'où une
commande plus courte que pour Qwen.)

## Consigne

Voir [`consigne.md`](consigne.md) : seul modèle qui **reproduit le gras/italique**
(clés `bold`/`italic`), avec un glossaire musical complet.

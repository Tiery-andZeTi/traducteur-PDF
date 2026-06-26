# Qwen 3.5 9B vision — fiche modèle

**Statut : modèle principal de fait (juin 2026).** En cours de validation sur
plusieurs traductions avant de figer quoi que ce soit.

## Réglages validés

| Réglage | Valeur | Pourquoi |
|---|---|---|
| Quantification | Q8_0 | Se charge en VRAM, fiable. |
| Contexte | 17k | — |
| **Thinking** | **ON** (obligatoire) | OFF testé le 24/06/2026 = inutilisable (bavures). On ne coupe pas le raisonnement. |
| **Température départ** | **0** | Mesuré meilleur que 0.2 / 0.6 — **à l'inverse de Gemma**. Le « jamais temp 0 » du script est une cicatrice Gemma. |
| Reprise sur boucle | auto → 0.2 | Si une page épuise son budget (boucle), le script relance à `--retry-temperature` (défaut 0.2). Rien à ajouter. |

⚠️ Tendance à **boucler** le raisonnement sur les pages denses (label de portée +
symboles musicaux + bémols inline) → peut épuiser le budget de tokens. Le filet
auto à 0.2 récupère ces pages.

## Commande (à copier-coller)

LM Studio démarré (Local Server, port 1234), **Qwen seul chargé** ou alors le
`--model` est obligatoire. Depuis `D:\Dev\traducteur PDF`, venv activé :

```powershell
.\.venv\Scripts\python.exe traduire_pdf.py "MON_FICHIER.pdf" --model qwen/qwen3.5-9b --temperature 0 --consigne modeles\qwen3.5\consigne.md
```

- `--model qwen/qwen3.5-9b` : requis (plusieurs modèles chargés).
- `--temperature 0` : requis (le défaut du script est resté 0.6).
- thinking ON : ne PAS toucher à `--reasoning-effort`.

Au lancement, vérifier le bandeau : `modèle : qwen/qwen3.5-9b   temperature : 0.0`.

## Consigne

Voir [`consigne.md`](consigne.md) dans ce dossier (prompt autonome, format
2-blocs SYSTEM + RAPPEL lu par `traduire_pdf.py`). Glossaire = solfège pur ;
les techniques de basse (slap, hammer-on, walking bass) restent en anglais et
ne sont PAS dans le prompt (Qwen les rend bien seul). Le comparatif global des
modèles est dans [`../COMPARATIF.md`](../COMPARATIF.md).

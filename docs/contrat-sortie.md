# Contrat de sortie JSON — LA référence

Ce document décrit **exactement** ce que `validateur.py` accepte. C'est le
**contrat figé** que toute consigne modèle doit faire produire.

> ⚠️ **Source de vérité unique.** Quand le schéma change, on édite :
> 1. `validateur.py` (le code qui fait respecter),
> 2. ce fichier,
> 3. **puis on reporte** dans chaque `modeles/<llm>/consigne.md` (qui sont
>    autonomes — voir la décision « une consigne par modèle » dans le CHANGELOG).
> Si les trois divergent, c'est le validateur qui fait foi.

---

## Structure

```
racine        objet { "pages": [ … ] }   — SEULE clé autorisée : "pages"
└─ page       objet
   ├─ page_number  entier ≥ 1   (séquence croissante de 1 en 1, sans trou ni doublon)
   ├─ status       "translated" | "no_translation"
   ├─ reason       chaîne non vide — UNIQUEMENT si status = "no_translation"
   └─ blocks       liste de blocs
      └─ bloc   { "type": …, … }
```

### Clés autorisées (toute autre clé = rejet)

| Niveau | Clés permises |
|---|---|
| racine | `pages` |
| page | `page_number`, `status`, `blocks`, `reason` |
| bloc `heading` / `paragraph` | `type`, `content` |
| bloc `list` | `type`, `items` |
| fragment | `text` (obligatoire), `bold`, `italic` |

### Types de bloc (et eux seuls)
- `heading` → clé `content` (liste de fragments, non vide)
- `paragraph` → clé `content` (liste de fragments, non vide)
- `list` → clé `items` (liste non vide ; **chaque item est lui-même une liste de
  fragments** non vide)

### Fragment
- `text` : chaîne **non vide**, obligatoire.
- `bold`, `italic` : booléens `true`/`false` (jamais des chaînes), facultatifs.
  *Si un modèle ignore l'emphase (cas Qwen), il n'émet jamais ces clés et chaque
  `content` n'a qu'un seul fragment.*

### Règles de cohérence du statut
- `status: "translated"` → `blocks` **non vide**.
- `status: "no_translation"` → `blocks` **vide** (`[]`), `reason` courte
  (ex. `"couverture"`, `"partition"`).

---

## Forme exacte

```json
{
  "pages": [
    {
      "page_number": 1,
      "status": "translated",
      "blocks": [
        { "type": "heading",   "content": [ { "text": "Titre" } ] },
        { "type": "paragraph", "content": [ { "text": "Un paragraphe traduit." } ] },
        { "type": "list", "items": [
            [ { "text": "Premier point." } ],
            [ { "text": "Deuxième point." } ]
        ] }
      ]
    }
  ]
}
```

Page sans rien à traduire :
```json
{ "pages": [ { "page_number": 1, "status": "no_translation", "reason": "partition", "blocks": [] } ] }
```

---

## Vérifier un JSON

```powershell
.\.venv\Scripts\python.exe validateur.py "chemin\vers\fichier.json"
```
Code de sortie `0` = valide, `1` = invalide (il liste TOUTES les erreurs avec
leur emplacement : « page 4, bloc 3, fragment 2 »).

# Traducteur PDF — cours de basse (anglais → français), 100 % local

Transforme un PDF de cours en anglais en **PDF bilingue** (page originale + page
traduite en français, en alternance), en **une seule commande**, via un modèle
vision local (LM Studio). Le projet sert aussi de **banc d'essai de LLM** : chaque
modèle a sa propre consigne et ses propres réglages.

> 📓 Historique des évolutions : [`CHANGELOG.md`](CHANGELOG.md).

---

## Démarrage rapide

1. **LM Studio** → onglet *Developer / Local Server* → charger un **modèle vision**
   → *Start Server* (port **1234**).
2. PowerShell depuis ce dossier, **venv activé**. Lancer (exemple Qwen, le modèle
   actuel) :

```powershell
.\.venv\Scripts\python.exe traduire_pdf.py "MON_FICHIER.pdf" --model qwen/qwen3.5-9b --temperature 0 --consigne modeles\qwen3.5\consigne.md
```

À la fin : `MON_FICHIER_FINAL.pdf` (le bilingue), `MON_FICHIER_workbook.json` (tout),
et un `MON_FICHIER_page_NN.json` par page (récupérable).

> ⚠️ Lancer avec le **Python du venv** (`.\.venv\Scripts\python.exe`), jamais le
> Python global (sinon `No module named 'fitz'`).
>
> 👉 La commande **exacte par modèle** (id, température, thinking) est dans la fiche
> du modèle : [`modeles/qwen3.5/README.md`](modeles/qwen3.5/README.md),
> [`modeles/gemma/README.md`](modeles/gemma/README.md).

---

## Organisation du dossier

```
traducteur-PDF/
├─ README.md            ← ce fichier (point d'entrée)
├─ CHANGELOG.md         ← journal des évolutions
│
├─ traduire_pdf.py      ← orchestrateur (PDF → JSON par page → PDF bilingue)
├─ validateur.py        ← fait respecter le contrat JSON
├─ assembler.py · build_pdf.py · json_to_html.py · pdf_engine.py · style.css
├─ lancer_traductions.ps1
│
├─ modeles/            ← UNE consigne autonome par modèle (version dans le nom)
│   ├─ qwen3.5/   consigne.md + README.md (réglages + commande)
│   ├─ gemma/     consigne.md + README.md  (abandonné de fait)
│   ├─ _gabarit/  consigne.md + README.md  (pour calibrer un nouveau LLM)
│   └─ COMPARATIF.md   ← tableau des modèles testés + verdicts
│
├─ docs/
│   ├─ contrat-sortie.md     ← LE schéma JSON de référence (= validateur.py)
│   ├─ cahier-des-charges.md · besoins.md · reglage-llm-local.md
│   ├─ demarrage-rapide.md   ← ancien guide détaillé (options DPI, dépannage…)
│   └─ backlog.md            ← idées / fonctionnalités à venir
│
└─ _archive/          ← fichiers de test conservés (JSON/PNG d'essai, traces thinking)
```

> Les **sorties de traduction** (PDF + JSON par cours) ne vivent pas dans le repo :
> elles sont rangées hors-projet (dossier Musique).

---

## Principes (à ne pas réapprendre)

- **Un modèle = ses propres réglages.** Les enseignements de Gemma (jamais temp 0,
  thinking off) **ne se transfèrent pas** aux autres modèles. Qwen, lui : thinking
  **ON** + température **0**. Détails dans [`modeles/COMPARATIF.md`](modeles/COMPARATIF.md).
- **Une consigne autonome par modèle.** On assume la duplication du contrat car le
  projet sert à *tester* des LLM : réécrire le prompt d'un modèle ne doit pas
  toucher les autres. Le contrat commun est documenté une fois dans
  [`docs/contrat-sortie.md`](docs/contrat-sortie.md), à reporter dans les consignes
  quand le schéma change.
- **La VO reste la référence.** La traduction est une aide lue en face-à-face ;
  priorité au sens, puis aux paragraphes. Voir [`docs/besoins.md`](docs/besoins.md).

---

## Options utiles

| Option | Défaut | Rôle |
|---|---|---|
| `--model` | (auto) | **Obligatoire si plusieurs modèles chargés.** |
| `--temperature` | `0.6` | Réglage Gemma ; **Qwen = 0**. |
| `--retry-temperature` | `0.2` | Température du 2ᵉ essai si une page **boucle** (auto). |
| `--reasoning-effort` | `""` (thinking ON) | `none` = thinking coupé (rapide, bavures). |
| `--consigne` | `modeles/gemma/consigne.md` | Prompt système du modèle. |
| `--dpi` | `150` | Résolution des images envoyées. |
| `--base-url` | `http://localhost:1234/v1` | Serveur LM Studio. |

Dépannage détaillé, tests DPI, assemblage manuel : [`docs/demarrage-rapide.md`](docs/demarrage-rapide.md).

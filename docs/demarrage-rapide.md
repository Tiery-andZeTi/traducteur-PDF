# Démarrage rapide — `traduire_pdf.py`

Transforme un PDF de cours en anglais en **PDF bilingue** (page originale +
page traduite en français, en alternance), en **une seule commande**, 100 % en
local.

> 📌 Ce guide est **générique** (valable pour tout modèle). La commande **exacte
> du modèle** (id, température, thinking) est dans sa fiche :
> [`modeles/qwen3.5/README.md`](../modeles/qwen3.5/README.md) (modèle actuel),
> [`modeles/gemma/README.md`](../modeles/gemma/README.md).

---

## 1. Avant de lancer (à faire une fois)

1. **Démarrer le serveur dans LM Studio**
   - Onglet **Developer / Local Server**
   - Charger un **modèle VISION** (qui sait lire des images).
     Actuel : `qwen/qwen3.5-9b`. Historique : `google/gemma-4-12b-qat`.
   - **Start Server** (port **1234** par défaut).

2. **Empêcher la mise en veille de Windows** si le PDF est long (un run de
   60–70 pages dure ~2 h). Paramètres → Système → Alimentation → veille sur « Jamais ».

> ⚠️ Lancer le script avec le **Python du venv** (il contient PyMuPDF +
> WeasyPrint), jamais le Python global.

---

## 2. La commande

Dans PowerShell, depuis le dossier du projet (`D:\Dev\traducteur PDF`), venv activé.
**Exemple avec le modèle actuel (Qwen 3.5)** :

```powershell
.\.venv\Scripts\python.exe traduire_pdf.py "mon_workbook.pdf" --model qwen/qwen3.5-9b --temperature 0 --consigne modeles\qwen3.5\consigne.md
```

> Pourquoi ces options ici : Qwen veut **température 0** et sa **propre consigne**.
> Chaque modèle a ses réglages — voir sa fiche. Avec Gemma, la commande est plus
> courte (ses défauts conviennent) : voir `modeles/gemma/README.md`.

À la fin tu obtiens :

| Fichier | Contenu |
|---|---|
| `mon_workbook_FINAL.pdf` | **le PDF bilingue final** (VO1, VF1, VO2, VF2…) |
| `mon_workbook_workbook.json` | le JSON complet de toutes les pages |
| `mon_workbook_page_NN.json` | une sauvegarde par page (récupérable) |

Pour choisir le nom de sortie, ajoute-le après le PDF source :
```powershell
.\.venv\Scripts\python.exe traduire_pdf.py "mon_workbook.pdf" "resultat.pdf" --model qwen/qwen3.5-9b --temperature 0 --consigne modeles\qwen3.5\consigne.md
```

---

## 3. Les options

| Option | Défaut | À quoi ça sert |
|---|---|---|
| `--model` | (auto) | **Obligatoire si plusieurs modèles sont chargés.** Sinon le script refuse de deviner et liste les modèles. |
| `--temperature` | `0.6` | **Dépend du modèle** : 0.6 pour Gemma, **0 pour Qwen**. La valeur passée prime sur LM Studio. Voir la fiche du modèle. |
| `--retry-temperature` | `0.2` | Température du **2ᵉ essai** si une page épuise son budget (= boucle de raisonnement). Automatique : un peu de hasard casse la boucle. Remplace l'ancien « doublement de max-tokens ». |
| `--reasoning-effort` | `""` (thinking actif) | Qualité par défaut. `none` = thinking coupé → plus rapide mais bavures. ⚠️ Pour Qwen, OFF est **inutilisable** : ne pas y toucher. |
| `--max-tokens` | `16384` | Budget réflexion+réponse par page. |
| `--dpi` | `150` | Résolution des images envoyées au modèle. |
| `--base-url` | `http://localhost:1234/v1` | Adresse du serveur LM Studio. |
| `--consigne` | `modeles\gemma\consigne.md` | Prompt système du modèle. **À préciser** pour tout modèle non-Gemma. |

---

## 4. Rythme et qualité

- **Thinking activé (défaut)** = ~1 à 1,5 min/page, sortie **propre**. Le modèle
  relit et applique les règles avant de livrer. C'est l'étape qualité. **Qwen
  l'exige** (thinking ON).
- **`--reasoning-effort none`** = ~10 s/page mais **premier jet non relu** → bon
  pour un brouillon de mise en page, à repasser à la main. *Ne marche bien que sur
  les modèles solides sans thinking (ex. Gemma Q8) — pas Qwen.*
- Si une page **boucle** (fréquent avec Qwen à temp 0 sur les pages denses), le
  script la **relance tout seul** à `--retry-temperature` (0.2). Rien à faire.

Le `page_number` est **imposé par le script** : le modèle n'a pas à le deviner.

---

## 5. En cas de souci

| Symptôme | Cause / solution |
|---|---|
| `Serveur LM Studio injoignable` | Le serveur n'est pas démarré, ou pas sur le port 1234. |
| `plusieurs modèles sont chargés` | Ajoute `--model <id>` (l'id exact est listé par le message). |
| `modèle « … » absent du serveur` | Le modèle n'est pas chargé dans LM Studio, ou id mal orthographié. |
| `Consignes introuvables : …` | Le chemin `--consigne` est faux. Vérifie : `modeles\<modèle>\consigne.md`. |
| Une page en **ÉCHEC** | Sa réponse brute est gardée en `*.raw.txt`. Les autres pages sont sauvées. Corrige cette page (ou relance) puis assemble à la main : `.\.venv\Scripts\python.exe assembler.py mon_workbook_workbook.json "mon_workbook.pdf" "FINAL.pdf"` |
| `No module named 'fitz'` | Tu utilises le Python global. Relance avec `.\.venv\Scripts\python.exe`. |

---

## 6. Si tu modifies les règles de traduction

Tout se passe dans le fichier **`modeles\<modèle>\consigne.md`** (le prompt système,
**autonome par modèle**). Le script le relit à chaque run — pas besoin de toucher
au code.

⚠️ Le prompt système sauvegardé dans l'interface Chat de LM Studio **n'est PAS
utilisé par le script** : seul le fichier `consigne.md` fait foi.

> Le **contrat JSON** que toute consigne doit faire produire est décrit une fois
> dans [`contrat-sortie.md`](contrat-sortie.md) (la référence à recopier quand le
> schéma change). Le comparatif des modèles testés est dans
> [`../modeles/COMPARATIF.md`](../modeles/COMPARATIF.md).

---

## 7. Commandes pour tester

Toutes les options se passent en ligne de commande : **inutile de modifier le
fichier** pour faire un essai. La valeur passée prime sur le défaut.

### Tester l'effet du DPI sur la vitesse (au chrono)

Baisser le DPI = images plus petites à encoder = run plus rapide. Le point à
surveiller n'est pas la vitesse (elle baisse forcément) mais la **lisibilité du
texte par le modèle** : trop bas, il lit mal les petits caractères → erreurs de
transcription. Le bon réglage est le DPI le plus bas où la traduction reste
identique.

```powershell
# référence actuelle (150)
.\.venv\Scripts\python.exe traduire_pdf.py "mon.pdf" --model qwen/qwen3.5-9b --temperature 0 --consigne modeles\qwen3.5\consigne.md --dpi 150

# test plus rapide
.\.venv\Scripts\python.exe traduire_pdf.py "mon.pdf" --model qwen/qwen3.5-9b --temperature 0 --consigne modeles\qwen3.5\consigne.md --dpi 120
```

> Pour comparer honnêtement : utilise **le même PDF** d'un essai à l'autre (le
> nombre et la densité des pages faussent la mesure).

### Tester un nouveau modèle (gabarit neutre)

Pour découvrir un modèle non encore calibré, lance-le avec la consigne neutre du
gabarit, observe ce qu'il produit seul, puis dérive-lui sa consigne dédiée :

```powershell
.\.venv\Scripts\python.exe traduire_pdf.py "court.pdf" --model <id-du-modele> --consigne modeles\_gabarit\consigne.md
```

Méthode complète : [`../modeles/_gabarit/README.md`](../modeles/_gabarit/README.md).

### Note sur `--temperature`

La température n'est **pas** un levier de vitesse (même coût de calcul par token).
La bonne valeur **dépend du modèle** et se mesure : 0.6 pour Gemma, 0 pour Qwen.
**Principe : un modèle = ses propres réglages** — ne transpose pas un réglage d'un
modèle à un autre par réflexe.

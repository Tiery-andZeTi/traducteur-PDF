# Démarrage rapide — `traduire_pdf.py`

Transforme un PDF de cours en anglais en **PDF bilingue** (page originale +
page traduite en français, en alternance), en **une seule commande**, 100 % en
local.

---

## 1. Avant de lancer (à faire une fois)

1. **Démarrer le serveur dans LM Studio**
   - Onglet **Developer / Local Server**
   - Charger un **modèle VISION** (qui sait lire des images). Validé : `google/gemma-4-12b-qat`.
   - **Start Server** (port **1234** par défaut).

2. **Empêcher la mise en veille de Windows** si le PDF est long (un run de
   60–70 pages dure ~2 h). Paramètres → Système → Alimentation → veille sur « Jamais ».

> ⚠️ Il faut lancer le script avec le **Python du venv** (il contient PyMuPDF +
> WeasyPrint). Pas le Python global.

---

## 2. La commande

Dans PowerShell, depuis le dossier du projet :

```powershell
.\.venv\Scripts\python.exe traduire_pdf.py "mon_workbook.pdf" --model google/gemma-4-12b-qat
```

C'est tout. À la fin tu obtiens :

| Fichier | Contenu |
|---|---|
| `mon_workbook_FINAL.pdf` | **le PDF bilingue final** (VO1, VF1, VO2, VF2…) |
| `mon_workbook_workbook.json` | le JSON complet de toutes les pages |
| `mon_workbook_page_NN.json` | une sauvegarde par page (récupérable) |

Pour choisir le nom de sortie, ajoute-le après le PDF source :
```powershell
.\.venv\Scripts\python.exe traduire_pdf.py "mon_workbook.pdf" "resultat.pdf" --model google/gemma-4-12b-qat
```

---

## 3. Les options (toutes facultatives)

| Option | Défaut | À quoi ça sert |
|---|---|---|
| `--model` | (auto) | **Obligatoire si plusieurs modèles sont chargés.** Sinon le script refuse de deviner et liste les modèles. |
| `--temperature` | `0.6` | **Ne jamais mettre 0** : le modèle part en boucle et n'écrit rien. 0.6 est sûr. |
| `--reasoning-effort` | `""` (thinking actif) | Qualité par défaut. `none` = thinking coupé → ~8× plus rapide mais bavures (LaTeX, erreurs de glossaire) à recorriger. |
| `--max-tokens` | `16384` | Budget par page. Doublé tout seul si une page très dense déborde. |
| `--dpi` | `150` | Résolution des images envoyées au modèle. |
| `--base-url` | `http://localhost:1234/v1` | Adresse du serveur LM Studio. |
| `--consigne` | `CONSIGNE_TRADUCTEUR.md` | Le prompt système (source unique des règles de traduction). |

---

## 4. Rythme et qualité

- **Thinking activé (défaut)** = ~1 à 1,5 min/page, sortie **propre**. Le modèle
  relit et applique les règles avant de livrer. C'est l'étape qualité.
- **`--reasoning-effort none`** = ~10 s/page mais te donne son **premier jet**
  (non relu) → bon pour un brouillon, à repasser à la main.

Le `page_number` est **imposé par le script** : le modèle n'a pas à le deviner.

---

## 5. En cas de souci

| Symptôme | Cause / solution |
|---|---|
| `Serveur LM Studio injoignable` | Le serveur n'est pas démarré, ou pas sur le port 1234. |
| `plusieurs modèles sont chargés` | Ajoute `--model <id>` (l'id exact est listé par le message). |
| `modèle « … » absent du serveur` | Le modèle n'est pas chargé dans LM Studio, ou id mal orthographié. |
| Une page en **ÉCHEC** | Sa réponse brute est gardée en `*.raw.txt`. Les autres pages sont sauvées. Corrige cette page (ou relance) puis assemble à la main : `.\.venv\Scripts\python.exe assembler.py mon_workbook_workbook.json "mon_workbook.pdf" "FINAL.pdf"` |
| `No module named 'fitz'` | Tu utilises le Python global. Relance avec `.\.venv\Scripts\python.exe`. |

---

## 6. Si tu modifies les règles de traduction

Tout se passe dans **`CONSIGNE_TRADUCTEUR.md`** (le prompt système). Le script le
relit à chaque run — pas besoin de toucher au code. ⚠️ Le prompt système
sauvegardé dans l'interface Chat de LM Studio (« traducteur ») **n'est PAS utilisé
par le script** : seul ce fichier fait foi.

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
.\.venv\Scripts\python.exe traduire_pdf.py "a_traduire\mon.pdf" --model google/gemma-4-12b-qat --dpi 150

# test plus rapide
.\.venv\Scripts\python.exe traduire_pdf.py "a_traduire\mon.pdf" --model google/gemma-4-12b-qat --dpi 120

# encore plus bas si 120 reste lisible
.\.venv\Scripts\python.exe traduire_pdf.py "a_traduire\mon.pdf" --model google/gemma-4-12b-qat --dpi 100
```

> Pour comparer honnêtement : utilise **le même PDF** d'un essai à l'autre (le
> nombre et la densité des pages faussent la mesure).

### Tester un brouillon ultra-rapide (thinking coupé)

```powershell
.\.venv\Scripts\python.exe traduire_pdf.py "a_traduire\mon.pdf" --model google/gemma-4-12b-qat --reasoning-effort none
```

~10 s/page au lieu de ~1–1,5 min, mais c'est le **premier jet non relu** : bon
pour vérifier la mise en page, à repasser pour la qualité.

### Note sur `--temperature`

La température n'est **pas** un levier de vitesse (même coût de calcul par token).
Si une valeur plus haute semble plus rapide, c'est que le modèle « réfléchit »
moins longtemps, pas qu'il infère plus vite. Pour la fidélité de traduction, reste
bas (**0.6**, 0.7 max). Ne jamais mettre 0 (boucle de raisonnement).

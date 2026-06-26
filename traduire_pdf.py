#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
traduire_pdf.py — orchestrateur tout-en-un (brique d'automatisation).

Remplace le travail manuel de copiste : au lieu de glisser chaque image dans
LM Studio et de coller la réponse dans un fichier à la main, ce script fait la
boucle complète, en UNE commande :

    PDF source
      → rasterise chaque page en image (PyMuPDF)
      → envoie l'image au modèle via le SERVEUR LM Studio (API compatible OpenAI)
      → récupère le texte JSON renvoyé par le modèle
      → ÉCRIT le fichier (c'est le script qui écrit, pas le modèle)
      → fusionne toutes les pages, VALIDE, puis ASSEMBLE le PDF bilingue.

Le modèle reste passif : il ne fait que répondre du texte. Tout ce qui « agit »
(ouvrir, écrire, enchaîner) est fait ici.

Prérequis : dans LM Studio, onglet « Developer / Local Server », démarrer le
serveur avec un modèle VISION chargé (port 1234 par défaut).

Usage :
    python traduire_pdf.py <source.pdf> [sortie.pdf]

À lancer avec le Python du venv (qui contient PyMuPDF + WeasyPrint) :
    ./.venv/Scripts/python.exe traduire_pdf.py mon_workbook.pdf

Options :
    --base-url   défaut http://localhost:1234/v1
    --model      identifiant du modèle (défaut : auto-détecté via /v1/models)
    --dpi        résolution d'envoi des images au modèle (défaut 150)
    --consigne   fichier de consignes (défaut modeles/gemma/consigne.md)
"""

import argparse
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.request

import fitz  # PyMuPDF

import assembler
from validateur import valider

TIMEOUT_PAGE = 600  # s — une inférence vision locale peut être lente


class BudgetEpuise(RuntimeError):
    """Le modèle a épuisé max_tokens (souvent en 'réfléchissant') sans écrire
    le JSON. Récupérable en redonnant un budget plus grand."""


# --------------------------------------------------------------------------- #
#  Consignes : on lit le fichier de consignes du modèle comme SEULE source de
#  vérité (un fichier autonome par modèle dans modeles/<llm>/consigne.md).
#  Les deux blocs sont dans des clôtures ``` ; on repère les lignes qui ne
#  contiennent QUE ``` (les ``` cités en pleine phrase dans le prompt ne
#  comptent donc pas). 1er bloc = system prompt, 2e bloc = rappel par tour.
# --------------------------------------------------------------------------- #
def charger_consignes(chemin):
    with open(chemin, encoding="utf-8") as f:
        lignes = f.read().splitlines()

    blocs, courant, dedans = [], [], False
    for ligne in lignes:
        if ligne.strip() == "```":
            if dedans:
                blocs.append("\n".join(courant))
                courant, dedans = [], False
            else:
                dedans = True
            continue
        if dedans:
            courant.append(ligne)

    if len(blocs) < 2:
        raise ValueError(
            f"{chemin} : impossible d'y trouver les 2 blocs (system prompt + "
            f"rappel). {len(blocs)} bloc(s) ``` détecté(s).")
    return blocs[0].strip(), blocs[1].strip()


def rappel_pour_page(modele_rappel, n):
    """Réinjecte le bon numéro de page dans le rappel (le script DICTE le n°)."""
    return re.sub(r"page_number\s*=\s*\d+", f"page_number = {n}", modele_rappel)


# --------------------------------------------------------------------------- #
#  Dialogue avec le serveur LM Studio (API compatible OpenAI).
# --------------------------------------------------------------------------- #
def _post_json(url, charge):
    data = json.dumps(charge).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT_PAGE) as rep:
        return json.loads(rep.read().decode("utf-8"))


def lister_modeles(base_url):
    """Renvoie la liste des identifiants de modèles exposés par /v1/models."""
    with urllib.request.urlopen(base_url + "/models", timeout=30) as rep:
        data = json.loads(rep.read().decode("utf-8"))
    return [m.get("id") for m in data.get("data", []) if m.get("id")]


def choisir_modele(base_url, demande):
    """Choisit le modèle : celui demandé s'il existe ; sinon auto SEULEMENT s'il
    n'y en a qu'un. Avec plusieurs modèles chargés, on REFUSE de deviner."""
    dispo = lister_modeles(base_url)
    if not dispo:
        raise RuntimeError("Le serveur ne déclare aucun modèle chargé.")
    if demande:
        if demande not in dispo:
            raise RuntimeError(
                f"modèle « {demande} » absent du serveur.\n   Chargés : "
                + ", ".join(dispo))
        return demande
    if len(dispo) == 1:
        return dispo[0]
    raise RuntimeError(
        "plusieurs modèles sont chargés — précise lequel avec --model :\n   "
        + "\n   ".join(dispo))


def demander_traduction(base_url, modele, system_prompt, rappel, image_png,
                        temperature=0, max_tokens=8192, reasoning_effort="none"):
    """Envoie une image + les consignes, renvoie le texte brut du modèle.

    reasoning_effort="none" coupe le « thinking » des modèles qui réfléchissent
    (LM Studio l'honore) : réponse directe, plus rapide, et plus de risque de
    boucle. Mettre "" pour ne pas envoyer le paramètre du tout.

    max_tokens couvre réflexion + réponse : si la réflexion est ACTIVE, elle
    consomme ce budget AVANT d'écrire le JSON ; trop bas → content vide
    (finish_reason=length)."""
    b64 = base64.b64encode(image_png).decode("ascii")
    charge = {
        "model": modele,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": [
                {"type": "text", "text": rappel},
                {"type": "image_url",
                 "image_url": {"url": f"data:image/png;base64,{b64}"}},
            ]},
        ],
    }
    if reasoning_effort:
        charge["reasoning_effort"] = reasoning_effort
    rep = _post_json(base_url + "/chat/completions", charge)
    choix = rep["choices"][0]
    contenu = (choix.get("message", {}).get("content") or "")
    if not contenu.strip():
        fr = choix.get("finish_reason")
        if fr == "length":
            raise BudgetEpuise(
                "budget de tokens épuisé par le raisonnement avant le JSON "
                "(finish_reason=length).")
        raise RuntimeError(f"réponse vide (finish_reason={fr}).")
    return contenu


# --------------------------------------------------------------------------- #
#  Nettoyage de la réponse : on extrait l'objet JSON même si le modèle a
#  ajouté des ``` ou du bavardage autour (filet, malgré la consigne).
# --------------------------------------------------------------------------- #
def extraire_page(brut, n):
    texte = brut.strip()
    # retire d'éventuelles clôtures ```json … ```
    texte = re.sub(r"^```[a-zA-Z]*\s*", "", texte)
    texte = re.sub(r"\s*```$", "", texte).strip()
    # garde du 1er { au dernier } (au cas où il reste du texte autour)
    debut, fin = texte.find("{"), texte.rfind("}")
    if debut == -1 or fin == -1 or fin < debut:
        raise ValueError("aucun objet JSON trouvé dans la réponse.")
    data = json.loads(texte[debut:fin + 1])

    # le modèle renvoie {"pages":[page]} ; on tolère aussi la page seule.
    if isinstance(data, dict) and "pages" in data:
        pages = data["pages"]
        if not isinstance(pages, list) or len(pages) != 1:
            raise ValueError("attendu exactement 1 page dans la réponse.")
        page = pages[0]
    elif isinstance(data, dict) and ("status" in data or "page_number" in data):
        page = data
    else:
        raise ValueError("structure de réponse inattendue.")

    if not isinstance(page, dict):
        raise ValueError("la page n'est pas un objet JSON.")
    page["page_number"] = n  # le script fait FOI sur le numéro de page
    return page


# --------------------------------------------------------------------------- #
def main(argv):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    ap = argparse.ArgumentParser(description="PDF anglais → PDF bilingue, en une commande.")
    ap.add_argument("source_pdf")
    ap.add_argument("sortie", nargs="?")
    ap.add_argument("--base-url", default="http://localhost:1234/v1")
    ap.add_argument("--model", default=None)
    ap.add_argument("--dpi", type=int, default=150)
    ap.add_argument("--temperature", type=float, default=0.6,
                    help="Défaut 0.6. NE PAS mettre 0 avec un modèle 'thinking' : "
                         "le raisonnement part en boucle (greedy) et n'écrit "
                         "jamais le JSON. Cette valeur PRIME sur LM Studio.")
    ap.add_argument("--max-tokens", type=int, default=16384, dest="max_tokens",
                    help="Budget réflexion+réponse par page (défaut 16384).")
    ap.add_argument("--retry-temperature", type=float, default=0.2,
                    dest="retry_temperature",
                    help="Température du 2e essai quand une page épuise son budget "
                         "(BudgetEpuise). À temp 0, le raisonnement greedy peut "
                         "BOUCLER (déterministe → inéchappable) et remplir le budget "
                         "sans jamais écrire le JSON ; un cheveu de hasard (défaut "
                         "0.2) casse la boucle. Remplace l'ancien doublement de "
                         "max_tokens, inutile quand c'est une boucle et non un "
                         "manque de budget. Si la valeur n'est pas > --temperature, "
                         "on ajoute +0.2 pour garantir une vraie hausse.")
    ap.add_argument("--reasoning-effort", default="", dest="reasoning_effort",
                    help="'' (défaut) = thinking laissé actif → MEILLEURE qualité "
                         "(le modèle applique les règles dans son brouillon). "
                         "'none' = coupe le thinking → plus rapide mais bavures "
                         "possibles (charabia LaTeX, erreurs de glossaire).")
    ap.add_argument("--consigne", default=os.path.join("modeles", "gemma", "consigne.md"))
    args = ap.parse_args(argv[1:])

    base_url = args.base_url.rstrip("/")
    if not os.path.isfile(args.source_pdf):
        print(f"PDF source introuvable : {args.source_pdf}")
        return 2
    if not os.path.isfile(args.consigne):
        print(f"Consignes introuvables : {args.consigne}")
        return 2

    sortie = args.sortie or (
        os.path.splitext(args.source_pdf)[0] + "_FINAL.pdf")
    base_nom = os.path.splitext(os.path.basename(args.source_pdf))[0]

    # 1) consignes
    try:
        system_prompt, modele_rappel = charger_consignes(args.consigne)
    except (OSError, ValueError) as e:
        print(f"Lecture des consignes : {e}")
        return 2

    # 2) serveur + modèle
    try:
        modele = choisir_modele(base_url, args.model)
    except urllib.error.URLError as e:
        print(f"❌ Serveur LM Studio injoignable sur {base_url} : {e.reason}")
        print("   → Démarre le serveur dans LM Studio (onglet Developer / "
              "Local Server) avec un modèle vision chargé.")
        return 2
    except Exception as e:
        print(f"❌ Choix du modèle impossible : {e}")
        return 2
    print(f"• Serveur : {base_url}   modèle : {modele}   "
          f"temperature : {args.temperature}   "
          f"reasoning : {args.reasoning_effort or 'défaut modèle'}")

    # 3) boucle page par page
    doc = fitz.open(args.source_pdf)
    print(f"• {doc.page_count} page(s) à traiter (DPI envoi = {args.dpi})")
    pages, echecs = [], []
    for i in range(doc.page_count):
        n = i + 1
        png = doc[i].get_pixmap(dpi=args.dpi).tobytes("png")
        rappel = rappel_pour_page(modele_rappel, n)
        print(f"  - page {n} : envoi…", end=" ", flush=True)
        brut = None
        try:
            try:
                brut = demander_traduction(base_url, modele, system_prompt,
                                           rappel, png,
                                           temperature=args.temperature,
                                           max_tokens=args.max_tokens,
                                           reasoning_effort=args.reasoning_effort)
            except BudgetEpuise:
                # Cause la plus fréquente à temp 0 : le raisonnement greedy BOUCLE
                # (déterministe → inéchappable) et remplit le budget sans écrire le
                # JSON. Doubler max_tokens ne sert à rien (on reboucle pareil). On
                # relance plutôt avec un peu de température : le hasard casse la
                # boucle. (Vérifié : page 5 du Level-5 récupérée en passant à 0.2.)
                t_retry = args.retry_temperature
                if t_retry <= args.temperature:
                    t_retry = args.temperature + 0.2  # garantit une vraie hausse
                print(f"budget épuisé (boucle probable) → 2e essai à temp "
                      f"{t_retry}…", end=" ", flush=True)
                brut = demander_traduction(base_url, modele, system_prompt,
                                           rappel, png,
                                           temperature=t_retry,
                                           max_tokens=args.max_tokens,
                                           reasoning_effort=args.reasoning_effort)
            page = extraire_page(brut, n)
        except Exception as e:
            print(f"ÉCHEC ({e})")
            # on garde la réponse brute (si on l'a reçue) pour correction manuelle
            if brut is not None:
                try:
                    with open(f"{base_nom}_page_{n:02d}.raw.txt", "w",
                              encoding="utf-8") as f:
                        f.write(brut)
                except Exception:
                    pass
            echecs.append(n)
            continue

        # on écrit aussi la page seule (comme le flux manuel : récupérable)
        with open(f"{base_nom}_page_{n:02d}.json", "w", encoding="utf-8") as f:
            json.dump({"pages": [page]}, f, ensure_ascii=False, indent=2)
        statut = page.get("status", "?")
        print(f"ok ({statut})")
        pages.append(page)
    doc.close()

    if echecs:
        print(f"\n❌ {len(echecs)} page(s) en échec : {echecs}")
        print("   Réponses brutes enregistrées en *.raw.txt. Corrige ces pages "
              "(ou relance), puis assemble manuellement avec assembler.py.")
        return 1

    # 4) workbook complet
    data = {"pages": pages}
    chemin_json = f"{base_nom}_workbook.json"
    with open(chemin_json, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"• JSON complet écrit : {chemin_json}")

    # 5) validation
    erreurs = []
    valider(data, erreurs)
    if erreurs:
        print(f"❌ JSON invalide — {len(erreurs)} erreur(s), pas d'assemblage :")
        for msg in erreurs:
            print(f"  - {msg}")
        return 1
    print("• JSON valide ✅")

    # 6) assemblage du PDF bilingue
    avertissements, manquantes = assembler.assembler(data, args.source_pdf, sortie)
    print(f"✅ PDF bilingue : {sortie} "
          f"({len(pages)} page(s) VO+VF = {2 * len(pages)} pages).")
    for a in avertissements:
        print(f"  · {a}")
    if manquantes:
        print(f"  ⚠ pages VO absentes du source : {manquantes}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

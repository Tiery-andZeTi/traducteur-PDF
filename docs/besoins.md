# Définition des besoins — projet traducteur PDF (le marbre)

> Couche STABLE, indépendante du modèle. Elle encode ce dont J'AI besoin, pas la
> manière de parler à tel ou tel LLM. On n'y touche qu'en cas de vrai changement
> d'usage. Le prompt système et les réglages, eux, se refont par modèle.

## Double objectif du projet
1. **Me former à l'IA locale** sur un terrain concret (quantification, contexte,
   thinking, température, prompt par modèle…).
2. **Aboutir à un livrable utile** : un pipeline qui traduit mes cours de basse
   la nuit, en local, sans frais d'API.
Les deux se nourrissent : le livrable sert de boussole, la formation sert le livrable.

## Principe directeur (la clé de tout)
- **La VO (le PDF d'origine) est la SOURCE DE VÉRITÉ.** Elle a les tablatures, les
  diagrammes, les photos, la notation, la mise en forme. Elle est lue EN PREMIER.
- **La traduction est une AIDE**, lue en second, en face-à-face avec la VO, quand
  je ne comprends pas l'anglais. Elle ne remplace jamais l'original.

## Ce qui en découle (priorités, dans l'ordre)
1. **Fidélité du SENS = priorité absolue.** Surtout le vocabulaire de solfège
   (double croche, anacrouse, hammer-on…) → c'est le rôle du GLOSSAIRE, le vrai
   levier de qualité (pas les réglages du modèle).
2. **Structure en paragraphes = importante.** Elle me permet de naviguer et de
   retrouver une info visuellement. À préserver (un paragraphe source = un bloc).
3. **Mise en forme fine (gras / italique) = NON requise.** Le signal « nouvelle
   notion » (terme en italique) reste visible dans la VO, que je lis d'abord.
   On NE fait PAS patiner le modèle là-dessus (c'est son point faible : il lit
   bien le sens, devine mal la typo).
4. **Tout ce qui est purement visuel et non traduisible** (tablature, portée,
   schéma, en-tête/pied de page, nom d'auteur) = **ignoré**.

## Périmètre assumé
- Optimisé pour une **lecture FACE-À-FACE** (la VO est toujours sous les yeux).
- Si un jour je voulais lire la traduction SEULE (l'imprimer, la partager sans la
  VO), la structure et l'emphase reprendraient de l'importance → il faudrait
  réviser ce document. Ce n'est pas le cas aujourd'hui.

## Conséquence sur les prompts
- **Contrat** (ce fichier + schéma JSON + glossaire) = stable, réutilisable d'un
  modèle à l'autre.
- **Réglage** (ton du prompt, thinking on/off, gestion typo, verbosité) = refait
  pour CHAQUE modèle, selon ses qualités et défauts. Un modèle = un réglage.

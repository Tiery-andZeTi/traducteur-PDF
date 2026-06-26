# Réglages de base d'un LLM local + outils de diagnostic

Mémo perso — LM Studio / llama.cpp. Carte de référence : NVIDIA 5060 Ti, 16 Go VRAM, 32 Go RAM.

---

## 1. La quantification du MODÈLE (les poids)

> ⚠️ Piège n°1 : **le chiffre plus GRAND = MOINS dégradé** (plus de bits conservés).
> Q4 est PLUS compressé (plus dégradé) que Q8. F16 = pas compressé du tout.

| Format | Bits/poids | Qualité | Taille | Usage |
|---|---|---|---|---|
| Q2 / Q3 | ~2–3 | médiocre | minuscule | à éviter sauf manque de VRAM |
| **Q4_K_M** | ~4,5 | bonne | petit | **le compromis le plus populaire** |
| Q5_K_M | ~5,5 | très bonne | moyen | si la VRAM le permet |
| Q6_K | ~6,5 | excellente | moyen+ | qualité quasi maximale |
| **Q8_0** | ~8,5 | quasi parfaite | gros | référence « sans perte audible » |
| **F16** | 16 | **la meilleure** | énorme | rarement utile vs Q8 (gaspillage VRAM) |

**À retenir :** F16 n'est PAS médiocre, c'est l'inverse — la qualité maximale. Mais entre Q8 et F16, le gain de qualité est négligeable pour le double de mémoire. Pour les poids, **Q6/Q8 est le vrai point d'équilibre**.

---

## 2. La quantification du KV CACHE (mémoire de travail)

C'est un réglage **séparé** des poids. Le KV cache retient le contexte traité.

| Format KV | Qualité | Taille | Quand |
|---|---|---|---|
| **F16** | meilleure | la plus grosse | si on a la VRAM (recommandé pour juger la qualité) |
| **Q8_0** | très bonne | moitié de F16 | **le meilleur compromis** à long contexte |
| Q4_0 / Q4_1 | correcte mais peut dégrader | la plus petite | seulement si on manque de VRAM |

> ⚠️ Le KV cache **grossit proportionnellement au contexte** (voir §3). À grand contexte, il devient le plus gros consommateur de VRAM, devant les poids.
> ⚠️ Quantifier le KV exige généralement la **Flash Attention activée** (§6).

---

## 3. La longueur de CONTEXTE (n_ctx)

- Nombre de jetons que le modèle peut « voir » d'un coup.
- **llama.cpp réserve TOUT le KV cache au chargement** pour la taille demandée → régler 70k mange la VRAM immédiatement, même avant de traiter quoi que ce soit.
- Règle : **mettre juste ce qu'il faut**. Une page courte ne justifie pas 32k de contexte.
- Ordre de grandeur (modèle ~14B, attention complète) : KV à 70k ≈ 11 Go en F16, ~5,5 Go en Q8, ~2,8 Go en Q4.

---

## 4. GPU Offload (n_gpu_layers)

- Combien de couches du modèle tournent sur le GPU.
- **Maximum = toutes les couches sur le GPU** = vitesse pleine.
- Si réglé trop bas → une partie calcule sur le **CPU** (lent, ça chauffe le proc, soufflerie).
- Premier réflexe quand le CPU force pendant l'inférence : vérifier ce réglage.

---

## 5. Flash Attention

- Optimisation du calcul de l'attention : plus rapide, moins de VRAM.
- **Obligatoire (en pratique) pour quantifier le KV cache.**
- À activer presque tout le temps sur GPU NVIDIA.

---

## 6. Température et échantillonnage

> Piège n°2 (que j'avais en fait bon) : **temp 0 = déterministe** (choisit toujours le jeton le plus probable), **temp haute = créatif/aléatoire**.

| Réglage | Effet | Pour la TRADUCTION |
|---|---|---|
| **Température** | 0 = figé/fidèle, 1+ = créatif/imprévisible | **0,1 – 0,3** (fidélité) |
| top_p | garde les jetons cumulant X% de probabilité | ~0,9, peu critique |
| top_k | ne garde que les K jetons les plus probables | 40 par défaut, peu critique |
| repeat_penalty | pénalise les répétitions | ~1,1 ; monter si le modèle radote |

Pour traduire : **température basse**. Pour brainstormer/écrire de la fiction : température haute.

---

## 7. OUTILS DE DIAGNOSTIC (Gestionnaire des tâches Windows)

### Les deux mémoires du GPU
- **VRAM dédiée** (16 Go) : mémoire propre de la carte, ultra-rapide. ✅ tout doit tenir ici.
- **Mémoire GPU partagée** : de la RAM système empruntée, reliée par le **bus PCIe = dizaines de fois plus lent**. ❌ si elle grimpe, c'est un **débordement**.

### Le bon moteur à observer
- Le graphe **« 3D »** mélange parfois tout selon le pilote.
- Les calculs d'IA sont sur le moteur **« Cuda »** ou **« Compute »** (menu déroulant au-dessus du mini-graphe). Toujours vérifier celui-là.

### 🌡️ La TEMPÉRATURE GPU = le détecteur de vérité
- **GPU chaud (60°C+) à fond** = il calcule **vraiment**. ✅ vraie performance.
- **GPU « 100% » mais FROID (~40°C) + lent** = il **poireaute** sur des transferts mémoire, il ne calcule presque pas. ❌

### Tableau des signatures à reconnaître

| Symptôme | Diagnostic |
|---|---|
| GPU chaud + rapide + CPU calme | ✅ tout va bien, vraie perf |
| GPU faible % + **CPU qui chauffe**, soufflerie | calcul sur CPU → GPU Offload trop bas, ou modèle/KV qui déborde |
| GPU « 100% » mais **froid + lent** + mémoire partagée qui monte | **débordement VRAM** dans la RAM via PCIe → réduire contexte ou quantifier le KV |

### Réglage anti-piège (pilote NVIDIA)
Panneau NVIDIA → Gérer les paramètres 3D → **CUDA - Sysmem Fallback Policy → « Prefer No Sysmem Fallback »**.
→ Le modèle **refuse net de se charger** s'il ne tient pas, au lieu de ralentir en silence. Échec franc = diagnostic immédiat.

---

## 8. RAM SYSTÈME : pourquoi elle monte pendant l'inférence  *(à approfondir plus tard)*

> Constat (24/06/2026) : pendant les runs, la RAM système grimpait page après page
> (jusqu'à 28/32 Go). Ce n'est **PAS** de la mémoire de calcul, c'est surtout du **CACHE**.
> Le calcul, lui, vit en **VRAM** (poids + KV cache) — voir §3-4.

Deux causes se cumulent :

| Cause | Détail | Récupérable ? |
|---|---|---|
| **a) Fichiers modèles mappés (mmap)** | LM Studio/llama.cpp projettent le `.gguf` en RAM. Même TOUT offloadé sur le GPU, le fichier reste **caché en RAM** ; la conso monte vers ~la taille du fichier puis **plafonne**. **Plusieurs modèles chargés = ça s'empile** (4 modèles → facile d'atteindre 25 Go). | oui (éjecter les modèles inutiles) |
| **b) Cache fichier Windows (standby)** | Lectures du PDF + écritures des JSON/PDF gardées en RAM. | oui (libéré dès qu'une appli en a besoin) |

**À retenir :**
- RAM « utilisée » élevée ≠ problème. *« La RAM libre est de la RAM gaspillée »* — Windows la remplit exprès.
- Diagnostic : Gestionnaire des tâches → Mémoire → comparer **« En cours d'utilisation »** vs **« En cache »**. Beaucoup « en cache » = sain.
- Vrai signal d'alerte = la mémoire **« Validée / Committed »** proche de la limite **+ du swap/ralentissements**. (Pas le cas à 28/32.)
- Pour faire baisser tout de suite : **éjecter dans LM Studio les modèles non utilisés**.

> ⚠️ **À creuser** : comportement exact de mmap avec full GPU offload, option « keep model in
> RAM » / mmap de LM Studio, et part réellement « résidente » vs « cache » selon le pilote.

---

## En une phrase

Juger un modèle **uniquement** quand il tient **entièrement en VRAM dédiée**, GPU **chaud**. Sinon on mesure le débordement, pas le modèle.

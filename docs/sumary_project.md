**Spécifications Techniques — Projet RPC-1**

# **Résumé**
- **Objectif** : résoudre le problème de chargement de véhicules avec contraintes géométriques et contraintes d'ordre de livraison (LIFO/accessibilité). Le format d'entrée et de sortie est strict pour une validation automatique.


# **Format du problème**

**Entrées**
- **Dimensions du camion** : `L W H` (cm) -> camion identique
- **Nombre d'articles** : `M` (1 ≤ M ≤ 1000).
- **Liste des objects** : `M` lignes, format `L2 W2 H2 D2` avec :
	- `L2, W2, H2` : dimensions de l'objet (cm).
	- `D2` : ordre. Plus `D2` est petit → plus c'est prioritaire. `D2 = -1` pas d'ordre.
  
Ex:
```
40 40 20            # dimension camion
4                   # nombre d'objet
40 20 10 -1         # Object 1
40 20 10 -1         # ...
10 40 10 -1         # ...
30 40 10 -1         # Object 4
```

**Sorties**
- **Statut** : `SAT` si une solution valide est trouvée, sinon `UNSAT`.
- **Plan de chargement** : `M` lignes (dans l'ordre d'entrée des articles) au format :
	- `v x0 y0 z0 x1 y1 z1`
	- `v` : identifiant du véhicule (0..N)
	- `(x0,y0,z0)` : coin le plus proche de (0, 0, 0)
	- `(x1,y1,z1)` : coin le plus loin de (0, 0, 0)

C'est les coordonnées des points les plus éloignés du carton en référence a (0, 0, 0). On s'y retrouve même si ya des rotations comme ca.

Ex: 

```
SAT
0 0 0 0 40 20 10
0 0 30 0 40 40 20
0 0 20 0 40 30 10
0 0 0 10 40 30 20
```

# **Contraintes (Règles Métiers)**

**Contraintes géométriques (Hard constraints)**
- **Intégrité physique** : aucun article ne dépasse les dimensions du véhicule `(L,W,H)`.
- **Non-chevauchement** : dans un même véhicule, volumes disjoints.
- **Intégrité de livraison** : pas de découpe d'article.
- **Rotations** : autorisées

**Contrainte d'ordre / Accessibilité (LIFO-like)**
- Si `A` doit être livré avant `B` (D_A < D_B), alors `B` **ne doit pas** bloquer la sortie de `A` :
	- `B` ne peut pas être posé sur `A`.
	- `B` ne peut pas être placé devant `A` (entre `A` et la porte).
	- les éléments à livrer plus tôt sont plus proches de la sortie ou au-dessus (`z` plus grand) pour faciliter l'accès.

# **Stratégies de résolution**

**A. Approche exacte (petites instances, M ≤ 100)**
- **Cible** : League Bronze & Argent.
- **Techniques** :
	- *Programmation par contraintes (CP)* — recommandée : gère `NoOverlap3D`, `DiffN`, et contraintes logiques sans linéarisation coûteuse.
	- *SAT* — possible via discrétisation spatiale mais combinatoire (coordonnées jusqu'à 400 → explosion des variables).
	- *MILP* — robustesse, mais nombreuses variables binaires pour garantir non-chevauchement.

**B. Approche heuristique (grandes instances, M ≤ 1000)**
- **Cible** : League Or.
- **Techniques** :
	- *Algorithme glouton initial* (p.ex. First-Fit Decreasing adapté pour LIFO/accessibilité).
	- *Amélioration locale* : swaps entre camions, rotations d'objets, réagencement pour respecter LIFO.
	- *Méta-heuristiques* : Recuit simulé, Recherche tabou, ou Algorithmes évolutionnaires pour diversifier la recherche.
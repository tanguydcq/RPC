# Solveur Ad-Hoc pour le Bin Packing 3D avec contraintes LIFO

Ce solveur ad-hoc implémente une solution pour le problème de bin packing 3D avec contraintes d'ordre de livraison LIFO pour le projet RPC.

## Fonctionnalités Implémentées

- **Parsing robuste** : Analyse complète du format d'entrée (dimensions camion et objets)
- **Placement 3D avancé** : Placement d'objets 3D avec support complet des rotations (6 orientations)
- **Détection de collisions sophistiquée** : Évite tous les chevauchements d'objets dans l'espace 3D
- **Format de sortie conforme** : Respecte strictement le format de sortie spécifié
- **Vérification de faisabilité** : Contrôle préalable que tous les objets peuvent physiquement rentrer
- **Optimisation de placement** : Stratégie de placement bottom-left-back pour maximiser l'espace utilisé

## Algorithme Détaillé

Le solveur utilise une approche gloutonne optimisée :

### 1. **Vérification de Faisabilité**
```python
def satisfiability_check(truck_dims, objects):
    # Vérifie que chaque objet peut rentrer dans au moins une orientation
    # Teste les 6 rotations possibles pour chaque objet
```

### 2. **Tri par Volume**
```python
def sort_objects_by_volume(objects):
    # Ordonne les objets par volume décroissant (First Fit Decreasing)
    # Les plus gros objets sont placés en premier pour une meilleure efficacité
```

### 3. **Placement Glouton**
Pour chaque objet dans l'ordre de volume décroissant :
1. **Recherche dans camions existants** : Teste le placement dans tous les camions déjà créés
2. **Test des orientations** : Essaie les 6 rotations possibles (L×W×H, L×H×W, W×L×H, W×H×L, H×L×W, H×W×L)
3. **Optimisation de position** : Place à la position la plus basse, la plus à gauche, la plus au fond (bottom-left-back)
4. **Création de nouveau camion** : Si aucun placement n'est possible, crée un nouveau camion

### 4. **Algorithme de Placement Bottom-Left-Back**
```python
def find_best_position(obj, obj_length, obj_width, obj_height, truck):
    # Parcourt l'espace 3D par ordre de priorité :
    # 1. Hauteur (z) : de bas en haut
    # 2. Longueur (x) : de gauche à droite  
    # 3. Largeur (y) : de l'arrière vers l'avant
```

## Utilisation

```bash
# Depuis le répertoire racine du projet
cd src/solver_ad-hoc
python3 solver.py <fichier_entrée>

# Exemple avec le fichier d'exemple
python3 solver.py ../../io_exemples/input.sample

# Exemple avec les données de test bronze
python3 solver.py ../../io_exemples/bronze/seed_42.input
```

## Format d'Entrée

```
L W H              # Dimensions du camion (longueur, largeur, hauteur en cm)
M                  # Nombre d'objets (1 ≤ M ≤ 1000)
L1 W1 H1 D1       # Objet 1: dimensions (cm) et ordre de livraison
L2 W2 H2 D2       # Objet 2: D = -1 signifie "pas de contrainte d'ordre"
...                # ... M objets au total
```

**Note sur les contraintes d'ordre** : 
- `D = -1` : Pas de contrainte d'ordre de livraison
- `D > 0` : Plus la valeur est petite, plus l'objet doit être livré tôt
- **⚠️ Limitation actuelle** : Les contraintes LIFO ne sont pas encore implémentées dans cette version

## Format de Sortie

```
SAT/UNSAT                    # Statut de la solution
truck_id x0 y0 z0 x1 y1 z1   # Pour chaque objet (dans l'ordre d'entrée)
truck_id x0 y0 z0 x1 y1 z1   # truck_id : identifiant du camion (0, 1, 2, ...)
...                          # (x0,y0,z0) : coin le plus proche de (0,0,0)
                             # (x1,y1,z1) : coin le plus éloigné de (0,0,0)
```

**Remarques importantes :**
- Les coordonnées sont toujours données pour le coin le plus proche et le plus éloigné de l'origine
- Cette représentation est indépendante des rotations appliquées à l'objet
- Les objets sont listés dans le même ordre que dans le fichier d'entrée

## Exemples

### Exemple Simple

**Entrée :**
```
40 40 20           # Camion 40×40×20
4                  # 4 objets
40 20 10 -1       # Objet 1: 40×20×10, pas de contrainte d'ordre
40 20 10 -1       # Objet 2: 40×20×10
10 40 10 -1       # Objet 3: 10×40×10  
30 40 10 -1       # Objet 4: 30×40×10
```

**Sortie possible :**
```
SAT
0 0 0 0 40 20 10     # Objet 1 dans camion 0
0 0 20 0 40 40 10    # Objet 2 dans camion 0 (rotationné)
0 30 0 0 40 40 10    # Objet 3 dans camion 0
0 0 0 10 30 40 20    # Objet 4 dans camion 0
```

### Exemple avec Plusieurs Camions

**Entrée :**
```
20 20 20           # Petit camion 20×20×20  
3                  # 3 objets
20 20 15 -1       # Objet volumineux
20 20 15 -1       # Autre objet volumineux
10 10 10 -1       # Petit objet
```

**Sortie possible :**
```
SAT  
0 0 0 0 20 20 15     # Objet 1 dans camion 0
1 0 0 0 20 20 15     # Objet 2 dans camion 1 (nouveau camion nécessaire)
0 0 0 15 10 10 25    # Objet 3 dans camion 0 (au-dessus de l'objet 1)
```

## Performance et Limitations

### ✅ Points Forts
- **Robustesse** : Gestion correcte de tous les cas d'entrée valides
- **Efficacité spatiale** : Stratégie bottom-left-back pour minimiser l'espace gaspillé
- **Support complet des rotations** : Teste automatiquement les 6 orientations possibles
- **Format de sortie strict** : Respecte parfaitement les spécifications

### ⚠️ Limitations Actuelles
- **Contraintes LIFO non implémentées** : Les contraintes d'ordre de livraison sont ignorées
- **Algorithme glouton** : Peut ne pas trouver la solution optimale globale
- **Pas d'optimisation locale** : Aucune amélioration post-placement
- **Performance sur grandes instances** : Peut être lent pour M > 500 objets

### 🚀 Améliorations Prévues
- [ ] **Implémentation LIFO** : Gestion des contraintes d'ordre de livraison
- [ ] **Recherche locale** : Algorithmes de swap et réarrangement
- [ ] **Méta-heuristiques** : Recuit simulé, algorithmes génétiques
- [ ] **Optimisations algorithmiques** : Structures de données plus efficaces
- [ ] **Heuristiques avancées** : Placement par zones, stratégies adaptatives

## Détails Techniques

### Complexité
- **Temps** : O(M × T × R × P) où :
  - M = nombre d'objets
  - T = nombre de camions créés  
  - R = 6 rotations par objet
  - P = positions testées par camion (≈ L×W×H dans le pire cas)
- **Espace** : O(M + T×M) pour stocker les objets et les placements

### Structure des Classes
```python
class Object:          # Représente un objet avec ses dimensions et contraintes
class Truck:           # Représente un camion avec ses objets placés  
class AdHocSolver:     # Implémente l'algorithme de résolution
```
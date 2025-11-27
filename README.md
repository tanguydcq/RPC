# Projet RPC

## Description

Vous êtes responsable de la logistique au Service d′Acheminement National dédié au Trans-
port d′Articles de la Compagnie Logistique Aérienne Ultra Spéciale. Vous disposez de plusieurs
véhicules spécialisés (Technologies de Roulage Avancées, Innovantes et Novatrices pour En-
gins Autonomes Urbains) de capacités différentes et d′une liste d′articles à livrer à différentes
adresses. Votre objectif est d′optimiser la répartition des colis dans les véhicules pour minimiser
le nombre de véhicules utilisés tout en respectant les capacités de charge maximale de chaque
véhicules.

La description complète du projet est disponible dans le dossier `docs/` avec sa modélisation.

## Structure du Projet

Ce répertoire contient :

### Outils de base
- `src/generate.py` : générateur de données d'entrée
- `src/visualize.py` : visualisateur de données de sortie

### Solveurs
- `src/solver_ad-hoc/` : Solveur ad-hoc pour le problème de bin packing 3D avec contraintes LIFO

### Données d'exemple
- `io_exemples/` : Fichiers d'exemple d'entrée et sortie
  - `input.sample` / `output.sample` : Exemple général
  - `bronze/` : Exemples pour la league Bronze
  - `silver/` : Exemples pour la league Silver  
  - `gold/` : Exemples pour la league Gold

### Documentation
- `docs/` : Documentation technique du projet

### `generate.py`

Permet de gérénérer des données d'entrée pour le projet pour les trois leagues (bronze, silver et gold).

Utiliser la commande :

```bash
python3 generate.py --help
```

Pour voir comment l'utiliser.

## Solveur Ad-Hoc

Le projet inclut un solveur ad-hoc implémenté pour résoudre le problème de bin packing 3D avec contraintes d'ordre de livraison (LIFO).

### Utilisation

```bash
cd src/solver_ad-hoc
python3 solver.py <fichier_entrée>
```

### Exemple

```bash
cd src/solver_ad-hoc
python3 solver.py ../../io_exemples/input.sample
```

### Fonctionnalités

- **Parsing robuste** : Analyse du format d'entrée (dimensions camion et objets)
- **Placement 3D** : Placement d'objets 3D avec support des rotations
- **Détection de collisions** : Évite les chevauchements d'objets
- **Format de sortie conforme** : Respect du format de sortie spécifié
- **Algorithme glouton** : Stratégie First Fit Decreasing optimisée par volume

### Algorithme

1. **Vérification de faisabilité** : Vérifie que tous les objets peuvent individuellement rentrer dans un camion
2. **Tri des objets** : Ordonne les objets par volume décroissant (plus grands en premier)
3. **Placement glouton** : Pour chaque objet :
   - Essaie de placer dans les camions existants
   - Teste toutes les rotations possibles (6 orientations)
   - Si impossible, crée un nouveau camion
4. **Optimisation de position** : Place chaque objet à la position la plus basse, la plus à gauche, la plus au fond possible

### `visualize.py`

Permet de visualiser les données de sortie du projet.

Utiliser la commande :

```bash
python3 visualize.py --help
```

Pour voir comment l'utiliser.

## Performances et Limitations

### Performances actuelles
- ✅ **League Bronze** : Gestion efficace des petites instances (M ≤ 100)
- ⚠️ **League Silver** : Performance acceptable pour instances moyennes
- ❌ **League Gold** : Optimisations nécessaires pour grandes instances (M ≤ 1000)

### Limitations connues
- Les contraintes LIFO (ordre de livraison) ne sont pas encore implémentées
- Algorithme glouton simple qui peut ne pas trouver la solution optimale
- Pas d'optimisation locale ou de méta-heuristiques

### Améliorations futures
- [ ] Implémentation des contraintes d'ordre de livraison (LIFO)
- [ ] Algorithmes de recherche locale (swaps, réarrangements)
- [ ] Méta-heuristiques (recuit simulé, algorithmes génétiques)
- [ ] Optimisations pour les grandes instances

## Format des Données

### Entrée
```
L W H              # Dimensions du camion (longueur, largeur, hauteur)
M                  # Nombre d'objets
L1 W1 H1 D1       # Objet 1: dimensions et ordre de livraison (-1 = pas de contrainte)
L2 W2 H2 D2       # Objet 2
...
```

### Sortie
```
SAT/UNSAT
truck_id x0 y0 z0 x1 y1 z1    # Pour chaque objet dans l'ordre d'entrée
...
```

Où (x0,y0,z0) est le coin le plus proche de l'origine et (x1,y1,z1) le coin le plus éloigné.


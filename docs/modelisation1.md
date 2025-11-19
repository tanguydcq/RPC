## 1. Variables de Décision (pour chaque objet $i$)

### Ancrage spatial
- $x_i, y_i, z_i \in \mathbb{N}$
- Domaines :
  - $x_i \in [0, W]$
  - $y_i \in [0, L]$
  - $z_i \in [0, H]$

### Orientation
- $o_i \in \{0, 1, 2, 3, 4, 5\}$
- Correspond aux 6 permutations possibles des dimensions $(L_{ref}, W_{ref}, H_{ref})$

### Dimensions effectives (après rotation) -> ce qu'on va chercher pour chaque object à placer
- $w'_i, l'_i, h'_i \in \mathbb{Z}$

### Affectation véhicule
- $v_i \in \{1, \ldots, V\}$

---

## 2. Contraintes de Rotation

Les dimensions effectives $(l'_i, w'_i, h'_i)$ dépendent de l’orientation $o_i$.

Table des permutations (Element / Table constraint) :

| $o_i$ | $l'_i$      | $w'_i$      | $h'_i$      |
|--------|---------------|---------------|---------------|
| 0      | $L_{ref}$   | $W_{ref}$   | $H_{ref}$   |
| 1      | $L_{ref}$   | $H_{ref}$   | $W_{ref}$   |
| 2      | $W_{ref}$   | $L_{ref}$   | $H_{ref}$   |
| 3      | $W_{ref}$   | $H_{ref}$   | $L_{ref}$   |
| 4      | $H_{ref}$   | $L_{ref}$   | $W_{ref}$   |
| 5      | $H_{ref}$   | $W_{ref}$   | $L_{ref}$   |

---

## 3. Coordonnées dérivées (non-variables)

Pour les deuxièmes coordonnées de sortie, on a juste à faire le calcul:
$$
x_1 = x_i + w'_i,\quad
y_1 = y_i + l'_i,\quad
z_1 = z_i + h'_i
$$

Ces valeurs ne sont **pas** des variables décisionnelles. Elles se retrouvent dirctement grace aux valeurs effectives donc elles ne doivent pas être déclarées dans le solveur -> alourdi le problème pour rien

---

## 4. Contraintes de Non Chevauchement

Pour deux objets $i$ et $j$ dans le même véhicule :
$$
\text{NoOverlap3D}(i,j)
$$

Forme disjonctive :
$$
(x_i + w'_i \le x_j) \,\lor\, (x_j + w'_j \le x_i) \,\lor\,
(y_i + l'_i \le y_j) \,\lor\, (y_j + l'_j \le y_i) \,\lor\,
(z_i + h'_i \le z_j) \,\lor\, (z_j + h'_j \le z_i)
$$

---

## 5. Contraintes de Précédence (ordre de livraison)

Soit $D_i$ la date/ordre de livraison de l’objet $i$.

Si $D_i < D_j$ (i doit être livré avant j) **et** $v_i = v_j$, alors :
$$
(y_i \ge y_j + l'_j) \;\lor\; (z_i \ge z_j + h'_j)
$$

Interprétation :
- L’objet prioritaire doit être plus profond (grand $y$) ou plus haut (grand $z$) pour être extrait après le retrait de l’autre.
Le plus près et haut de la porte, rien doit le gêner devant et haut dessus
---

## 6. Contraintes de Limites du Véhicule

Pour chaque objet $i$, dans son véhicule $v_i$ :

$$
x_i + w'_i \le W_{veh}(v_i)
$$
$$
y_i + l'_i \le L_{veh}(v_i)
$$
$$
z_i + h'_i \le H_{veh}(v_i)
$$

L'objet doit pas être plus grand que le camion

---

## 8. Objectif

- Minimiser le nombre de véhicules utilisés  
- Minimiser le volume perdu total  

Forme générique :
$$
\min f(x_i, y_i, z_i, o_i, v_i)
$$
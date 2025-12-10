#!/usr/bin/env python3
import fileinput
import math
import argparse
import os
import platform
import subprocess
import sys
import tempfile
from functools import cache


class Dimension:
    def __init__(self, xyz):
        (x, y, z) = map(int, xyz.split("x"))
        self.x = x
        self.y = y
        self.z = z

    def __getitem__(self, index):
        if index == 0:
            return self.x
        elif index == 1:
            return self.y
        elif index == 2:
            return self.z
        else:
            raise IndexError("Dimension index out of range")


class Rgb:
    def __init__(self, r, g, b, a=1.0):
        self.r = r
        self.g = g
        self.b = b
        self.a = a

    def lighten(self, factor):
        return Cmyk.from_rgb(self).lighten(factor).to_rgba()

    def darken(self, factor):
        return Cmyk.from_rgb(self).darken(factor).to_rgba()

    def __getitem__(self, item):
        if item == 0:
            return self.r
        elif item == 1:
            return self.g
        elif item == 2:
            return self.b
        elif item == 3:
            return self.a
        else:
            raise IndexError("Rgb index out of range")

    def __str__(self):
        def fmt(channel):
            return int(channel * 255)

        return f"Rgb({fmt(self.r)}, {fmt(self.g)}, {fmt(self.b)}, {fmt(self.a)})"


class Cmyk:
    def __init__(self, c, m, y, k):
        self.c = c
        self.m = m
        self.y = y
        self.k = k

    @staticmethod
    def from_rgb(rgb):
        (r, g, b, _) = rgb

        k = 1.0 - max(r, g, b)
        if k == 1.0:
            return Cmyk(0, 0, 0, 1)

        c = (1.0 - r - k) / (1.0 - k)
        m = (1.0 - g - k) / (1.0 - k)
        y = (1.0 - b - k) / (1.0 - k)

        return Cmyk(c, m, y, k)

    def to_rgba(self):
        r = (1.0 - self.c) * (1.0 - self.k)
        g = (1.0 - self.m) * (1.0 - self.k)
        b = (1.0 - self.y) * (1.0 - self.k)
        return Rgb(r, g, b, 1.0)

    @cache
    def lighten(self, factor):
        def lighten(u):
            return clamp(u - u * factor, 0.0, 1.0)

        return Cmyk(lighten(self.c), lighten(self.m), lighten(self.y), lighten(self.k))

    @cache
    def darken(self, factor):
        def darken(u):
            return clamp(u + (1.0 - u) * factor, 0.0, 1.0)

        return Cmyk(darken(self.c), darken(self.m), darken(self.y), darken(self.k))


def rgb(r, g, b):
    return Rgb(r / 255, g / 255, b / 255)


def clamp(x, minv, maxv):
    return max(minv, min(x, maxv))


def path(points, fill=None, fill_opacity=None, stroke=None, stroke_width=None, stroke_linejoin=None,
         stroke_linecap=None, paint_order=None):
    attrs = {
        "fill": fill,
        "fill-opacity": fill_opacity,
        "stroke": stroke,
        "stroke-width": stroke_width,
        "stroke-linejoin": stroke_linejoin,
        "stroke-linecap": stroke_linecap,
        "paint-order": paint_order,
    }
    return f"""<path d="{' '.join(points)} z" {' '.join(f'{k}="{v}"' for (k, v) in attrs.items() if v is not None)} />"""

def is_on_left(other, item):
    (x0, y0, z0, x1, y1, z1) = range(6)
    return (other[x0], other[y0], other[z0]) == (item[x0], item[y1], item[z0])
def is_in_front_of(other, item):
    (x0, y0, z0, x1, y1, z1) = range(6)
    return (other[x0], other[y0], other[z0]) == (item[x1], item[y0], item[z0])
def is_above(other, item):
    (x0, y0, z0, x1, y1, z1) = range(6)
    return (other[x0], other[y0], other[z0]) == (item[x0], item[y0], item[z1])

def is_hidden(item, others):
    return any([ is_on_left(o[0], item) for o in others ]) and any([ is_in_front_of(o[0], item) for o in others ]) and any([ is_above(o[0], item) for o in others ])

def voxel(x0, y0, z0, x1, y1, z1, color, shape, offset_x=0, offset_y=0, projection_func=None):
    scale = 1
    sin = .5
    cos = math.sqrt(3) / 2

    def default_isometric_projection(x, y, z):
        return f"{200 + offset_x + (x - y) * cos * scale} {240 + offset_y + ((x + y - 2 * z) * sin * scale)}"
    
    isometric_projection = projection_func if projection_func else default_isometric_projection

    def M(point):
        return f"M {point}"

    def L(point):
        return f"L {point}"

    face_a = [
        M(isometric_projection(x0, y0, z1)),
        L(isometric_projection(x1, y0, z1)),
        L(isometric_projection(x1, y1, z1)),
        L(isometric_projection(x0, y1, z1))
    ]

    face_b = [
        M(isometric_projection(x1, y0, z0)),
        L(isometric_projection(x1, y1, z0)),
        L(isometric_projection(x1, y1, z1)),
        L(isometric_projection(x1, y0, z1)),
    ]

    face_c = [
        M(isometric_projection(x0, y1, z0)),
        L(isometric_projection(x1, y1, z0)),
        L(isometric_projection(x1, y1, z1)),
        L(isometric_projection(x0, y1, z1)),
    ]

    xpz = [
        M(isometric_projection(x1, y0, z0)),
        L(isometric_projection(x1, y1, z0)),
    ]

    xpy = [
        M(isometric_projection(x1, y0, z0)),
        L(isometric_projection(x1, y0, z1)),
    ]

    xpzp = [
        M(isometric_projection(x1, y0, z1)),
        L(isometric_projection(x1, y1, z1)),
    ]

    yzp = [
        M(isometric_projection(x0, y0, z1)),
        L(isometric_projection(x1, y0, z1)),
    ]

    xzp = [
        M(isometric_projection(x0, y0, z1)),
        L(isometric_projection(x0, y1, z1)),
    ]

    ypzp = [
        M(isometric_projection(x0, y1, z1)),
        L(isometric_projection(x1, y1, z1)),
    ]

    ypz = [
        M(isometric_projection(x0, y1, z0)),
        L(isometric_projection(x1, y1, z0)),
    ]

    xyp = [
        M(isometric_projection(x0, y1, z0)),
        L(isometric_projection(x0, y1, z1)),
    ]

    xpyp = [
        M(isometric_projection(x1, y1, z0)),
        L(isometric_projection(x1, y1, z1)),
    ]

    front_color = color.darken(20 / 100)
    top_color = color.lighten(50 / 100)
    left_color = color.lighten(10 / 100)
    (X0, Y0, Z0, X1, Y1, Z1) = shape

    args = {
        "fill": "none",
        "stroke_linejoin": "round",
        "paint_order": "stroke",
    }
    color = color.darken(50 / 100)

    return "\n".join([
        path(face_b, fill=front_color),
        path(xpz, stroke=color if (x1 == X1 and z0 == Z0) else front_color, stroke_width=1 if (x1 == X1 and z0 == Z0) else 0, **args),
        path(xpy, stroke=color if (x1 == X1 and y0 == Y0) else front_color, stroke_width=1 if (x1 == X1 and y0 == Y0) else 0, **args),
        path(face_c, fill=left_color),
        path(xyp, stroke=color if (x0 == X0 and y1 == Y1) else left_color, stroke_width=1 if (x0 == X0 and y1 == Y1) else 0, **args),
        path(ypz, stroke=color if (y1 == Y1 and z0 == Z0) else left_color, stroke_width=1 if (y1 == Y1 and z0 == Z0) else 0, **args),
        path(xpyp, stroke=color if (x1 == X1 and y1 == Y1) else left_color, stroke_width=1 if (x1 == X1 and y1 == Y1) else 0, **args),
        path(face_a, fill=top_color),
        path(xpzp, stroke=color if (x1 == X1 and z1 == Z1) else top_color, stroke_width=1 if (x1 == X1 and z1 == Z1) else 0, **args),
        path(xzp, stroke=color if (x0 == X0 and z1 == Z1) else top_color, stroke_width=1 if (x0 == X0 and z1 == Z1) else 0, **args),
        path(yzp, stroke=color if (y0 == Y0 and z1 == Z1) else top_color, stroke_width=1 if (y0 == Y0 and z1 == Z1) else 0, **args),
        path(ypzp, stroke=color if (y1 == Y1 and z1 == Z1) else top_color, stroke_width=1 if (y1 == Y1 and z1 == Z1) else 0, **args),
    ])


def open_file_default(file_path):
    system_platform = platform.system()

    if system_platform == 'Windows':
        os.startfile(file_path)
    elif system_platform == 'Darwin':  # For macOS
        subprocess.Popen(['open', file_path])
    else:  # For Linux or other Unix-based systems
        # Try to open with a browser to avoid ImageMagick issues
        browsers = ['google-chrome', 'xdg-open', 'firefox', 'chromium-browser']
        for browser in browsers:
            try:
                subprocess.Popen([browser, file_path])
                break
            except FileNotFoundError:
                continue


COLORS = [
    rgb(208, 118, 223),
    rgb(83, 187, 82),
    rgb(143, 84, 203),
    rgb(185, 179, 53),
    rgb(83, 106, 215),
    rgb(127, 166, 60),
    rgb(200, 64, 168),
    rgb(102, 185, 131),
    rgb(215, 58, 122),
    rgb(63, 191, 188),
    rgb(206, 59, 70),
    rgb(93, 161, 216),
    rgb(218, 91, 48),
    rgb(140, 140, 225),
    rgb(218, 143, 53),
    rgb(85, 104, 169),
    rgb(206, 168, 105),
    rgb(144, 79, 152),
    rgb(70, 121, 61),
    rgb(227, 118, 170),
    rgb(132, 113, 45),
    rgb(200, 144, 204),
    rgb(166, 87, 52),
    rgb(159, 71, 101),
    rgb(225, 128, 125)
]

def create_projection_functions():
    """Créer différentes fonctions de projection pour la vue multi-angles"""
    scale = 1
    sin = .5
    cos = math.sqrt(3) / 2
    
    def front_view(offset_x, offset_y):
        def projection(x, y, z):
            return f"{offset_x + x * scale} {offset_y + (y/8 - z) * scale}"
        return projection
    
    def top_view(offset_x, offset_y):
        def projection(x, y, z):
            return f"{offset_x + x * (scale + 0.2)} {offset_y/2 + y * (scale + 0.2)}"
        return projection
    
    def side_view(offset_x, offset_y):
        def projection(x, y, z):
            return f"{offset_x + y * scale} {offset_y + (x/8 - z) * scale}"
        return projection
    
    def side_view_opposite(offset_x, offset_y):
        def projection(x, y, z):
            return f"{offset_x *1.05- x * 1.45 * scale} {offset_y + (y/8 - z) * scale}"
        return projection
    
    def isometric_standard(offset_x, offset_y):
        def projection(x, y, z):
            return f"{offset_x + (x - y) * cos * scale} {offset_y + ((x + y - 2 * z) * sin * scale)}"
        return projection
    
    def isometric_rotated(offset_x, offset_y):
        def projection(x, y, z):
            return f"{offset_x + (y - x) * 1.25 * scale} {offset_y + ((x + y - 2 * z) * sin * scale)}"
        return projection
    
    def back_isometric(offset_x, offset_y):
        def projection(x, y, z):
            return f"{offset_x * 1.05 + (x - y) * cos * scale} {offset_y * 1.1 + ((-x - y - 2 * z) * sin * scale)}"
        return projection
    
    return {
        'front': front_view,
        'top': top_view,
        'side': side_view,
        'side_opposite': side_view_opposite,
        'iso_standard': isometric_standard,
        'iso_rotated': isometric_rotated,
        'iso_back': back_isometric
    }


MAX_TRUCK_DIMENSIONS = Dimension("400x210x220")

if __name__ == "__main__":
    parser = argparse.ArgumentParser("visualize.py")
    parser.add_argument("output_file", help="Le fichier de sortie (.output) - le fichier d'entrée correspondant (.input) sera détecté automatiquement")
    parser.add_argument("--truck-no", type=int, default=None, dest="truck_no", help="Le numéro du véhicule à visualiser (si spécifié, affiche ce camion sous plusieurs angles; si non spécifié, visualise tous les camions côte à côte)")
    parser.add_argument("--truck-dimensions", type=Dimension, default=None,
                        dest="truck_dimensions", help="Dimensions du véhicule (si non spécifié, lit depuis le fichier .input correspondant)")

    args = parser.parse_args()
    
    # Détecter automatiquement le fichier d'entrée à partir du fichier de sortie
    if args.output_file.endswith('.output'):
        input_file_path = args.output_file.replace('.output', '.input')
    else:
        # Si le fichier ne se termine pas par .output, on assume qu'on veut quand même trouver le .input correspondant
        input_file_path = args.output_file + '.input' if not args.output_file.endswith('.input') else args.output_file
        if input_file_path.endswith('.input'):
            # Si on a donné un .input, on cherche le .output correspondant
            args.output_file = input_file_path.replace('.input', '.output')
    
    print(f"Fichier de sortie: {args.output_file}")
    print(f"Fichier d'entrée détecté: {input_file_path}")
        
    # Si les dimensions ne sont pas spécifiées, les lire depuis le fichier input détecté
    if args.truck_dimensions is None:
        try:
            with open(input_file_path, 'r') as f:
                first_line = f.readline().strip()
                dimensions = first_line.split()
                if len(dimensions) == 3:
                    args.truck_dimensions = Dimension(f"{dimensions[0]}x{dimensions[1]}x{dimensions[2]}")
                    print(f"Dimensions du camion lues depuis {input_file_path}: {dimensions[0]}x{dimensions[1]}x{dimensions[2]}")
                else:
                    args.truck_dimensions = MAX_TRUCK_DIMENSIONS
                    print(f"Attention: Format des dimensions invalide dans {input_file_path}, utilisation des dimensions par défaut")
        except FileNotFoundError:
            args.truck_dimensions = MAX_TRUCK_DIMENSIONS
            print(f"Attention: Fichier {input_file_path} non trouvé, utilisation des dimensions par défaut")
        except Exception as e:
            args.truck_dimensions = MAX_TRUCK_DIMENSIONS
            print(f"Erreur lors de la lecture de {input_file_path}: {e}, utilisation des dimensions par défaut")


    # Lire toutes les lignes du fichier de sortie
    try:
        with open(args.output_file, 'r') as f:
            all_lines = list(f)
    except FileNotFoundError:
        print(f"Erreur: Fichier de sortie {args.output_file} non trouvé")
        exit(1)
    except Exception as e:
        print(f"Erreur lors de la lecture de {args.output_file}: {e}")
        exit(1)
    
    trucks_data = {}
    first = True
    
    for line_idx, line in enumerate(all_lines):
        if first:
            first = False
            if line == "SAT\n":
                continue
            elif line == "UNSAT\n":
                exit(0)
            else:
                raise ValueError("Invalid input")
        if line == "\n":
            break
        parts = line.split(" ")
        if len(parts) < 7:
            continue
        (truck, x0, y0, z0, x1, y1, z1) = map(int, parts[:7])
        
        if truck not in trucks_data:
            trucks_data[truck] = []
        trucks_data[truck].append((line_idx, (x0, y0, z0, x1, y1, z1)))
    
    # Déterminer quels camions afficher
    if args.truck_no is not None:
        # Mode camion unique
        trucks_to_display = [args.truck_no] if args.truck_no in trucks_data else []
        if not trucks_to_display:
            print(f"Aucun bloc trouvé pour le camion {args.truck_no}")
            exit(1)
    else:
        # Mode tous les camions
        trucks_to_display = sorted(trucks_data.keys())
        if not trucks_to_display:
            print("Aucun camion trouvé dans les données")
            exit(1)
    
    num_trucks = len(trucks_to_display)
    (L, W, H) = args.truck_dimensions
    
    # Vérifier si on doit utiliser la vue multi-angles
    # Vue multi-angles activée automatiquement quand un camion spécifique est sélectionné
    use_multi_view = args.truck_no is not None and num_trucks == 1
    
    if use_multi_view:
        # Vue multi-angles : disposition en grille 2x3 avec marges améliorées
        view_width = 400  # Largeur de chaque vue
        view_height = 350  # Hauteur de chaque vue
        views_per_row = 3
        margin_x = 80  # Marge horizontale entre les vues et du bord
        margin_y = 100  # Marge verticale entre les vues et du bord
        spacing_x = 50  # Espacement horizontal entre les vues
        spacing_y = 50  # Espacement vertical entre les vues
        
        svg_width = 2 * margin_x + views_per_row * view_width + (views_per_row - 1) * spacing_x
        svg_height = 2 * margin_y + 2 * view_height + spacing_y
        
        projection_funcs = create_projection_functions()
        views = [
            ('Vue Isométrique', projection_funcs['iso_standard']),
            ('Vue Avant', projection_funcs['front']),
            ('Vue du Dessus', projection_funcs['top']),
            ('Vue Isométrique Rotée', projection_funcs['iso_rotated']),
            ('Vue de Côté Gauche', projection_funcs['side']),
            ('Vue de Côté Droit', projection_funcs['side_opposite'])
        ]
        
        svg_content = []
        svg_content.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_width}" height="{svg_height}">')
        
        truck_id = trucks_to_display[0]
        blocks = trucks_data[truck_id]
        
        # Ajouter les titres et dessiner chaque vue
        for view_idx, (view_name, proj_func) in enumerate(views):
            row = view_idx // views_per_row
            col = view_idx % views_per_row
            offset_x = margin_x + col * (view_width + spacing_x)
            offset_y = margin_y + row * (view_height + spacing_y)
            
            # Ajouter le titre de la vue en haut
            svg_content.append(f'<text x="{offset_x + view_width//2}" y="{offset_y - 30}" text-anchor="middle" font-family="Arial, sans-serif" font-size="16" font-weight="bold" fill="#333">{view_name}</text>')
            
            # Créer la fonction de projection avec les bons offsets (décaler les images plus bas et à droite)
            projection_with_offset = proj_func(offset_x + 180, offset_y + 180)
            
            # Dessiner un cadre pour délimiter chaque vue
            svg_content.append(f'<rect x="{offset_x - 10}" y="{offset_y - 40}" width="{view_width + 20}" height="{view_height + 20}" fill="none" stroke="#ddd" stroke-width="1" rx="5"/>')
            
            # Dessiner la structure du camion
            svg_content.append(voxel(-2, 0, 0, 0, H + 10, W + 10, rgb(64, 64, 64), (0, 0, 0, L, H, W), 0, 0, projection_with_offset))
            svg_content.append(voxel(0, -2, 0, L + 10, 0, W + 10, rgb(32, 32, 32), (0, 0, 0, L, H, W), 0, 0, projection_with_offset))
            svg_content.append(voxel(0, 0, -2, L + 10, H + 10, 0, rgb(0, 0, 0), (0, 0, 0, L, H, W), 0, 0, projection_with_offset))
            
            # Dessiner les blocs
            voxels = []
            for (i, (x0, y0, z0, x1, y1, z1)) in blocks:
                for x in range(x0, x1, 10):
                    for y in range(y0, y1, 10):
                        for z in range(z0, z1, 10):
                            voxels.append(((x, y, z, x + 10, y + 10, z + 10),
                                           voxel(x, y, z, x + 10, y + 10, z + 10, COLORS[i % len(COLORS)],
                                                 (x0, y0, z0, x1, y1, z1), 0, 0, projection_with_offset)))
            
            voxels.sort(key=lambda it: (it[0][0] + it[0][1], it[0][2]))
            visible_voxels = [v for v in voxels if not is_hidden(v[0], voxels)]
            
            for voxel_item in visible_voxels:
                (coord, shape) = voxel_item
                svg_content.append(shape)
    
    else:
        # Vue normale (camion unique ou multiples camions)
        # Calculer la largeur SVG en fonction du nombre de camions
        truck_width = 400  # largeur approximative d'un camion en pixels
        spacing = 50  # espacement entre camions
        svg_width = max(560, num_trucks * truck_width + (num_trucks - 1) * spacing + 200)
        
        svg_content = []
        svg_content.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_width}" height="560">')
        
        # Dessiner chaque camion
        for truck_idx, truck_id in enumerate(trucks_to_display):
            offset_x = truck_idx * (truck_width + spacing)
            blocks = trucks_data[truck_id]
            
            # Drawing the truck structure
            svg_content.append(voxel(-2, 0, 0, 0, H + 10, W + 10, rgb(64, 64, 64), (0, 0, 0, L, H, W), offset_x))
            svg_content.append(voxel(0, -2, 0, L + 10, 0, W + 10, rgb(32, 32, 32), (0, 0, 0, L, H, W), offset_x))
            svg_content.append(voxel(0, 0, -2, L + 10, H + 10, 0, rgb(0, 0, 0), (0, 0, 0, L, H, W), offset_x))
            
            # Drawing the blocks for this truck
            voxels = []
            for (i, (x0, y0, z0, x1, y1, z1)) in blocks:
                for x in range(x0, x1, 10):
                    for y in range(y0, y1, 10):
                        for z in range(z0, z1, 10):
                            voxels.append(((x, y, z, x + 10, y + 10, z + 10),
                                           voxel(x, y, z, x + 10, y + 10, z + 10, COLORS[i % len(COLORS)],
                                                 (x0, y0, z0, x1, y1, z1), offset_x)))
            
            voxels.sort(key=lambda it: (it[0][0] + it[0][1], it[0][2]))
            visible_voxels = [v for v in voxels if not is_hidden(v[0], voxels)]
            
            for voxel_item in visible_voxels:
                (coord, shape) = voxel_item
                svg_content.append(shape)
    
    svg_content.append("</svg>")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".svg", delete=False) as f:
        f.write("\n".join(svg_content) + "\n")
        output = f.name

    open_file_default(output)

# Ad-hoc Solver for RPC 3D Bin Packing

This is an ad-hoc solver for the 3D bin packing problem with LIFO delivery constraints.

## Features

- **Input Parsing**: Robust parsing of the input format (truck dimensions and objects)
- **3D Placement**: Basic 3D object placement with rotation support
- **Collision Detection**: Prevents object overlapping
- **Output Formatting**: Correct output format as per specifications

## Algorithm

The solver uses a simple greedy approach:

1. **Sort Objects**: Orders objects by delivery priority (if specified) and then by volume (largest first)
2. **Greedy Placement**: For each object:
   - Try to place in existing trucks
   - Try all possible rotations
   - If not possible, create a new truck

## Usage

```bash
python3 solver.py input_file
```

## Input Format

```
L W H              # Truck dimensions (length, width, height)
M                  # Number of objects
L1 W1 H1 D1       # Object 1: dimensions and delivery order (-1 = no constraint)
L2 W2 H2 D2       # Object 2
...
```

## Output Format

```
SAT/UNSAT
truck_id x0 y0 z0 x1 y1 z1    # For each object in input order
...
```

Where (x0,y0,z0) is the corner closest to origin and (x1,y1,z1) is the farthest corner.

## Example

Input:
```
40 40 20
4
40 20 10 -1
40 20 10 -1
40 10 10 -1
30 40 10 -1
```

Output:
```
SAT
0 0 0 10 40 20 20
0 0 20 10 40 40 20
0 30 0 0 40 40 10
0 0 0 0 30 40 10
```

This shows all 4 objects can be placed in truck 0 without overlapping.
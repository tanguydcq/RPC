from ortools.sat.python import cp_model
from typing import List, Tuple, Dict
import sys


"""
======== DATA STRUCTURES ========
"""

class Object:
    """Represents an object to be placed in a truck."""
    length: int
    width: int
    height: int
    delivery_order: int  # -1 means no order constraint
    id: int  # Original position in input
    
    def __init__(self, id: int, length: int, width: int, height: int, delivery_order: int = -1):
        self.id = id
        self.length = length
        self.width = width
        self.height = height
        self.delivery_order = delivery_order

class Truck:
    """Represents a truck with its dimensions and placed objects."""
    length: int
    width: int
    height: int
    placed_objects: List[Tuple[Object, int, int, int]] # List of tuples (Object, x_0, y_0, z_0)

    def __init__(self, length: int, width: int, height: int):
        self.length = length
        self.width = width
        self.height = height
        self.placed_objects = []



def parse_input(input_text: str):
    """Parse input text and return truck dimensions and objects list."""
    lines = input_text.strip().split('\n')
    
    # Parse truck dimensions
    truck_parts = lines[0].split()
    truck_dims = (int(truck_parts[0]), int(truck_parts[1]), int(truck_parts[2]))
    
    # Parse number of objects
    num_objects = int(lines[1])
    
    # Parse objects
    objects = []
    for i in range(num_objects):
        parts = lines[2 + i].split()
        length, width, height, delivery_order = map(int, parts)
        objects.append(Object(i, length, width, height, delivery_order))
    
    return truck_dims, objects

def generate_output(trucks: List[Truck]) -> str:
    """Format the solution as required output format."""
    lines = ["SAT"]
    
    placements = {}
    
    for truck_id, truck in enumerate(trucks):
        for obj, x, y, z in truck.placed_objects:
            # Calculate the farthest corner coordinates
            x1 = x + obj.length
            y1 = y + obj.width
            z1 = z + obj.height
            
            # Store placement: truck_id, closest corner (x,y,z), farthest corner (x1,y1,z1)
            placements[obj.id] = f"{truck_id} {x} {y} {z} {x1} {y1} {z1}"
    
    # Output objects in their original input order (object id)
    for i in range(len(placements)):
        lines.append(placements[i])
    
    return '\n'.join(lines)


"""
======== UTILS FUNCTIONS ========
"""

class GenericORToolsSolver:
    def __init__(self, truck_dims, objects):
        self.L, self.W, self.H = truck_dims
        self.objects = objects
        self.n = len(objects)

    def solve(self, max_trucks=5):
        model = cp_model.CpModel()

        # === Variables ===
        # Truck assignment : truck[k][i] = 1 if object i in truck k
        truck = {}
        for k in range(max_trucks):
            for i in range(self.n):
                truck[k, i] = model.NewBoolVar(f"truck_{k}_obj_{i}")

        # Coordinates (x,y,z)
        x = {i: model.NewIntVar(0, self.L, f"x_{i}") for i in range(self.n)}
        y = {i: model.NewIntVar(0, self.W, f"y_{i}") for i in range(self.n)}
        z = {i: model.NewIntVar(0, self.H, f"z_{i}") for i in range(self.n)}

        # 6 orientations — we encode them explicitly
        # o[i][r] = 1 si l'objet i utilise la rotation r
        R = [
            lambda o: (o.length, o.width, o.height),
            lambda o: (o.length, o.height, o.width),
            lambda o: (o.width, o.length, o.height),
            lambda o: (o.width, o.height, o.length),
            lambda o: (o.height, o.length, o.width),
            lambda o: (o.height, o.width, o.length),
        ]

        orient = {(i, r): model.NewBoolVar(f"orient_{i}_{r}") for i in range(self.n) for r in range(6)}

        # Dimensions effectives selon orientation
        lx, ly, lz = {}, {}, {}
        for i, obj in enumerate(self.objects):
            for r in range(6):
                Lr, Wr, Hr = R[r](obj)
                lx[i, r] = Lr
                ly[i, r] = Wr
                lz[i, r] = Hr

        # === Constraints ===

        # Each object assigned to exactly 1 truck
        for i in range(self.n):
            model.Add(sum(truck[k, i] for k in range(max_trucks)) == 1)

        # Object uses exactly 1 orientation
        for i in range(self.n):
            model.Add(sum(orient[i, r] for r in range(6)) == 1)

        # Boundaries: x+L <= truck.L, same for y, z
        for i in range(self.n):
            model.Add(sum(orient[i, r] * lx[i, r] for r in range(6)) + x[i] <= self.L)
            model.Add(sum(orient[i, r] * ly[i, r] for r in range(6)) + y[i] <= self.W)
            model.Add(sum(orient[i, r] * lz[i, r] for r in range(6)) + z[i] <= self.H)

        # === Non-overlap constraints ===
        for k in range(max_trucks):
            for i in range(self.n):
                for j in range(i + 1, self.n):
                    # Constraint: if both objects are in the same truck, they cannot overlap
                    both_in_truck = model.NewBoolVar(f"both_{i}_{j}_t{k}")
                    model.Add(truck[k, i] + truck[k, j] == 2).OnlyEnforceIf(both_in_truck)
                    model.Add(truck[k, i] + truck[k, j] <= 1).OnlyEnforceIf(both_in_truck.Not())

                    # Get effective dimensions for each object based on orientation
                    Li = sum(orient[i, r] * lx[i, r] for r in range(6))
                    Wi = sum(orient[i, r] * ly[i, r] for r in range(6))
                    Hi = sum(orient[i, r] * lz[i, r] for r in range(6))

                    Lj = sum(orient[j, r] * lx[j, r] for r in range(6))
                    Wj = sum(orient[j, r] * ly[j, r] for r in range(6))
                    Hj = sum(orient[j, r] * lz[j, r] for r in range(6))

                    # No overlap: at least one of these must be true when both in same truck:
                    # 1. i is completely to the left of j: x[i] + Li <= x[j]
                    # 2. j is completely to the left of i: x[j] + Lj <= x[i]
                    # 3. i is completely in front of j: y[i] + Wi <= y[j]
                    # 4. j is completely in front of i: y[j] + Wj <= y[i]
                    # 5. i is completely below j: z[i] + Hi <= z[j]
                    # 6. j is completely below i: z[j] + Hj <= z[i]
                    
                    no_overlap_x1 = model.NewBoolVar(f"no_overlap_x1_{i}_{j}_t{k}")
                    no_overlap_x2 = model.NewBoolVar(f"no_overlap_x2_{i}_{j}_t{k}")
                    no_overlap_y1 = model.NewBoolVar(f"no_overlap_y1_{i}_{j}_t{k}")
                    no_overlap_y2 = model.NewBoolVar(f"no_overlap_y2_{i}_{j}_t{k}")
                    no_overlap_z1 = model.NewBoolVar(f"no_overlap_z1_{i}_{j}_t{k}")
                    no_overlap_z2 = model.NewBoolVar(f"no_overlap_z2_{i}_{j}_t{k}")
                    
                    # At least one no-overlap condition must be true
                    model.Add(no_overlap_x1 + no_overlap_x2 + no_overlap_y1 + no_overlap_y2 + no_overlap_z1 + no_overlap_z2 >= 1).OnlyEnforceIf(both_in_truck)
                    
                    # Enforce the actual no-overlap constraints
                    model.Add(x[i] + Li <= x[j]).OnlyEnforceIf([both_in_truck, no_overlap_x1])
                    model.Add(x[j] + Lj <= x[i]).OnlyEnforceIf([both_in_truck, no_overlap_x2])
                    model.Add(y[i] + Wi <= y[j]).OnlyEnforceIf([both_in_truck, no_overlap_y1])
                    model.Add(y[j] + Wj <= y[i]).OnlyEnforceIf([both_in_truck, no_overlap_y2])
                    model.Add(z[i] + Hi <= z[j]).OnlyEnforceIf([both_in_truck, no_overlap_z1])
                    model.Add(z[j] + Hj <= z[i]).OnlyEnforceIf([both_in_truck, no_overlap_z2])

        # === Optional: delivery order ===
        for i in range(self.n):
            for j in range(self.n):
                if self.objects[i].delivery_order >= 0 and \
                   self.objects[j].delivery_order >= 0 and \
                   self.objects[i].delivery_order < self.objects[j].delivery_order:
                    # impose z_exit_order(i) <= z_exit_order(j)
                    model.Add(z[i] <= z[j])

        # Objective: minimize used trucks
        used = {k: model.NewBoolVar(f"used_{k}") for k in range(max_trucks)}
        for k in range(max_trucks):
            for i in range(self.n):
                model.Add(used[k] >= truck[k, i])
        model.Minimize(sum(used[k] for k in range(max_trucks)))

        # === Solve ===
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 180 # to modify as needed
        solver.parameters.num_search_workers = 8
        solver.parameters.search_branching = cp_model.FIXED_SEARCH
        solver.parameters.cp_model_presolve = True

        status = solver.Solve(model)
        if status not in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            return []

        # === Build result: list of Truck ===
        trucks_out = [Truck(self.L, self.W, self.H) for _ in range(max_trucks)]

        for i, obj in enumerate(self.objects):
            for k in range(max_trucks):
                if solver.Value(truck[k, i]) == 1:
                    xi, yi, zi = solver.Value(x[i]), solver.Value(y[i]), solver.Value(z[i])
                    # Compute orientation
                    for r in range(6):
                        if solver.Value(orient[i, r]):
                            Lr, Wr, Hr = R[r](obj)
                            obj.length, obj.width, obj.height = Lr, Wr, Hr
                    trucks_out[k].placed_objects.append((obj, xi, yi, zi))
                    break

        # Trim empty trucks
        trucks_out = [t for t in trucks_out if len(t.placed_objects) > 0]
        return trucks_out

"""
======== MAIN FUNCTION ========
"""

def main():
    """Main function to run the solver."""
    if len(sys.argv) != 2:
        print("Usage: python solver.py <input_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    try:
        with open(input_file, 'r') as f:
            input_text = f.read()
        
        # Parse input
        truck_dims, objects = parse_input(input_text)
        
        # Solve
        solver = GenericORToolsSolver(truck_dims, objects)
        solution_trucks = solver.solve()
        
        # Format and output result
        if solution_trucks:
            result = generate_output(solution_trucks)
        else:
            result = "UNSAT"
        
        print(result)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
    
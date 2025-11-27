import sys
from typing import List, Tuple, Optional

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


"""
======== UTILS FUNCTIONS ========
"""

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
    
    pass
    
    return '\n'.join(lines)

"""
======== SOLVER ========
"""

class AdHocSolver:
    """
    Ad-hoc solver for the 3D bin packing problem.
    1. Checks if all objects can fit individually in the truck.
    """
    truck_dims = None
    objects = None
    
    def __init__(self, truck_dims: Optional[Tuple[int, int, int]] = None, objects: Optional[List[Object]] = None):
        self.truck_dims = truck_dims
        self.objects = objects        
    
    def satisfiability_check(self, truck_dims: Tuple[int, int, int], objects: List[Object]) -> bool:
        """
        Verify that all objects can individually fit within truck dimensions.
        Returns True if all objects are featible, False otherwise.
        """
        truck_length, truck_width, truck_height = truck_dims
        
        for obj in objects:
            # Check if object can fit in any orientation (all 6 possible rotations)
            orientations = [
                (obj.length, obj.width, obj.height),
                (obj.length, obj.height, obj.width),
                (obj.width, obj.length, obj.height),
                (obj.width, obj.height, obj.length),
                (obj.height, obj.length, obj.width),
                (obj.height, obj.width, obj.length)
            ]
            
            can_fit = False
            for length, width, height in orientations:
                if (length <= truck_length and width <= truck_width and height <= truck_height):
                    can_fit = True
                    break
            
            if not can_fit:
                return False
        
        return True
    
    def solve(self, truck_dims: Tuple[int, int, int], objects: List[Object]) -> List[Truck]:
        """
        Main solving method.
        Returns list of trucks with placed objects or empty list if UNSAT.
        """
        self.truck_dims = truck_dims
        self.objects = objects
        
        # 1. check if all objects can individually fit
        if not self.satisfiability_check(truck_dims, objects):
            return []  # UNSAT - at least one object cannot fit
        
        # TODO: Implement actual placement logic
        print("All objects can fit individually. Proceeding with placement...")
        return []

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
        solver = AdHocSolver()
        solution_trucks = solver.solve(truck_dims, objects)
        
        # Format and output result
        if solution_trucks:
            result = generate_output(solution_trucks)
        else:
            result = "UNSAT"
        
        print(result)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
    
import sys
import time
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
======== SOLVER ========
"""

class AdHocSolver:
    """
    Ad-hoc solver for the 3D bin packing problem.
    Strategy: Place largest objects first at bottom-left-back positions.
    """
    truck_dims = None
    objects = None
    
    def __init__(self, truck_dims: Optional[Tuple[int, int, int]] = None, objects: Optional[List[Object]] = None):
        self.truck_dims = truck_dims
        self.objects = objects
    
    def get_object_volume(self, obj: Object) -> int:
        """Calculate volume of an object."""
        return obj.length * obj.width * obj.height
    
    def sort_objects_by_volume(self, objects: List[Object]) -> List[Object]:
        """Sort objects by volume in descending order (largest first)."""
        return sorted(objects, key=self.get_object_volume, reverse=True)        
    
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
    
    def check_collision(self, obj: Object, x: int, y: int, z: int, obj_length: int, obj_width: int, obj_height: int, truck: Truck) -> bool:
        """Check if placing an object at (x,y,z) with given dimensions would collide with existing objects."""
        for placed_obj, px, py, pz in truck.placed_objects:
            # Get dimensions of placed object at its position
            placed_obj_length, placed_obj_width, placed_obj_height = placed_obj.length, placed_obj.width, placed_obj.height
            
            # Check for overlap in all 3 dimensions
            overlap_x = not (x + obj_length <= px or px + placed_obj_length <= x)
            overlap_y = not (y + obj_width <= py or py + placed_obj_width <= y) 
            overlap_z = not (z + obj_height <= pz or pz + placed_obj_height <= z)
            
            if overlap_x and overlap_y and overlap_z:
                return True  # Collision detected
        
        return False  # No collision
    
    def find_best_position(self, obj: Object, obj_length: int, obj_width: int, obj_height: int, truck: Truck) -> Optional[Tuple[int, int, int]]:
        """Find the lowest, leftmost, deepest position where the object can be placed."""
        truck_length, truck_width, truck_height = truck.length, truck.width, truck.height
        
        # Try positions from bottom-left-back to top-right-front
        for z in range(truck_height - obj_height + 1):  # height (bottom to top)
            for x in range(truck_length - obj_length + 1):  # length (left to right)
                for y in range(truck_width - obj_width + 1):  # width (back to front)
                    if not self.check_collision(obj, x, y, z, obj_length, obj_width, obj_height, truck):
                        if self.check_gravity_support(x, y, z, obj_length, obj_width, truck):
                            return (x, y, z)
        
        return None  # No valid position found
    
    def check_gravity_support(self, x: int, y: int, z: int, obj_length: int, obj_width: int, truck: Truck) -> bool:
        """
        Check if at least 50% of the bottom surface is supported.
        An object is supported if it's on the ground (z=0) or resting on other objects.
        """
        # Calculate the area of the bottom surface
        bottom_area = obj_length * obj_width
        required_support_area = bottom_area * 0.5
        
        # Calculate supported area by checking overlap with ground and objects below
        supported_area = 0.0
        
        # If on the ground (z=0), the entire bottom surface is supported by the ground
        if z == 0:
            supported_area = bottom_area
        else:
            # Check overlap with objects directly below
            for placed_obj, px, py, pz in truck.placed_objects:
                # Check if this object is directly below (top surface touches bottom of new object)
                if pz + placed_obj.height == z:
                    # Calculate overlap area in x-y plane
                    overlap_x_start = max(x, px)
                    overlap_x_end = min(x + obj_length, px + placed_obj.length)
                    overlap_y_start = max(y, py)
                    overlap_y_end = min(y + obj_width, py + placed_obj.width)
                    
                    if overlap_x_end > overlap_x_start and overlap_y_end > overlap_y_start:
                        overlap_area = (overlap_x_end - overlap_x_start) * (overlap_y_end - overlap_y_start)
                        supported_area += overlap_area
        
        return supported_area >= required_support_area
    
    def place_object_in_truck(self, obj: Object, truck: Truck) -> bool:
        """Try to place an object in a truck. Returns True if successful."""
        # Try all 6 orientations
        orientations = [
            (obj.length, obj.width, obj.height),
            (obj.length, obj.height, obj.width),
            (obj.width, obj.length, obj.height),
            (obj.width, obj.height, obj.length),
            (obj.height, obj.length, obj.width),
            (obj.height, obj.width, obj.length)
        ]
        
        truck_length, truck_width, truck_height = truck.length, truck.width, truck.height
        
        for length, width, height in orientations:
            # Check if orientation fits in truck dimensions
            if (length <= truck_length and width <= truck_width and height <= truck_height):
                position = self.find_best_position(obj, length, width, height, truck)
                if position:
                    x, y, z = position
                    # Update object dimensions for this orientation
                    obj.length, obj.width, obj.height = length, width, height
                    truck.placed_objects.append((obj, x, y, z))
                    return True
        
        return False  # Could not place object
    
    def solve(self, truck_dims: Tuple[int, int, int], objects: List[Object]) -> List[Truck]:
        """
        Main solving method.
        Returns list of trucks with placed objects or empty list if UNSAT.
        """
        self.truck_dims = truck_dims
        self.objects = objects
        
        # 1. Check if all objects can individually fit
        if not self.satisfiability_check(truck_dims, objects):
            return []  # UNSAT - at least one object cannot fit
        
        # 2. Sort objects by volume (largest first)
        sorted_objects = self.sort_objects_by_volume(objects)
        
        # 3. Place objects using First Fit Decreasing strategy
        trucks = []
        
        for obj in sorted_objects:
            placed = False
            
            # Try to place in existing trucks
            for truck in trucks:
                if self.place_object_in_truck(obj, truck):
                    placed = True
                    break
            
            # If couldn't place in existing trucks, create a new one
            if not placed:
                new_truck = Truck(truck_dims[0], truck_dims[1], truck_dims[2])
                trucks.append(new_truck)
                if not self.place_object_in_truck(obj, new_truck):
                    return []  # UNSAT - couldn't place object even in a new truck (should not happen due to prior check)
        
        return trucks

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
        start_time = time.time()
        solver = AdHocSolver()
        solution_trucks = solver.solve(truck_dims, objects)
        end_time = time.time()
        
        # Format and output result
        if solution_trucks:
            result = generate_output(solution_trucks)
        else:
            result = "UNSAT"
        
        print(result)
        print(f"Execution time: {end_time - start_time:.3f} seconds", file=sys.stderr)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
    
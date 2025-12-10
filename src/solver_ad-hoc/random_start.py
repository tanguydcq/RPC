import sys
import random
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
        # Store original dimensions for rotation
        self.original_dims = (length, width, height)

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
    
    def get_used_volume(self) -> int:
        """Calculate total volume used in this truck."""
        return sum(obj.length * obj.width * obj.height for obj, _, _, _ in self.placed_objects)
    
    def get_capacity(self) -> int:
        """Get total capacity of the truck."""
        return self.length * self.width * self.height
    
    def get_utilization(self) -> float:
        """Get utilization percentage."""
        return (self.get_used_volume() / self.get_capacity()) * 100 if self.get_capacity() > 0 else 0


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

def copy_objects(objects: List[Object]) -> List[Object]:
    """Create a deep copy of objects list."""
    new_objects = []
    for obj in objects:
        new_obj = Object(obj.id, obj.original_dims[0], obj.original_dims[1], obj.original_dims[2], obj.delivery_order)
        new_obj.original_dims = obj.original_dims
        new_objects.append(new_obj)
    return new_objects

"""
======== SOLVER ========
"""

class RandomStartSolver:
    """
    Random start solver for the 3D bin packing problem.
    Strategy: Try multiple random orderings of objects and keep the best solution.
    """
    truck_dims = None
    objects = None
    
    def __init__(self, truck_dims: Optional[Tuple[int, int, int]] = None, objects: Optional[List[Object]] = None):
        self.truck_dims = truck_dims
        self.objects = objects
    
    def get_object_volume(self, obj: Object) -> int:
        """Calculate volume of an object."""
        return obj.length * obj.width * obj.height
    
    def calculate_min_trucks(self, truck_dims: Tuple[int, int, int], objects: List[Object]) -> int:
        """Calculate the theoretical minimum number of trucks needed based on volume."""
        truck_volume = truck_dims[0] * truck_dims[1] * truck_dims[2]
        total_objects_volume = sum(self.get_object_volume(obj) for obj in objects)
        min_trucks = (total_objects_volume + truck_volume - 1) // truck_volume
        return max(1, min_trucks)
    
    def satisfiability_check(self, truck_dims: Tuple[int, int, int], objects: List[Object]) -> bool:
        """
        Verify that all objects can individually fit within truck dimensions.
        Returns True if all objects are feasible, False otherwise.
        """
        truck_length, truck_width, truck_height = truck_dims
        
        for obj in objects:
            # Check if object can fit in any orientation (all 6 possible rotations)
            orientations = [
                (obj.original_dims[0], obj.original_dims[1], obj.original_dims[2]),
                (obj.original_dims[0], obj.original_dims[2], obj.original_dims[1]),
                (obj.original_dims[1], obj.original_dims[0], obj.original_dims[2]),
                (obj.original_dims[1], obj.original_dims[2], obj.original_dims[0]),
                (obj.original_dims[2], obj.original_dims[0], obj.original_dims[1]),
                (obj.original_dims[2], obj.original_dims[1], obj.original_dims[0])
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
                        return (x, y, z)
        
        return None  # No valid position found
    
    def place_object_in_truck(self, obj: Object, truck: Truck) -> bool:
        """Try to place an object in a truck. Returns True if successful."""
        # Try all 6 orientations
        orientations = [
            (obj.original_dims[0], obj.original_dims[1], obj.original_dims[2]),
            (obj.original_dims[0], obj.original_dims[2], obj.original_dims[1]),
            (obj.original_dims[1], obj.original_dims[0], obj.original_dims[2]),
            (obj.original_dims[1], obj.original_dims[2], obj.original_dims[0]),
            (obj.original_dims[2], obj.original_dims[0], obj.original_dims[1]),
            (obj.original_dims[2], obj.original_dims[1], obj.original_dims[0])
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
    
    def solve_with_ordering(self, truck_dims: Tuple[int, int, int], objects: List[Object], ordering: str = "random", seed: Optional[int] = None) -> List[Truck]:
        """
        Solve with a specific ordering strategy.
        ordering: "random", "volume_desc", "volume_asc", "shuffle"
        """
        # Create a copy of objects to avoid modifying the original
        objects_copy = copy_objects(objects)
        
        # Apply ordering strategy
        if ordering == "volume_desc":
            # Largest first (default greedy approach)
            objects_copy.sort(key=self.get_object_volume, reverse=True)
        elif ordering == "volume_asc":
            # Smallest first
            objects_copy.sort(key=self.get_object_volume)
        elif ordering == "random" or ordering == "shuffle":
            # Random ordering with seed
            if seed is not None:
                random.seed(seed)
            random.shuffle(objects_copy)
        
        # Place objects using First Fit strategy
        trucks = []
        
        for obj in objects_copy:
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
                    return []  # UNSAT - couldn't place object even in a new truck
        
        return trucks
    
    def evaluate_solution(self, trucks: List[Truck]) -> Tuple[int, float]:
        """
        Evaluate a solution quality.
        Returns (number of trucks, average utilization)
        """
        if not trucks:
            return (float('inf'), 0.0)
        
        num_trucks = len(trucks)
        avg_utilization = sum(truck.get_utilization() for truck in trucks) / num_trucks
        
        return (num_trucks, avg_utilization)
    
    def solve(self, truck_dims: Tuple[int, int, int], objects: List[Object], num_runs: int = 10, seed_start: int = 42) -> List[Truck]:
        """
        Main solving method with multiple random starts.
        Returns the best solution found across all runs.
        """
        self.truck_dims = truck_dims
        self.objects = objects
        
        # Check if all objects can individually fit
        if not self.satisfiability_check(truck_dims, objects):
            return []  # UNSAT
        
        # Calculate theoretical minimum
        min_trucks_theoretical = self.calculate_min_trucks(truck_dims, objects)
        truck_volume = truck_dims[0] * truck_dims[1] * truck_dims[2]
        total_objects_volume = sum(self.get_object_volume(obj) for obj in objects)
        
        print("="*60, file=sys.stderr)
        print(f"Random Start Solver", file=sys.stderr)
        print("="*60, file=sys.stderr)
        print(f"Volume Analysis:", file=sys.stderr)
        print(f"  Truck capacity: {truck_volume:,} cubic units", file=sys.stderr)
        print(f"  Total objects volume: {total_objects_volume:,} cubic units", file=sys.stderr)
        print(f"  Theoretical minimum trucks: {min_trucks_theoretical}", file=sys.stderr)
        print(f"  Number of runs: {num_runs}", file=sys.stderr)
        print("="*60, file=sys.stderr)
        
        best_solution = None
        best_num_trucks = float('inf')
        best_utilization = 0.0
        best_run_info = None
        
        # Run 1: Greedy (volume descending)
        print(f"\nRun 1: Greedy (largest first)", file=sys.stderr)
        solution = self.solve_with_ordering(truck_dims, objects, "volume_desc")
        if solution:
            num_trucks, utilization = self.evaluate_solution(solution)
            print(f"  Result: {num_trucks} trucks, {utilization:.2f}% utilization", file=sys.stderr)
            if num_trucks < best_num_trucks or (num_trucks == best_num_trucks and utilization > best_utilization):
                best_solution = solution
                best_num_trucks = num_trucks
                best_utilization = utilization
                best_run_info = ("Greedy", None)
            
            # If already optimal, no need to continue
            if num_trucks <= min_trucks_theoretical:
                print(f"   Optimal solution found!", file=sys.stderr)
                print("="*60, file=sys.stderr)
                return solution
        
        # Run 2: Reverse greedy (volume ascending)
        print(f"\nRun 2: Reverse greedy (smallest first)", file=sys.stderr)
        solution = self.solve_with_ordering(truck_dims, objects, "volume_asc")
        if solution:
            num_trucks, utilization = self.evaluate_solution(solution)
            print(f"  Result: {num_trucks} trucks, {utilization:.2f}% utilization", file=sys.stderr)
            if num_trucks < best_num_trucks or (num_trucks == best_num_trucks and utilization > best_utilization):
                best_solution = solution
                best_num_trucks = num_trucks
                best_utilization = utilization
                best_run_info = ("Reverse greedy", None)
            
            if num_trucks <= min_trucks_theoretical:
                print(f"   Optimal solution found!", file=sys.stderr)
                print("="*60, file=sys.stderr)
                return solution
        
        # Runs 3-N: Random orderings
        for i in range(num_runs - 2):
            run_num = i + 3
            seed = seed_start + i
            print(f"\nRun {run_num}: Random order (seed={seed})", file=sys.stderr)
            
            solution = self.solve_with_ordering(truck_dims, objects, "random", seed=seed)
            if solution:
                num_trucks, utilization = self.evaluate_solution(solution)
                print(f"  Result: {num_trucks} trucks, {utilization:.2f}% utilization", file=sys.stderr)
                
                if num_trucks < best_num_trucks or (num_trucks == best_num_trucks and utilization > best_utilization):
                    best_solution = solution
                    best_num_trucks = num_trucks
                    best_utilization = utilization
                    best_run_info = ("Random", seed)
                    print(f"   New best solution!", file=sys.stderr)
                
                # If already optimal, no need to continue
                if num_trucks <= min_trucks_theoretical:
                    print(f"   Optimal solution found!", file=sys.stderr)
                    break
        
        # Print summary
        print("\n" + "="*60, file=sys.stderr)
        print("Summary:", file=sys.stderr)
        print(f"  Best solution: {best_num_trucks} trucks, {best_utilization:.2f}% utilization", file=sys.stderr)
        if best_run_info:
            strategy, seed = best_run_info
            if seed is not None:
                print(f"  Found by: {strategy} (seed={seed})", file=sys.stderr)
            else:
                print(f"  Found by: {strategy}", file=sys.stderr)
        
        if best_num_trucks == min_trucks_theoretical:
            print(f"   Optimal solution (matches theoretical minimum)!", file=sys.stderr)
        else:
            print(f"  Gap to theoretical minimum: {best_num_trucks - min_trucks_theoretical} trucks", file=sys.stderr)
        print("="*60, file=sys.stderr)
        
        return best_solution if best_solution else []

"""
======== MAIN FUNCTION ========
"""

def main():
    """Main function to run the solver."""
    if len(sys.argv) < 2:
        print("Usage: python random_start.py <input_file> [num_runs] [seed_start]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    num_runs = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    seed_start = int(sys.argv[3]) if len(sys.argv) > 3 else 42
    
    try:
        with open(input_file, 'r') as f:
            input_text = f.read()
        
        # Parse input
        truck_dims, objects = parse_input(input_text)
        
        # Solve with random starts
        solver = RandomStartSolver()
        solution_trucks = solver.solve(truck_dims, objects, num_runs, seed_start)
        
        # Format and output result
        if solution_trucks:
            result = generate_output(solution_trucks)
        else:
            result = "UNSAT"
        
        print(result)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

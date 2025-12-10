import sys
import random
import math
from typing import List, Tuple, Optional
from copy import deepcopy

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
        # Store original dimensions for rotation operations
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

"""
======== BASE SOLVER ========
"""

class BaseSolver:
    """Base solver with common functionality."""
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
    
    def check_collision(self, obj: Object, x: int, y: int, z: int, obj_length: int, obj_width: int, obj_height: int, truck: Truck, exclude_obj: Optional[Object] = None) -> bool:
        """Check if placing an object at (x,y,z) with given dimensions would collide with existing objects."""
        for placed_obj, px, py, pz in truck.placed_objects:
            # Skip the excluded object (for repositioning)
            if exclude_obj and placed_obj.id == exclude_obj.id:
                continue
                
            # Get dimensions of placed object at its position
            placed_obj_length, placed_obj_width, placed_obj_height = placed_obj.length, placed_obj.width, placed_obj.height
            
            # Check for overlap in all 3 dimensions
            overlap_x = not (x + obj_length <= px or px + placed_obj_length <= x)
            overlap_y = not (y + obj_width <= py or py + placed_obj_width <= y) 
            overlap_z = not (z + obj_height <= pz or pz + placed_obj_height <= z)
            
            if overlap_x and overlap_y and overlap_z:
                return True  # Collision detected
        
        return False  # No collision
    
    def find_best_position(self, obj: Object, obj_length: int, obj_width: int, obj_height: int, truck: Truck, exclude_obj: Optional[Object] = None) -> Optional[Tuple[int, int, int]]:
        """Find the lowest, leftmost, deepest position where the object can be placed."""
        truck_length, truck_width, truck_height = truck.length, truck.width, truck.height
        
        # Try positions from bottom-left-back to top-right-front
        for z in range(truck_height - obj_height + 1):  # height (bottom to top)
            for x in range(truck_length - obj_length + 1):  # length (left to right)
                for y in range(truck_width - obj_width + 1):  # width (back to front)
                    if not self.check_collision(obj, x, y, z, obj_length, obj_width, obj_height, truck, exclude_obj):
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
    
    def get_initial_solution(self, truck_dims: Tuple[int, int, int], objects: List[Object]) -> List[Truck]:
        """
        Generate initial solution using First Fit Decreasing strategy.
        Returns list of trucks with placed objects or empty list if UNSAT.
        """
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
                    return []  # UNSAT - couldn't place object even in a new truck
        
        return trucks


"""
======== LOCAL SEARCH SOLVER ========
"""

class LocalSearchSolver(BaseSolver):
    """
    Enhanced solver with local search optimization.
    Implements shift, swap, rotate, and compaction operations with simulated annealing.
    """
    
    def __init__(self, truck_dims: Optional[Tuple[int, int, int]] = None, objects: Optional[List[Object]] = None):
        super().__init__(truck_dims, objects)
        self.best_solution = None
        self.best_score = float('inf')
        self.min_trucks_theoretical = 0
    
    def calculate_min_trucks(self, truck_dims: Tuple[int, int, int], objects: List[Object]) -> int:
        """
        Calculate the theoretical minimum number of trucks needed based on volume.
        This is a lower bound - the actual solution may need more trucks due to geometric constraints.
        """
        truck_volume = truck_dims[0] * truck_dims[1] * truck_dims[2]
        total_objects_volume = sum(self.get_object_volume(obj) for obj in objects)
        
        # Ceiling division: minimum trucks needed to fit all objects by volume
        min_trucks = (total_objects_volume + truck_volume - 1) // truck_volume
        
        return max(1, min_trucks)  # At least 1 truck
    
    def calculate_score(self, trucks: List[Truck]) -> float:
        """
        Calculate the quality score of a solution.
        Lower is better. Score = number of trucks + (1 - average utilization).
        """
        if not trucks:
            return float('inf')
        
        num_trucks = len(trucks)
        avg_utilization = sum(truck.get_utilization() for truck in trucks) / num_trucks
        
        # Primary objective: minimize number of trucks
        # Secondary objective: maximize utilization
        score = num_trucks * 1000 + (100 - avg_utilization)
        
        return score
    
    def copy_solution(self, trucks: List[Truck]) -> List[Truck]:
        """Deep copy a solution."""
        new_trucks = []
        for truck in trucks:
            new_truck = Truck(truck.length, truck.width, truck.height)
            for obj, x, y, z in truck.placed_objects:
                # Create a copy of the object
                new_obj = Object(obj.id, obj.length, obj.width, obj.height, obj.delivery_order)
                new_obj.original_dims = obj.original_dims
                new_truck.placed_objects.append((new_obj, x, y, z))
            new_trucks.append(new_truck)
        return new_trucks
    
    def shift_operation(self, trucks: List[Truck]) -> Optional[List[Truck]]:
        """
        Try to shift an object to a better position within the same truck
        or move it to another truck.
        """
        if not trucks:
            return None
        
        new_trucks = self.copy_solution(trucks)
        
        # Select random truck with objects
        non_empty_trucks = [t for t in new_trucks if t.placed_objects]
        if not non_empty_trucks:
            return None
        
        truck_idx = random.randint(0, len(non_empty_trucks) - 1)
        truck = non_empty_trucks[truck_idx]
        
        if not truck.placed_objects:
            return None
        
        # Select random object to shift
        obj_idx = random.randint(0, len(truck.placed_objects) - 1)
        obj, old_x, old_y, old_z = truck.placed_objects[obj_idx]
        
        # Remove object temporarily
        truck.placed_objects.pop(obj_idx)
        
        # Try to find a better position in the same truck
        new_position = self.find_best_position(obj, obj.length, obj.width, obj.height, truck)
        if new_position:
            truck.placed_objects.append((obj, new_position[0], new_position[1], new_position[2]))
            return new_trucks
        
        # Try to place in another truck
        for other_truck in new_trucks:
            if other_truck is truck:
                continue
            if self.place_object_in_truck(obj, other_truck):
                # Successfully moved to another truck
                # Remove original truck if empty
                if not truck.placed_objects:
                    new_trucks.remove(truck)
                return new_trucks
        
        # Couldn't improve, restore object
        truck.placed_objects.insert(obj_idx, (obj, old_x, old_y, old_z))
        return None
    
    def swap_operation(self, trucks: List[Truck]) -> Optional[List[Truck]]:
        """
        Try to swap two objects between trucks to improve packing.
        """
        if len(trucks) < 2:
            return None
        
        new_trucks = self.copy_solution(trucks)
        
        # Select two different trucks with objects
        non_empty_trucks = [t for t in new_trucks if t.placed_objects]
        if len(non_empty_trucks) < 2:
            return None
        
        truck1_idx = random.randint(0, len(non_empty_trucks) - 1)
        truck1 = non_empty_trucks[truck1_idx]
        
        remaining_trucks = [t for i, t in enumerate(non_empty_trucks) if i != truck1_idx]
        truck2 = random.choice(remaining_trucks)
        
        # Select random objects from each truck
        obj1_idx = random.randint(0, len(truck1.placed_objects) - 1)
        obj2_idx = random.randint(0, len(truck2.placed_objects) - 1)
        
        obj1, _, _, _ = truck1.placed_objects[obj1_idx]
        obj2, _, _, _ = truck2.placed_objects[obj2_idx]
        
        # Remove both objects
        truck1.placed_objects.pop(obj1_idx)
        truck2.placed_objects.pop(obj2_idx)
        
        # Try to place obj2 in truck1 and obj1 in truck2
        if self.place_object_in_truck(obj2, truck1) and self.place_object_in_truck(obj1, truck2):
            return new_trucks
        
        # Swap failed, return None
        return None
    
    def rotate_operation(self, trucks: List[Truck]) -> Optional[List[Truck]]:
        """
        Try to rotate an object to a different orientation.
        """
        if not trucks:
            return None
        
        new_trucks = self.copy_solution(trucks)
        
        # Select random truck with objects
        non_empty_trucks = [t for t in new_trucks if t.placed_objects]
        if not non_empty_trucks:
            return None
        
        truck = random.choice(non_empty_trucks)
        
        if not truck.placed_objects:
            return None
        
        # Select random object to rotate
        obj_idx = random.randint(0, len(truck.placed_objects) - 1)
        obj, old_x, old_y, old_z = truck.placed_objects[obj_idx]
        
        # Remove object temporarily
        truck.placed_objects.pop(obj_idx)
        
        # Try different orientations
        orientations = [
            (obj.original_dims[0], obj.original_dims[1], obj.original_dims[2]),
            (obj.original_dims[0], obj.original_dims[2], obj.original_dims[1]),
            (obj.original_dims[1], obj.original_dims[0], obj.original_dims[2]),
            (obj.original_dims[1], obj.original_dims[2], obj.original_dims[0]),
            (obj.original_dims[2], obj.original_dims[0], obj.original_dims[1]),
            (obj.original_dims[2], obj.original_dims[1], obj.original_dims[0])
        ]
        
        # Remove current orientation
        current = (obj.length, obj.width, obj.height)
        orientations = [o for o in orientations if o != current]
        
        if not orientations:
            # Restore object
            truck.placed_objects.insert(obj_idx, (obj, old_x, old_y, old_z))
            return None
        
        random.shuffle(orientations)
        
        for length, width, height in orientations:
            position = self.find_best_position(obj, length, width, height, truck)
            if position:
                obj.length, obj.width, obj.height = length, width, height
                truck.placed_objects.append((obj, position[0], position[1], position[2]))
                return new_trucks
        
        # Couldn't rotate, restore object
        truck.placed_objects.insert(obj_idx, (obj, old_x, old_y, old_z))
        return None
    
    def compact_operation(self, trucks: List[Truck]) -> Optional[List[Truck]]:
        """
        Try to compact objects by removing a truck and redistributing its objects.
        """
        if len(trucks) <= 1:
            return None
        
        new_trucks = self.copy_solution(trucks)
        
        # Select the truck with lowest utilization to empty
        truck_to_empty = min(new_trucks, key=lambda t: t.get_utilization())
        objects_to_place = [obj for obj, _, _, _ in truck_to_empty.placed_objects]
        
        # Remove the truck
        new_trucks.remove(truck_to_empty)
        
        # Try to place all objects in remaining trucks
        for obj in objects_to_place:
            placed = False
            for truck in new_trucks:
                if self.place_object_in_truck(obj, truck):
                    placed = True
                    break
            
            if not placed:
                # Couldn't redistribute, operation failed
                return None
        
        return new_trucks
    
    def local_search(self, initial_solution: List[Truck], max_iterations: int = 1000, temperature: float = 100.0) -> List[Truck]:
        """
        Perform local search with simulated annealing.
        Stops early if theoretical minimum is reached.
        """
        current_solution = self.copy_solution(initial_solution)
        current_score = self.calculate_score(current_solution)
        
        best_solution = self.copy_solution(current_solution)
        best_score = current_score
        
        operations = [
            (self.shift_operation, 0.35),
            (self.swap_operation, 0.20),
            (self.rotate_operation, 0.25),
            (self.compact_operation, 0.20)
        ]
        
        iterations_without_improvement = 0
        early_stop_threshold = max_iterations // 10  # Stop if no improvement for 10% of max iterations
        
        for iteration in range(max_iterations):
            # Check if we've reached the theoretical minimum
            if len(best_solution) <= self.min_trucks_theoretical:
                print(f"Optimal solution reached at iteration {iteration}! (Theoretical minimum: {self.min_trucks_theoretical} trucks)", file=sys.stderr)
                break
            
            # Early stopping if no improvement for a while
            if iterations_without_improvement >= early_stop_threshold:
                print(f"Early stopping at iteration {iteration} (no improvement for {early_stop_threshold} iterations)", file=sys.stderr)
                break
            
            # Select operation based on weights
            rand = random.random()
            cumulative = 0.0
            selected_operation = operations[0][0]
            
            for op, weight in operations:
                cumulative += weight
                if rand <= cumulative:
                    selected_operation = op
                    break
            
            # Apply operation
            new_solution = selected_operation(current_solution)
            
            if new_solution is None:
                iterations_without_improvement += 1
                continue
            
            new_score = self.calculate_score(new_solution)
            
            # Simulated annealing acceptance criterion
            delta = new_score - current_score
            temp = temperature * (1 - iteration / max_iterations)
            
            if delta < 0 or (temp > 0 and random.random() < math.exp(-delta / temp)):
                current_solution = new_solution
                current_score = new_score
                
                # Update best solution
                if current_score < best_score:
                    best_solution = self.copy_solution(current_solution)
                    best_score = current_score
                    iterations_without_improvement = 0  # Reset counter
                    print(f"Iteration {iteration}: New best score = {best_score:.2f}, Trucks = {len(best_solution)} (min theoretical: {self.min_trucks_theoretical})", file=sys.stderr)
                else:
                    iterations_without_improvement += 1
            else:
                iterations_without_improvement += 1
        
        return best_solution
    
    def solve(self, truck_dims: Tuple[int, int, int], objects: List[Object], max_iterations: int = 1000) -> List[Truck]:
        """
        Main solving method with local search optimization.
        """
        self.truck_dims = truck_dims
        self.objects = objects
        
        # Calculate theoretical minimum number of trucks
        self.min_trucks_theoretical = self.calculate_min_trucks(truck_dims, objects)
        truck_volume = truck_dims[0] * truck_dims[1] * truck_dims[2]
        total_objects_volume = sum(self.get_object_volume(obj) for obj in objects)
        
        print("="*60, file=sys.stderr)
        print(f"Volume Analysis:", file=sys.stderr)
        print(f"  Truck capacity: {truck_volume:,} cubic units", file=sys.stderr)
        print(f"  Total objects volume: {total_objects_volume:,} cubic units", file=sys.stderr)
        print(f"  Theoretical minimum trucks: {self.min_trucks_theoretical}", file=sys.stderr)
        print(f"  Theoretical utilization: {(total_objects_volume / (self.min_trucks_theoretical * truck_volume) * 100):.2f}%", file=sys.stderr)
        print("="*60, file=sys.stderr)
        
        # Get initial solution using base solver
        print("Generating initial solution...", file=sys.stderr)
        initial_solution = self.get_initial_solution(truck_dims, objects)
        
        if not initial_solution:
            return []  # UNSAT
        
        initial_score = self.calculate_score(initial_solution)
        print(f"Initial solution: {len(initial_solution)} trucks, score = {initial_score:.2f}", file=sys.stderr)
        
        # Check if already optimal
        if len(initial_solution) <= self.min_trucks_theoretical:
            print(f"Initial solution is already optimal! (matches theoretical minimum)", file=sys.stderr)
            return initial_solution
        
        # Perform local search optimization
        print(f"Starting local search optimization (gap to optimal: {len(initial_solution) - self.min_trucks_theoretical} trucks)...", file=sys.stderr)
        optimized_solution = self.local_search(initial_solution, max_iterations)
        
        final_score = self.calculate_score(optimized_solution)
        print("="*60, file=sys.stderr)
        print(f"Final solution: {len(optimized_solution)} trucks, score = {final_score:.2f}", file=sys.stderr)
        print(f"Improvement: {len(initial_solution) - len(optimized_solution)} trucks saved", file=sys.stderr)
        
        if len(optimized_solution) == self.min_trucks_theoretical:
            print(f" Optimal solution found! (matches theoretical minimum)", file=sys.stderr)
        else:
            print(f"Gap to theoretical minimum: {len(optimized_solution) - self.min_trucks_theoretical} trucks", file=sys.stderr)
        print("="*60, file=sys.stderr)
        
        return optimized_solution


"""
======== MAIN FUNCTION ========
"""

def main():
    """Main function to run the solver."""
    if len(sys.argv) < 2:
        print("Usage: python solver_local.py <input_file> [max_iterations]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    max_iterations = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
    
    try:
        with open(input_file, 'r') as f:
            input_text = f.read()
        
        # Parse input
        truck_dims, objects = parse_input(input_text)
        
        # Solve with local search
        solver = LocalSearchSolver()
        solution_trucks = solver.solve(truck_dims, objects, max_iterations)
        
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

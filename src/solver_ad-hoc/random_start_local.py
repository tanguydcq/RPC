import sys
import random
import math
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

def copy_objects(objects: List[Object]) -> List[Object]:
    """Create a deep copy of objects list."""
    new_objects = []
    for obj in objects:
        new_obj = Object(obj.id, obj.original_dims[0], obj.original_dims[1], obj.original_dims[2], obj.delivery_order)
        new_obj.original_dims = obj.original_dims
        new_objects.append(new_obj)
    return new_objects

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
    
    def calculate_min_trucks(self, truck_dims: Tuple[int, int, int], objects: List[Object]) -> int:
        """Calculate the theoretical minimum number of trucks needed based on volume."""
        truck_volume = truck_dims[0] * truck_dims[1] * truck_dims[2]
        total_objects_volume = sum(self.get_object_volume(obj) for obj in objects)
        min_trucks = (total_objects_volume + truck_volume - 1) // truck_volume
        return max(1, min_trucks)
    
    def satisfiability_check(self, truck_dims: Tuple[int, int, int], objects: List[Object]) -> bool:
        """Verify that all objects can individually fit within truck dimensions."""
        truck_length, truck_width, truck_height = truck_dims
        
        for obj in objects:
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
            if exclude_obj and placed_obj.id == exclude_obj.id:
                continue
                
            placed_obj_length, placed_obj_width, placed_obj_height = placed_obj.length, placed_obj.width, placed_obj.height
            
            overlap_x = not (x + obj_length <= px or px + placed_obj_length <= x)
            overlap_y = not (y + obj_width <= py or py + placed_obj_width <= y) 
            overlap_z = not (z + obj_height <= pz or pz + placed_obj_height <= z)
            
            if overlap_x and overlap_y and overlap_z:
                return True
        
        return False
    
    def find_best_position(self, obj: Object, obj_length: int, obj_width: int, obj_height: int, truck: Truck, exclude_obj: Optional[Object] = None) -> Optional[Tuple[int, int, int]]:
        """Find the lowest, leftmost, deepest position where the object can be placed."""
        truck_length, truck_width, truck_height = truck.length, truck.width, truck.height
        
        for z in range(truck_height - obj_height + 1):
            for x in range(truck_length - obj_length + 1):
                for y in range(truck_width - obj_width + 1):
                    if not self.check_collision(obj, x, y, z, obj_length, obj_width, obj_height, truck, exclude_obj):
                        return (x, y, z)
        
        return None
    
    def place_object_in_truck(self, obj: Object, truck: Truck) -> bool:
        """Try to place an object in a truck. Returns True if successful."""
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
            if (length <= truck_length and width <= truck_width and height <= truck_height):
                position = self.find_best_position(obj, length, width, height, truck)
                if position:
                    x, y, z = position
                    obj.length, obj.width, obj.height = length, width, height
                    truck.placed_objects.append((obj, x, y, z))
                    return True
        
        return False
    
    def solve_with_ordering(self, truck_dims: Tuple[int, int, int], objects: List[Object], ordering: str = "random", seed: Optional[int] = None) -> List[Truck]:
        """Generate initial solution with a specific ordering strategy."""
        objects_copy = copy_objects(objects)
        
        # Set seed BEFORE any random operations
        if seed is not None:
            random.seed(seed)
        
        if ordering == "volume_desc":
            objects_copy.sort(key=self.get_object_volume, reverse=True)
        elif ordering == "volume_asc":
            objects_copy.sort(key=self.get_object_volume)
        elif ordering == "random" or ordering == "shuffle":
            random.shuffle(objects_copy)
        
        trucks = []
        
        for obj in objects_copy:
            placed = False
            
            for truck in trucks:
                if self.place_object_in_truck(obj, truck):
                    placed = True
                    break
            
            if not placed:
                new_truck = Truck(truck_dims[0], truck_dims[1], truck_dims[2])
                trucks.append(new_truck)
                if not self.place_object_in_truck(obj, new_truck):
                    return []
        
        return trucks


"""
======== RANDOM START + LOCAL SEARCH SOLVER ========
"""

class RandomStartLocalSearchSolver(BaseSolver):
    """
    Combines random start with local search optimization.
    Generates multiple initial solutions and applies local search to each.
    """
    
    def __init__(self, truck_dims: Optional[Tuple[int, int, int]] = None, objects: Optional[List[Object]] = None):
        super().__init__(truck_dims, objects)
        self.min_trucks_theoretical = 0
    
    def calculate_score(self, trucks: List[Truck]) -> float:
        """Calculate the quality score of a solution."""
        if not trucks:
            return float('inf')
        
        num_trucks = len(trucks)
        avg_utilization = sum(truck.get_utilization() for truck in trucks) / num_trucks
        score = num_trucks * 1000 + (100 - avg_utilization)
        
        return score
    
    def copy_solution(self, trucks: List[Truck]) -> List[Truck]:
        """Deep copy a solution."""
        new_trucks = []
        for truck in trucks:
            new_truck = Truck(truck.length, truck.width, truck.height)
            for obj, x, y, z in truck.placed_objects:
                new_obj = Object(obj.id, obj.length, obj.width, obj.height, obj.delivery_order)
                new_obj.original_dims = obj.original_dims
                new_truck.placed_objects.append((new_obj, x, y, z))
            new_trucks.append(new_truck)
        return new_trucks
    
    def shift_operation(self, trucks: List[Truck]) -> Optional[List[Truck]]:
        """Try to shift an object to a better position."""
        if not trucks:
            return None
        
        new_trucks = self.copy_solution(trucks)
        non_empty_trucks = [t for t in new_trucks if t.placed_objects]
        if not non_empty_trucks:
            return None
        
        truck = random.choice(non_empty_trucks)
        if not truck.placed_objects:
            return None
        
        obj_idx = random.randint(0, len(truck.placed_objects) - 1)
        obj, old_x, old_y, old_z = truck.placed_objects[obj_idx]
        truck.placed_objects.pop(obj_idx)
        
        new_position = self.find_best_position(obj, obj.length, obj.width, obj.height, truck)
        if new_position:
            truck.placed_objects.append((obj, new_position[0], new_position[1], new_position[2]))
            return new_trucks
        
        for other_truck in new_trucks:
            if other_truck is truck:
                continue
            if self.place_object_in_truck(obj, other_truck):
                if not truck.placed_objects:
                    new_trucks.remove(truck)
                return new_trucks
        
        truck.placed_objects.insert(obj_idx, (obj, old_x, old_y, old_z))
        return None
    
    def swap_operation(self, trucks: List[Truck]) -> Optional[List[Truck]]:
        """Try to swap two objects between trucks to improve packing."""
        if len(trucks) < 2:
            return None
        
        new_trucks = self.copy_solution(trucks)
        non_empty_trucks = [t for t in new_trucks if t.placed_objects]
        if len(non_empty_trucks) < 2:
            return None
        
        truck1_idx = random.randint(0, len(non_empty_trucks) - 1)
        truck1 = non_empty_trucks[truck1_idx]
        
        remaining_trucks = [t for i, t in enumerate(non_empty_trucks) if i != truck1_idx]
        truck2 = random.choice(remaining_trucks)
        
        obj1_idx = random.randint(0, len(truck1.placed_objects) - 1)
        obj2_idx = random.randint(0, len(truck2.placed_objects) - 1)
        
        obj1, _, _, _ = truck1.placed_objects[obj1_idx]
        obj2, _, _, _ = truck2.placed_objects[obj2_idx]
        
        truck1.placed_objects.pop(obj1_idx)
        truck2.placed_objects.pop(obj2_idx)
        
        if self.place_object_in_truck(obj2, truck1) and self.place_object_in_truck(obj1, truck2):
            return new_trucks
        
        return None
    
    def rotate_operation(self, trucks: List[Truck]) -> Optional[List[Truck]]:
        """Try to rotate an object to a different orientation."""
        if not trucks:
            return None
        
        new_trucks = self.copy_solution(trucks)
        non_empty_trucks = [t for t in new_trucks if t.placed_objects]
        if not non_empty_trucks:
            return None
        
        truck = random.choice(non_empty_trucks)
        if not truck.placed_objects:
            return None
        
        obj_idx = random.randint(0, len(truck.placed_objects) - 1)
        obj, old_x, old_y, old_z = truck.placed_objects[obj_idx]
        truck.placed_objects.pop(obj_idx)
        
        orientations = [
            (obj.original_dims[0], obj.original_dims[1], obj.original_dims[2]),
            (obj.original_dims[0], obj.original_dims[2], obj.original_dims[1]),
            (obj.original_dims[1], obj.original_dims[0], obj.original_dims[2]),
            (obj.original_dims[1], obj.original_dims[2], obj.original_dims[0]),
            (obj.original_dims[2], obj.original_dims[0], obj.original_dims[1]),
            (obj.original_dims[2], obj.original_dims[1], obj.original_dims[0])
        ]
        
        current = (obj.length, obj.width, obj.height)
        orientations = [o for o in orientations if o != current]
        
        if not orientations:
            truck.placed_objects.insert(obj_idx, (obj, old_x, old_y, old_z))
            return None
        
        random.shuffle(orientations)
        
        for length, width, height in orientations:
            position = self.find_best_position(obj, length, width, height, truck)
            if position:
                obj.length, obj.width, obj.height = length, width, height
                truck.placed_objects.append((obj, position[0], position[1], position[2]))
                return new_trucks
        
        truck.placed_objects.insert(obj_idx, (obj, old_x, old_y, old_z))
        return None
    
    def compact_operation(self, trucks: List[Truck]) -> Optional[List[Truck]]:
        """Try to compact objects by removing a truck and redistributing."""
        if len(trucks) <= 1:
            return None
        
        new_trucks = self.copy_solution(trucks)
        truck_to_empty = min(new_trucks, key=lambda t: t.get_utilization())
        objects_to_place = [obj for obj, _, _, _ in truck_to_empty.placed_objects]
        new_trucks.remove(truck_to_empty)
        
        for obj in objects_to_place:
            placed = False
            for truck in new_trucks:
                if self.place_object_in_truck(obj, truck):
                    placed = True
                    break
            if not placed:
                return None
        
        return new_trucks
    
    def local_search(self, initial_solution: List[Truck], max_iterations: int = 2000, temperature: float = 100.0, verbose: bool = False) -> List[Truck]:
        """Perform local search with simulated annealing."""
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
        
        # Debug statistics
        successful_ops = 0
        failed_ops = 0
        
        for iteration in range(max_iterations):
            if len(best_solution) <= self.min_trucks_theoretical:
                if verbose:
                    print(f"    Optimal reached at iteration {iteration}!", file=sys.stderr)
                break
            
            if iterations_without_improvement >= early_stop_threshold:
                if verbose:
                    print(f"    Early stop at iteration {iteration}", file=sys.stderr)
                break
            
            rand = random.random()
            cumulative = 0.0
            selected_operation = operations[0][0]
            
            for op, weight in operations:
                cumulative += weight
                if rand <= cumulative:
                    selected_operation = op
                    break
            
            new_solution = selected_operation(current_solution)
            
            if new_solution is None:
                iterations_without_improvement += 1
                failed_ops += 1
                continue
            
            successful_ops += 1
            new_score = self.calculate_score(new_solution)
            delta = new_score - current_score
            temp = temperature * (1 - iteration / max_iterations)
            
            if delta < 0 or (temp > 0 and random.random() < math.exp(-delta / temp)):
                current_solution = new_solution
                current_score = new_score
                
                if current_score < best_score:
                    best_solution = self.copy_solution(current_solution)
                    best_score = current_score
                    iterations_without_improvement = 0
                    if verbose:
                        print(f"    Iteration {iteration}: New best score = {best_score:.2f}, Trucks = {len(best_solution)} (min theoretical: {self.min_trucks_theoretical})", file=sys.stderr)
                else:
                    iterations_without_improvement += 1
            else:
                iterations_without_improvement += 1
        
        if verbose:
            success_rate = (successful_ops / (successful_ops + failed_ops) * 100) if (successful_ops + failed_ops) > 0 else 0
            print(f"    Stats: {successful_ops} successful ops, {failed_ops} failed ops ({success_rate:.1f}% success rate)", file=sys.stderr)
        
        return best_solution
    
    def solve(self, truck_dims: Tuple[int, int, int], objects: List[Object], num_starts: int = 5, ls_iterations: int = 2000, seed_start: int = 42) -> List[Truck]:
        """
        Main solving method: Random starts + Local search.
        """
        self.truck_dims = truck_dims
        self.objects = objects
        
        if not self.satisfiability_check(truck_dims, objects):
            return []
        
        self.min_trucks_theoretical = self.calculate_min_trucks(truck_dims, objects)
        truck_volume = truck_dims[0] * truck_dims[1] * truck_dims[2]
        total_objects_volume = sum(self.get_object_volume(obj) for obj in objects)
        
        print("="*60, file=sys.stderr)
        print(f"Random Start + Local Search Solver", file=sys.stderr)
        print("="*60, file=sys.stderr)
        print(f"Volume Analysis:", file=sys.stderr)
        print(f"  Truck capacity: {truck_volume:,} cubic units", file=sys.stderr)
        print(f"  Total objects volume: {total_objects_volume:,} cubic units", file=sys.stderr)
        print(f"  Theoretical minimum trucks: {self.min_trucks_theoretical}", file=sys.stderr)
        print(f"  Number of random starts: {num_starts}", file=sys.stderr)
        print(f"  Local search iterations per start: {ls_iterations}", file=sys.stderr)
        print("="*60, file=sys.stderr)
        
        global_best_solution = None
        global_best_score = float('inf')
        global_best_info = None
        
        # Only random starts
        strategies = [(f"Random (seed={seed_start + i})", "random", seed_start + i) for i in range(num_starts)]
        
        for idx, (name, ordering, seed) in enumerate(strategies, 1):
            print(f"\n[{idx}/{len(strategies)}] {name}:", file=sys.stderr)
            
            # Generate initial solution
            initial_solution = self.solve_with_ordering(truck_dims, objects, ordering, seed)
            if not initial_solution:
                print(f"  ✗ Failed to generate initial solution", file=sys.stderr)
                continue
            
            initial_score = self.calculate_score(initial_solution)
            initial_objects_order = [obj.id for truck in initial_solution for obj, _, _, _ in truck.placed_objects]
            avg_util = sum(t.get_utilization() for t in initial_solution) / len(initial_solution)
            truck_utils = [f"{t.get_utilization():.1f}%" for t in initial_solution]
            truck_counts = [len(t.placed_objects) for t in initial_solution]
            print(f"  Initial: {len(initial_solution)} trucks, score={initial_score:.2f}, avg utilization={avg_util:.2f}%", file=sys.stderr)
            print(f"    Per-truck utils: {', '.join(truck_utils)} | Objects: {truck_counts}", file=sys.stderr)
            
            # Apply local search with fresh seed for reproducibility
            print(f"  Applying local search...", file=sys.stderr)
            if seed is not None:
                random.seed(seed + 1000)  # Different seed for LS phase
            optimized_solution = self.local_search(initial_solution, ls_iterations, verbose=True)
            optimized_score = self.calculate_score(optimized_solution)
            
            improvement = len(initial_solution) - len(optimized_solution)
            print(f"  After LS: {len(optimized_solution)} trucks, score={optimized_score:.2f} (improved by {improvement} trucks)", file=sys.stderr)
            
            # Update global best
            if optimized_score < global_best_score:
                global_best_solution = optimized_solution
                global_best_score = optimized_score
                global_best_info = (name, len(initial_solution), len(optimized_solution))
                print(f"  New global best!", file=sys.stderr)
            
            # Early stop if optimal
            if len(optimized_solution) <= self.min_trucks_theoretical:
                print(f"  Optimal solution found!", file=sys.stderr)
                break
        
        # Print summary
        print("\n" + "="*60, file=sys.stderr)
        print("Final Summary:", file=sys.stderr)
        if global_best_info:
            name, initial_trucks, final_trucks = global_best_info
            print(f"  Best solution: {final_trucks} trucks (score={global_best_score:.2f})", file=sys.stderr)
            print(f"  Found by: {name}", file=sys.stderr)
            print(f"  Total improvement: {initial_trucks} → {final_trucks} trucks", file=sys.stderr)
        
        if len(global_best_solution) == self.min_trucks_theoretical:
            print(f"  Optimal solution (matches theoretical minimum)!", file=sys.stderr)
        else:
            print(f"  Gap to theoretical minimum: {len(global_best_solution) - self.min_trucks_theoretical} trucks", file=sys.stderr)
        print("="*60, file=sys.stderr)
        
        return global_best_solution if global_best_solution else []


"""
======== MAIN FUNCTION ========
"""

def main():
    """Main function to run the solver."""
    if len(sys.argv) < 2:
        print("Usage: python random_start_local.py <input_file> [num_starts] [ls_iterations] [seed_start]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    num_starts = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    ls_iterations = int(sys.argv[3]) if len(sys.argv) > 3 else 2000
    seed_start = int(sys.argv[4]) if len(sys.argv) > 4 else 42
    
    try:
        with open(input_file, 'r') as f:
            input_text = f.read()
        
        truck_dims, objects = parse_input(input_text)
        
        solver = RandomStartLocalSearchSolver()
        solution_trucks = solver.solve(truck_dims, objects, num_starts, ls_iterations, seed_start)
        
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

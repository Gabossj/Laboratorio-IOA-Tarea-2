import numpy as np
import pandas as pd
import os
from amplpy import AMPL, ampl_notebook
import time
from typing import Dict, List, Tuple

class InstanceReader:
    @staticmethod
    def read_cap_instance(filename: str) -> Dict:
        with open(filename, 'r') as f:
            lines = f.readlines()
            
        # Read first line: number of facilities (m) and customers (n)
        m, n = map(int, lines[0].split())
        current_line = 1
        
        # Read facility data
        capacities = []
        fixed_costs = []
        for i in range(m):
            cap, cost = map(float, lines[current_line].split())
            capacities.append(cap)
            fixed_costs.append(cost)
            current_line += 1
            
        # Read customer demands
        demands = []
        for i in range(n):
            demand = float(lines[current_line].split()[0])
            demands.append(demand)
            current_line += 1
            
        # Read assignment costs and convert to numpy array for better handling
        assignment_costs = np.zeros((n, m))
        for i in range(n):
            costs = list(map(float, lines[current_line].split()))
            assignment_costs[i] = costs
            current_line += 1
            
        return {
            'm': m,
            'n': n,
            'capacities': np.array(capacities),
            'fixed_costs': np.array(fixed_costs),
            'demands': np.array(demands),
            'assignment_costs': assignment_costs
        }
    
    @staticmethod
    def read_large_instance(filename: str) -> Dict:
        with open(filename, 'r') as f:
            lines = f.readlines()
        
        # First line contains dimensions
        m, n = map(int, lines[0].split())
        current_line = 2  # Skip the '*' line
        
        # Read facility data
        capacities = []
        fixed_costs = []
        for _ in range(m):
            cap, cost = map(float, lines[current_line].split())
            capacities.append(cap)
            fixed_costs.append(cost)
            current_line += 1
            
        current_line += 1  # Skip the '*' line
        
        # Read demands
        demands = []
        for _ in range(n):
            demands.append(float(lines[current_line]))
            current_line += 1
            
        current_line += 1  # Skip the '*' line
        
        # Read assignment costs
        assignment_costs = np.zeros((n, m))
        for i in range(m):
            costs = list(map(float, lines[current_line].split()))
            assignment_costs[:, i] = costs  # Transpose while reading
            current_line += 1
            
        return {
            'm': m,
            'n': n,
            'capacities': np.array(capacities),
            'fixed_costs': np.array(fixed_costs),
            'demands': np.array(demands),
            'assignment_costs': assignment_costs
        }

class LocalSearch:
    def __init__(self, instance_data: Dict):
        self.data = instance_data
        self.best_solution = None
        self.best_cost = float('inf')
        
    def generate_initial_solution(self) -> Tuple[np.ndarray, np.ndarray]:
        """Generate a random feasible initial solution"""
        m, n = self.data['m'], self.data['n']
        open_facilities = np.zeros(m, dtype=int)
        
        # Open random facilities (at least one)
        num_facilities = max(1, np.random.randint(1, m//2))
        open_indices = np.random.choice(m, num_facilities, replace=False)
        open_facilities[open_indices] = 1
        
        assignments = np.zeros((n, m), dtype=int)
        remaining_capacity = self.data['capacities'].copy() * open_facilities
        
        # Assign customers to facilities greedily
        for i in range(n):
            # Find feasible facilities
            feasible = np.where((remaining_capacity >= self.data['demands'][i]) & (open_facilities == 1))[0]
            if len(feasible) == 0:
                # If no feasible assignment found, try generating a new solution
                return self.generate_initial_solution()
            
            # Choose the facility with minimum cost
            costs = self.data['assignment_costs'][i][feasible]
            best_idx = feasible[np.argmin(costs)]
            
            assignments[i][best_idx] = 1
            remaining_capacity[best_idx] -= self.data['demands'][i]
        
        return open_facilities, assignments
    
    def calculate_cost(self, open_facilities: np.ndarray, assignments: np.ndarray) -> float:
        """Calculate total cost for a given solution"""
        # Fixed costs for open facilities
        fixed_cost = np.sum(self.data['fixed_costs'] * open_facilities)
        
        # Assignment costs
        assignment_cost = np.sum(self.data['assignment_costs'] * assignments)
        
        return fixed_cost + assignment_cost
    
    def is_feasible(self, open_facilities: np.ndarray, assignments: np.ndarray) -> bool:
        """Check if solution is feasible"""
        # Check if each customer is assigned exactly once
        if not np.all(np.sum(assignments, axis=1) == 1):
            return False
            
        # Check capacity constraints
        facility_loads = np.dot(assignments.T, self.data['demands'])
        if np.any(facility_loads > self.data['capacities'] * open_facilities):
            return False
            
        return True
    
    def solve(self, max_iterations: int) -> Tuple[float, np.ndarray, np.ndarray]:
        """Solve using local search"""
        for iteration in range(max_iterations):
            try:
                # Generate initial solution
                current_solution = self.generate_initial_solution()
                if current_solution is None:
                    continue
                    
                current_facilities, current_assignments = current_solution
                current_cost = self.calculate_cost(current_facilities, current_assignments)
                
                improved = True
                while improved:
                    improved = False
                    
                    # Try to close/open facilities
                    for i in range(self.data['m']):
                        new_facilities = current_facilities.copy()
                        new_facilities[i] = 1 - new_facilities[i]
                        
                        if np.sum(new_facilities) > 0:  # Ensure at least one facility is open
                            new_assignments = self.generate_new_assignments(new_facilities)
                            if new_assignments is not None:
                                new_cost = self.calculate_cost(new_facilities, new_assignments)
                                if new_cost < current_cost:
                                    current_facilities = new_facilities
                                    current_assignments = new_assignments
                                    current_cost = new_cost
                                    improved = True
                
                if current_cost < self.best_cost:
                    self.best_cost = current_cost
                    self.best_solution = (current_facilities, current_assignments)
                    
            except Exception as e:
                print(f"Error in iteration {iteration}: {str(e)}")
                continue
                
        if self.best_solution is None:
            raise Exception("Could not find a feasible solution")
            
        return self.best_cost, *self.best_solution
    
    def generate_new_assignments(self, open_facilities: np.ndarray) -> np.ndarray:
        """Generate feasible assignments for given open facilities"""
        n, m = self.data['n'], self.data['m']
        assignments = np.zeros((n, m), dtype=int)
        remaining_capacity = self.data['capacities'].copy() * open_facilities
        
        # Sort customers by demand (largest first)
        customer_order = np.argsort(-self.data['demands'])
        
        for i in customer_order:
            # Find feasible facilities
            feasible = np.where((remaining_capacity >= self.data['demands'][i]) & (open_facilities == 1))[0]
            if len(feasible) == 0:
                return None
                
            # Choose the facility with minimum cost
            costs = self.data['assignment_costs'][i][feasible]
            best_idx = feasible[np.argmin(costs)]
            
            assignments[i][best_idx] = 1
            remaining_capacity[best_idx] -= self.data['demands'][i]
            
        return assignments

class ProblemSolver:
    def __init__(self):
        self.ampl = ampl_notebook(
            modules=["highs", "cbc", "gurobi", "cplex"],
            license_uuid="bb2c71f6-2b4c-4570-8eaf-4db0b0d7349a")
    
    def solve_instance(self, instance_file: str, problem_type: str, max_iterations: int) -> Dict:
        try:
            # Read instance
            if "500x500" in instance_file or "5000x5000" in instance_file:
                instance_data = InstanceReader.read_large_instance(instance_file)
            else:
                instance_data = InstanceReader.read_cap_instance(instance_file)
                
            # Solve using local search
            local_search = LocalSearch(instance_data)
            ls_start_time = time.time()
            ls_cost, ls_facilities, ls_assignments = local_search.solve(max_iterations)
            ls_time = time.time() - ls_start_time
            
            # Solve using AMPL (exact method)
            ampl_start_time = time.time()
            self.ampl.reset()
            
            # Load appropriate model
            if problem_type == "sscflp":
                self.ampl.read("sscflp.mod")
            else:
                self.ampl.read("mscflp.mod")
                
            # Set parameters
            self.ampl.param['n'] = instance_data['n']
            self.ampl.param['m'] = instance_data['m']
            self.ampl.param['c'] = instance_data['assignment_costs'].tolist()
            self.ampl.param['f'] = instance_data['fixed_costs'].tolist()
            self.ampl.param['d'] = instance_data['demands'].tolist()
            self.ampl.param['b'] = instance_data['capacities'].tolist()
            
            # Solve
            self.ampl.solve()
            ampl_time = time.time() - ampl_start_time
            
            # Get results
            objective = self.ampl.get_objective('TotalCost').value()
            
            return {
                'instance': os.path.basename(instance_file),
                'problem_type': problem_type,
                'local_search_cost': ls_cost,
                'local_search_time': ls_time,
                'exact_cost': objective,
                'exact_time': ampl_time
            }
            
        except Exception as e:
            print(f"Error solving {instance_file}: {str(e)}")
            return {
                'instance': os.path.basename(instance_file),
                'problem_type': problem_type,
                'error': str(e)
            }

def main():
    # Create results directory if it doesn't exist
    os.makedirs('resultadosInstancias', exist_ok=True)
    
    # Initialize solver
    solver = ProblemSolver()
    
    # List of instances to solve
    instances = [
        # Cap instances
        #'Problem set OR Library/cap41.txt',
        'Problem set OR Library/cap111.txt',
        # Add other instances as needed
    ]
    
    # Problem types
    problem_types = ['sscflp']  # Comment/uncomment as needed
    # problem_types = ['mscflp']
    
    # Maximum iterations for local search
    max_iterations = int(input("Enter maximum number of iterations for local search: "))
    
    # Solve instances
    results = []
    for instance in instances:
        for problem_type in problem_types:
            print(f"Solving {instance} using {problem_type}...")
            result = solver.solve_instance(instance, problem_type, max_iterations)
            results.append(result)
            
            # Save individual result
            output_file = f'resultadosInstancias/{os.path.basename(instance)}_{problem_type}_result.txt'
            with open(output_file, 'w') as f:
                for key, value in result.items():
                    f.write(f"{key}: {value}\n")
    
    # Save summary results
    df = pd.DataFrame(results)
    df.to_csv('resultadosInstancias/summary_results.csv', index=False)

if __name__ == "__main__":
    main()
# Laboratorio de Investigación de Operaciones Avanzadas
# SSCFLP y MSCFLP con Búsqueda Local y Descomposición de Benders

import numpy as np
import pandas as pd
import os
from typing import Dict, List, Tuple
from amplpy import AMPL, ampl_notebook
import time

class ProblemInstance:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.m = 0  # número de ubicaciones
        self.n = 0  # número de clientes
        self.capacities = []
        self.fixed_costs = []
        self.demands = []
        self.assignment_costs = []
        
    def read_cap_instance(self):
        """Lee instancias del tipo cap41.txt - cap131.txt"""
        with open(self.file_path, 'r') as f:
            # Primera línea: m y n
            self.m, self.n = map(int, f.readline().split())
            
            # Leer capacidades y costos fijos
            for _ in range(self.m):
                cap, cost = map(float, f.readline().split())
                self.capacities.append(cap)
                self.fixed_costs.append(cost)
            
            # Leer demandas y costos de asignación
            for j in range(self.n):
                line = list(map(float, f.readline().split()))
                self.demands.append(line[0])
                self.assignment_costs.append(line[1:])
                
    def read_500x500_instance(self):
        """Lee instancias del tipo 500x500_1.txt"""
        with open(self.file_path, 'r') as f:
            # Primera línea: m y n
            self.m, self.n = map(int, f.readline().split())
            
            # Saltar línea con *
            f.readline()
            
            # Leer capacidades y costos fijos
            for _ in range(self.m):
                cap, cost = map(float, f.readline().split())
                self.capacities.append(cap)
                self.fixed_costs.append(cost)
            
            # Saltar línea con *
            f.readline()
            
            # Leer demandas
            for _ in range(self.n):
                self.demands.append(float(f.readline()))
            
            # Saltar línea con *
            f.readline()
            
            # Leer costos de asignación
            costs = []
            while True:
                line = f.readline().strip()
                if not line:
                    break
                costs.extend(map(float, line.split()))
            
            # Reorganizar costos en matriz
            for i in range(self.n):
                row = costs[i * self.m:(i + 1) * self.m]
                self.assignment_costs.append(row)

class BendersDecomposition:
    def __init__(self, instance: ProblemInstance):
        self.instance = instance
        self.best_solution = None
        self.best_objective = float('inf')
        
    def solve_master_problem(self, cuts: List[Dict]) -> Tuple[List[int], float]:
        """Resuelve el problema maestro de Benders usando AMPL"""
        ampl = AMPL()
        
        # Cargar el modelo según el tipo de problema
        if self.problem_type == "SSCFLP":
            ampl.read("sscflp_master.mod")
        else:
            ampl.read("mscflp_master.mod")
            
        # Configurar datos
        ampl.param['m'] = self.instance.m
        ampl.param['n'] = self.instance.n
        ampl.param['f'] = self.instance.fixed_costs
        ampl.param['cuts'] = cuts
        
        # Resolver
        ampl.solve()
        
        # Obtener solución
        y = [ampl.get_variable('y')[i].value() for i in range(self.instance.m)]
        obj = ampl.get_objective('TotalCost').value()
        
        return y, obj

    def solve_subproblem(self, y: List[int]) -> Tuple[Dict, float]:
        """Resuelve el subproblema de Benders usando AMPL"""
        ampl = AMPL()
        
        # Cargar el modelo según el tipo de problema
        if self.problem_type == "SSCFLP":
            ampl.read("sscflp_sub.mod")
            
        else:
            ampl.read("mscflp_sub.mod")
            
            
        # Configurar datos
        ampl.param['m'] = self.instance.m
        ampl.param['n'] = self.instance.n
        ampl.param['c'] = self.instance.assignment_costs
        ampl.param['d'] = self.instance.demands
        ampl.param['b'] = self.instance.capacities
        ampl.param['y'] = y
        
        # Resolver
        ampl.solve()
        
        # Obtener dual values y objetivo
        pi = [ampl.get_constraint('Demand')[j].dual() for j in range(self.instance.n)]
        obj = ampl.get_objective('SubObjective').value()
        
        return {'pi': pi}, obj

class LocalSearch:
    def __init__(self, instance: ProblemInstance):
        self.instance = instance
        self.best_solution = None
        self.best_objective = float('inf')
    
    def initial_solution(self) -> List[int]:
        """Genera una solución inicial factible"""
        y = [0] * self.instance.m
        total_demand = sum(self.instance.demands)
        
        # Abrir instalaciones hasta cubrir la demanda total
        remaining_capacity = 0
        for i in range(self.instance.m):
            if remaining_capacity < total_demand:
                y[i] = 1
                remaining_capacity += self.instance.capacities[i]
        
        return y
    
    def evaluate_solution(self, y: List[int]) -> float:
        """Evalúa una solución usando el subproblema de asignación"""
        ampl = AMPL()
        
        if self.problem_type == "SSCFLP":
            ampl.read("sscflp_evaluation.mod")
            
        else:
            ampl.read("mscflp_evaluation.mod")
            
            
        # Configurar datos
        ampl.param['m'] = self.instance.m
        ampl.param['n'] = self.instance.n
        #----------------><------------------------ 
        ampl.param['c'] = self.instance.assignment_costs
        ampl.param['f'] = self.instance.fixed_costs
        ampl.param['d'] = self.instance.demands
        ampl.param['b'] = self.instance.capacities
        ampl.param['y'] = y
        
        # Resolver
        ampl.solve()
        
        return ampl.get_objective('TotalCost').value()
    
    def neighborhood(self, y: List[int]) -> List[List[int]]:
        """Genera vecinos cambiando el estado de una instalación"""
        neighbors = []
        for i in range(self.instance.m):
            y_new = y.copy()
            y_new[i] = 1 - y_new[i]  # Cambiar estado
            neighbors.append(y_new)
        return neighbors

def solve_instance(instance_path: str, max_iterations: int, problem_type: str = "SSCFLP"):
    """Resuelve una instancia combinando búsqueda local y descomposición de Benders"""
    # Cargar instancia
    instance = ProblemInstance(instance_path)
    if "500x500" in instance_path or "5000x5000" in instance_path:
        instance.read_500x500_instance()
    else:
        instance.read_cap_instance()
    
    # Inicializar algoritmos
    local_search = LocalSearch(instance)
    local_search.problem_type = problem_type
    benders = BendersDecomposition(instance)
    benders.problem_type = problem_type
    
    # Obtener solución inicial con búsqueda local
    current_solution = local_search.initial_solution()
    #----------------><------------------------ 
    current_objective = local_search.evaluate_solution(current_solution)
    best_solution = current_solution
    best_objective = current_objective
    
    # Iteraciones
    iteration = 0
    while iteration < max_iterations:
        # Búsqueda local
        neighbors = local_search.neighborhood(current_solution)
        improved = False
        
        for neighbor in neighbors:
            neighbor_objective = local_search.evaluate_solution(neighbor)
            if neighbor_objective < current_objective:
                current_solution = neighbor
                current_objective = neighbor_objective
                improved = True
                
                if current_objective < best_objective:
                    best_solution = current_solution
                    best_objective = current_objective
                break
        
        # Si no hay mejora, aplicar Benders
        if not improved:
            cuts = []
            y, obj = benders.solve_master_problem(cuts)
            
            while True:
                cut, sub_obj = benders.solve_subproblem(y)
                if sub_obj > obj + 1e-6:  # GAP tolerance
                    cuts.append(cut)
                    y, obj = benders.solve_master_problem(cuts)
                else:
                    break
            
            if obj < best_objective:
                best_solution = y
                best_objective = obj
        
        iteration += 1
    
    return best_solution, best_objective

# Configuración de directorios
#BASE_DIR = "LAB IOA"
#INSTANCE_DIR = os.path.join(BASE_DIR, "Problem set OR Library")
#RESULTS_DIR = os.path.join(BASE_DIR, "resultadosInstancias")
INSTANCE_DIR = os.path.join( "Problem set OR Library")
RESULTS_DIR = os.path.join("resultadosInstancias")

# Crear directorio de resultados si no existe
if not os.path.exists(RESULTS_DIR):
    os.makedirs(RESULTS_DIR)

# Configuración de AMPL
ampl = ampl_notebook(
    modules=["highs", "cbc", "gurobi", "cplex"],
    license_uuid="bb2c71f6-2b4c-4570-8eaf-4db0b0d7349a"
)

# Lista de instancias (comentar/descomentar según se necesite)
instances = [
    # Instancias cap
    "cap41.txt",
    #"cap42.txt",
    #"cap43.txt",
    # ... hasta cap131.txt
    
    # Instancias capa
    #"capa.txt",
    #"capb.txt",
    #"capc.txt",
    
    # Instancias grandes
    #"500x500_1.txt",
    #"5000x5000_1.txt"
]

# Seleccionar tipo de problema (comentar uno)
problem_type = "SSCFLP"
#problem_type = "MSCFLP"

# Parámetros del algoritmo
max_iterations = int(input("Ingrese el número máximo de iteraciones: "))
print(max_iterations, "iteraciones ingresadas xd")

# Resolver instancias
results = []
for instance_name in instances:
    instance_path = os.path.join(INSTANCE_DIR, instance_name)
    
    print(f"\nResolviendo instancia: {instance_name}")
    start_time = time.time()
    #----------------><------------------------ 
    solution, objective = solve_instance(instance_path, max_iterations, problem_type)
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    # Guardar resultados
    result = {
        "instance": instance_name,
        "problem_type": problem_type,
        "objective": objective,
        "time": elapsed_time,
        "solution": solution
    }
    results.append(result)
    
    # Exportar solución
    solution_path = os.path.join(RESULTS_DIR, f"{instance_name}_{problem_type}_solution.txt")
    with open(solution_path, "w") as f:
        f.write(f"Objective: {objective}\n")
        f.write(f"Time: {elapsed_time} seconds\n")
        f.write("Solution:\n")
        f.write(" ".join(map(str, solution)))

# Exportar resumen de resultados
summary_path = os.path.join(RESULTS_DIR, f"summary_{problem_type}.csv")
pd.DataFrame(results).to_csv(summary_path, index=False)

print("\nResumen de resultados:")
for result in results:
    print(f"{result['instance']}: {result['objective']} ({result['time']:.2f} seconds)")
    
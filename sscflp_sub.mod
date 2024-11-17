# Subproblema para SSCFLP (problema de asignación)
param m;                          # Número de ubicaciones potenciales
param n;                          # Número de clientes
param c{i in 1..n, j in 1..m};   # Costos de asignación
param d{i in 1..n};              # Demandas de los clientes
param b{j in 1..m};              # Capacidades de las ubicaciones
param y_fix{j in 1..m};          # Solución del problema maestro (fija)

# Variables de decisión
var x{i in 1..n, j in 1..m} >= 0;  # Fracción de demanda del cliente i satisfecha por ubicación j

# Función objetivo
minimize SubObjective: sum{i in 1..n, j in 1..m} c[i,j] * x[i,j];

# Restricciones
subject to SingleSource{i in 1..n}:
    sum{j in 1..m} x[i,j] = 1;

subject to Capacity{j in 1..m}:
    sum{i in 1..n} d[i] * x[i,j] <= b[j] * y_fix[j];

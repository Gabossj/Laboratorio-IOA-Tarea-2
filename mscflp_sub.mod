# Subproblema para MSCFLP (problema de asignación)
param m;                          # Número de ubicaciones potenciales
param n;                          # Número de clientes
param c{i in 1..m, j in 1..n};   # Costos de asignación
param D{j in 1..n};              # Demandas de los clientes
param S{i in 1..m};              # Capacidades de las ubicaciones
param y_fix{i in 1..m};          # Solución del problema maestro (fija)

# Variables de decisión
var x{i in 1..m, j in 1..n} >= 0;  # Cantidad enviada de ubicación i a cliente j

# Función objetivo
minimize SubObjective: sum{i in 1..m, j in 1..n} c[i,j] * x[i,j];

# Restricciones
subject to Demand{j in 1..n}:
    sum{i in 1..m} x[i,j] >= D[j];

subject to Capacity{i in 1..m}:
    sum{j in 1..n} x[i,j] <= S[i] * y_fix[i];

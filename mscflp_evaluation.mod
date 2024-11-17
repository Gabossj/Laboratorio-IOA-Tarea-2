# Modelo de evaluación para MSCFLP
param m;                          # Número de ubicaciones potenciales
param n;                          # Número de clientes
param c{i in 1..m, j in 1..n};   # Costos de asignación
param f{i in 1..m};              # Costos fijos de apertura
param D{j in 1..n};              # Demandas de los clientes
param S{i in 1..m};              # Capacidades de las ubicaciones
param y_fix{i in 1..m} binary;   # Solución fija de ubicaciones

# Variables de decisión
var x{i in 1..m, j in 1..n} >= 0;  # Cantidad enviada de ubicación i a cliente j

# Función objetivo
minimize TotalCost: 
    sum{i in 1..m} f[i] * y_fix[i] + sum{i in 1..m, j in 1..n} c[i,j] * x[i,j];

# Restricciones
subject to Demand{j in 1..n}:
    sum{i in 1..m} x[i,j] >= D[j];

subject to Capacity{i in 1..m}:
    sum{j in 1..n} x[i,j] <= S[i] * y_fix[i];

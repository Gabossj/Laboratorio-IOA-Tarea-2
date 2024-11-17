# Problema maestro para MSCFLP
param m;                          # Número de ubicaciones potenciales
param n;                          # Número de clientes
param f{i in 1..m};              # Costos fijos de apertura
param num_cuts >= 0 integer;      # Número de cortes de Benders
param cut_coef{1..num_cuts, i in 1..m};  # Coeficientes de los cortes
param cut_rhs{1..num_cuts};      # Términos independientes de los cortes

# Variables de decisión
var y{i in 1..m} binary;         # 1 si se abre la ubicación i, 0 en caso contrario
var theta >= 0;                  # Aproximación del costo del subproblema

# Función objetivo
minimize MasterObjective: sum{i in 1..m} f[i] * y[i] + theta;

# Cortes de Benders
subject to BendersCuts{k in 1..num_cuts}:
    theta >= sum{i in 1..m} cut_coef[k,i] * y[i] + cut_rhs[k];

# mscflp_sub.mod
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

# Problema maestro para SSCFLP
param m;                          # Número de ubicaciones potenciales
param n;                          # Número de clientes
param f{j in 1..m};              # Costos fijos de apertura
param num_cuts >= 0 integer;      # Número de cortes de Benders
param cut_coef{1..num_cuts, j in 1..m};  # Coeficientes de los cortes
param cut_rhs{1..num_cuts};      # Términos independientes de los cortes

# Variables de decisión
var y{j in 1..m} binary;         # 1 si se abre la ubicación j, 0 en caso contrario
var theta >= 0;                  # Aproximación del costo del subproblema

# Función objetivo
minimize MasterObjective: sum{j in 1..m} f[j] * y[j] + theta;

# Cortes de Benders
subject to BendersCuts{k in 1..num_cuts}:
    theta >= sum{j in 1..m} cut_coef[k,j] * y[j] + cut_rhs[k];

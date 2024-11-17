# Definición de parámetros
param m; # Número de centros de distribución
param n; # Número de clientes
param f{i in 1..m}; # Costo de apertura del centro i
param c{i in 1..m, j in 1..n}; # Costo de transporte del centro i al cliente j
param S{i in 1..m}; # Capacidad del centro i
param D{j in 1..n}; # Demanda del cliente j

# Definición de variables de decisión
var x{i in 1..m, j in 1..n} >= 0; # Cantidad de demanda del cliente j atendida por el centro i
var y{i in 1..m} binary; # Si el centro i está abierto

# Función objetivo: Minimizar los costos totales
minimize TotalCost: sum{i in 1..m} f[i] * y[i] + sum{i in 1..m, j in 1..n} c[i,j] * x[i,j];

# Restricción: La capacidad del centro no debe ser excedida
subject to Capacity{i in 1..m}: sum{j in 1..n} x[i,j] <= S[i];

# Restricción: La demanda de cada cliente debe ser satisfecha
subject to Demand{j in 1..n}: sum{i in 1..m} x[i,j] >= D[j];

# Restricción: Un centro solo puede satisfacer demanda si está abierto
subject to OpenIfAssigned{i in 1..m, j in 1..n}: x[i,j] <= S[i] * y[i];

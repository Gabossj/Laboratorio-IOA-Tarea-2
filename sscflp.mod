# Definición de parámetros
param n; # Número de clientes
param m; # Número de centros de distribución
param c{i in 1..n, j in 1..m}; # Costo de transporte del cliente i al centro j
param f{j in 1..m}; # Costo fijo de apertura del centro j
param d{i in 1..n}; # Demanda del cliente i
param b{j in 1..m}; # Capacidad del centro j

# Definición de variables de decisión
var x{j in 1..m} binary; # Si el centro j está abierto
var y{i in 1..n, j in 1..m} binary; # Si el cliente i es atendido por el centro j

# Función objetivo: Minimizar los costos totales
minimize TotalCost: sum{i in 1..n, j in 1..m} c[i,j] * y[i,j] + sum{j in 1..m} f[j] * x[j];

# Restricción: Cada cliente debe ser atendido por exactamente un centro
subject to AssignCliente{i in 1..n}: sum{j in 1..m} y[i,j] = 1;

# Restricción: La capacidad del centro no debe ser excedida
subject to Capacity{j in 1..m}: sum{i in 1..n} d[i] * y[i,j] <= b[j] * x[j];

# Restricción: Un cliente solo puede ser asignado a un centro si el centro está abierto
subject to OpenIfAssigned{i in 1..n, j in 1..m}: y[i,j] <= x[j];

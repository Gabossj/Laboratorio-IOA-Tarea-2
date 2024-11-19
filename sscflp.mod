
        set FACILITIES;
        set CUSTOMERS;

        param fixed_cost{FACILITIES} >= 0;
        param capacity{FACILITIES} >= 0;
        param demand{CUSTOMERS} >= 0;
        param var_cost{FACILITIES, CUSTOMERS} >= 0;

        var y{FACILITIES} binary;
        var x{FACILITIES, CUSTOMERS} binary;

        minimize Total_Cost:
            sum{i in FACILITIES} fixed_cost[i] * y[i] +
            sum{i in FACILITIES, j in CUSTOMERS} var_cost[i,j] * x[i,j];

        subject to Demand_Satisfaction{j in CUSTOMERS}:
            sum{i in FACILITIES} x[i,j] = 1;

        subject to Capacity_Limit{i in FACILITIES}:
            sum{j in CUSTOMERS} demand[j] * x[i,j] <= capacity[i] * y[i];
        
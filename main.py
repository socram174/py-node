from gurobipy import Model, GRB

# Crear los modelos
m1 = Model("Optimización de Perforación (sin h[j])")
m2 = Model("Optimización de Perforación (con h[j])")

# Conjuntos de perforadoras, polígonos y diámetros
drilling_machines = ['p1', 'p2']
polygons = ['Po1', 'Po2', 'Po3']
diameters = ['d1', 'd2']

# Costos de transporte por hora de cada máquina en cada polígono
transport_cost_per_hour = {('Po1', 'p1'): 4000000, ('Po1', 'p2'): 4000000,
                           ('Po2', 'p1'): 4000000, ('Po2', 'p2'): 4000000,
                           ('Po3', 'p1'): 4000000, ('Po3', 'p2'): 4000000}

# Distancias entre polígonos
distances = {('Po1', 'Po2'): 7000, ('Po2', 'Po1'): 7000,
             ('Po1', 'Po3'): 5000, ('Po3', 'Po1'): 5000,
             ('Po2', 'Po3'): 8000, ('Po3', 'Po2'): 8000,
             ('Po1', 'Po1'): 0, ('Po2', 'Po2'): 0, ('Po3', 'Po3'): 0}

# Velocidades de cada máquina en metros por hora para cada polígono
speeds = {'p1': {'Po1': 2550, 'Po2': 2550, 'Po3': 2550},
          'p2': {'Po1': 2550, 'Po2': 2550, 'Po3': 2550}}

# Requerimientos de metros de perforación en cada polígono para cada diámetro
meters_to_drill = {
    ('Po1', 'd1'): 2325, ('Po1', 'd2'): 2000,
    ('Po2', 'd1'): 4000, ('Po2', 'd2'): 1500,
    ('Po3', 'd1'): 3500, ('Po3', 'd2'): 2500
}

# Costo de perforación por metro según el diámetro
drilling_cost_per_meter = {'d1': 4827, 'd2': 4074}

# Horas disponibles mensuales para cada máquina
available_hours = {'p1': 600, 'p2': 600}

# Tiempo de perforación por metro para cada máquina y diámetro
drilling_time_per_meter = {('p1', 'd1'): 0.03125, ('p1', 'd2'): 0.06,
                           ('p2', 'd1'): 0.04, ('p2', 'd2'): 0.045}

# Variables de decisión
x = m1.addVars(polygons, drilling_machines, diameters, vtype=GRB.BINARY, name="x")
y = m1.addVars(polygons, drilling_machines, diameters, vtype=GRB.CONTINUOUS, name="y")

x2 = m2.addVars(polygons, drilling_machines, diameters, vtype=GRB.BINARY, name="x")
y2 = m2.addVars(polygons, drilling_machines, diameters, vtype=GRB.CONTINUOUS, name="y")
h = m2.addVars(drilling_machines, vtype=GRB.CONTINUOUS, name="h")

# Función objetivo
m1.setObjective(
    sum(transport_cost_per_hour[(i, j)] * (distances[(i, i_prime)] / speeds[j][i_prime]) * x[i, j, d]
        + drilling_cost_per_meter[d] * y[i, j, d]
        for i in polygons for j in drilling_machines for i_prime in polygons if i != i_prime for d in diameters),
    GRB.MINIMIZE
)

m2.setObjective(
    sum(transport_cost_per_hour[(i, j)] * (distances[(i, i_prime)] / speeds[j][i_prime]) * x2[i, j, d]
        + drilling_cost_per_meter[d] * y2[i, j, d]
        for i in polygons for j in drilling_machines for i_prime in polygons if i != i_prime for d in diameters),
    GRB.MINIMIZE
)

# Restricción 1: Cada polígono debe ser cubierto para cada diámetro por al menos una máquina
for i in polygons:
    for d in diameters:
        m1.addConstr(sum(x[i, j, d] for j in drilling_machines) >= 1, name=f"Cover_{i}_{d}")
        m2.addConstr(sum(x2[i, j, d] for j in drilling_machines) >= 1, name=f"Cover_{i}_{d}")

# Restricción 2: Los metros perforados deben igualar los requerimientos de cada polígono y diámetro
for i in polygons:
    for d in diameters:
        m1.addConstr(sum(y[i, j, d] for j in drilling_machines) == meters_to_drill[(i, d)], name=f"DrillRequirement_{i}_{d}")
        m2.addConstr(sum(y2[i, j, d] for j in drilling_machines) == meters_to_drill[(i, d)], name=f"DrillRequirement_{i}_{d}")

# Restricción 3: Consistencia lógica entre x e y
for i in polygons:
    for j in drilling_machines:
        for d in diameters:
            m1.addConstr(y[i, j, d] <= meters_to_drill[(i, d)] * x[i, j, d], name=f"Logic_{i}_{j}_{d}")
            m2.addConstr(y2[i, j, d] <= meters_to_drill[(i, d)] * x2[i, j, d], name=f"Logic_{i}_{j}_{d}")

# Restricción 4: Restricción de tiempo total para cada máquina
for j in drilling_machines:
    m1.addConstr(
        sum(drilling_time_per_meter[(j, d)] * y[i, j, d] + (distances[(i, i_prime)] / speeds[j][i_prime]) * x[i, j, d]
            for i in polygons for d in diameters for i_prime in polygons if i != i_prime) <= available_hours[j],
        name=f"TimeConstraint_{j}"
    )
    m2.addConstr(
        sum(drilling_time_per_meter[(j, d)] * y2[i, j, d] + (distances[(i, i_prime)] / speeds[j][i_prime]) * x2[i, j, d]
            for i in polygons for d in diameters for i_prime in polygons if i != i_prime) <= available_hours[j] + h[j],
        name=f"TimeConstraint_{j}"
    )

# Optimizar los modelos
m1.optimize()
m2.optimize()

# Imprimir los resultados
print("Resultados sin h[j]:")
for j in drilling_machines:
    total_time_used = 0
    for i in polygons:
        for d in diameters:
            for i_prime in polygons:
                if i != i_prime:
                    total_time_used += drilling_time_per_meter[(j, d)] * y[i, j, d].x + (distances[(i, i_prime)] / speeds[j][i_prime]) * x[i, j, d].x
    print(f"Perforadora {j}:")
    print(f"  Horas utilizadas: {total_time_used:.2f}")
    print(f"  Horas disponibles: {available_hours[j]}")

print("\nResultados con h[j]:")
for j in drilling_machines:
    total_time_used = 0
    for i in polygons:
        for d in diameters:
            for i_prime in polygons:
                if i != i_prime:
                    total_time_used += drilling_time_per_meter[(j, d)] * y2[i, j, d].x + (distances[(i, i_prime)] / speeds[j][i_prime]) * x2[i, j, d].x
    print(f"Perforadora {j}:")
    print(f"  Horas utilizadas: {total_time_used + h[j].x:.2f}")
    print(f"  Horas disponibles: {available_hours[j] + h[j].x:.2f}")

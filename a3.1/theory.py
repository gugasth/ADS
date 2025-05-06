import numpy as np

# Matriz de transição
P = np.array([
    [0.7, 0.2, 0.1],
    [0.3, 0.4, 0.3],
    [0.2, 0.3, 0.5]
])

# Transpor P e subtrair a identidade
A = P.T - np.eye(3)

# Adiciona a equação π0 + π1 + π2 = 1
A = np.vstack([A, np.ones(3)])
b = np.array([0, 0, 0, 1])

# Resolve o sistema
pi = np.linalg.lstsq(A, b, rcond=None)[0]

print("Probabilidades estacionárias:", pi)


# Taxas de tráfego em Mbps para cada estado
throughput_by_state = np.array([0, 10, 50])

# Vazão média
average_throughput = np.dot(pi, throughput_by_state)

print(f"Vazão média teórica: {average_throughput:.2f} Mbps")

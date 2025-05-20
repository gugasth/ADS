import numpy as np
import scipy.linalg
import matplotlib.pyplot as plt
import random

# ===============================
# PARÂMETROS DO SISTEMA
# ===============================

C = 5   # Capacidade total do sistema
R = 2   # Reserva mínima para tráfego prioritário (T1)

lambda1 = 10  # Taxa de chegada do tráfego prioritário (req/min)
lambda2 = 15  # Taxa de chegada do tráfego não prioritário (req/min)
mu1 = 15      # Taxa de serviço do tráfego prioritário (req/min)
mu2 = 25      # Taxa de serviço do tráfego não prioritário (req/min)

# ===============================
# CONJUNTO DE ESTADOS VÁLIDOS
# ===============================
states = []
state_to_index = {}
index_to_state = {}

index = 0
for n1 in range(C + 1):
    for n2 in range(C + 1 - n1):
        if n2 <= C - R:
            states.append((n1, n2))
            state_to_index[(n1, n2)] = index
            index_to_state[index] = (n1, n2)
            index += 1

num_states = len(states)

# ===============================
# CONSTRUÇÃO DA MATRIZ Q
# ===============================
Q = np.zeros((num_states, num_states))

for i, (n1, n2) in enumerate(states):
    # Tentativa de chegada de T1
    if (n1 + 1, n2) in state_to_index:
        j = state_to_index[(n1 + 1, n2)]
        Q[i, j] = lambda1

    # Tentativa de chegada de T2
    if (n1, n2 + 1) in state_to_index:
        j = state_to_index[(n1, n2 + 1)]
        Q[i, j] = lambda2

    # Saída de T1
    if n1 > 0 and (n1 - 1, n2) in state_to_index:
        j = state_to_index[(n1 - 1, n2)]
        Q[i, j] = n1 * mu1

    # Saída de T2
    if n2 > 0 and (n1, n2 - 1) in state_to_index:
        j = state_to_index[(n1, n2 - 1)]
        Q[i, j] = n2 * mu2

    # Diagonal principal
    Q[i, i] = -np.sum(Q[i, :])

# ===============================
# SOLUÇÃO ANALÍTICA: πQ = 0
# ===============================
# Sistema homogêneo com a restrição de que soma das probabilidades é 1
A = Q.T
A[-1, :] = 1  # Substitui última equação pela condição de normalização
b = np.zeros(num_states)
b[-1] = 1

pi = np.linalg.solve(A, b)

# ===============================
# CÁLCULOS DOS INDICADORES
# ===============================
# Estados que bloqueiam T1: n1 + n2 = C
block_T1 = [i for i, (n1, n2) in enumerate(states) if n1 + n2 == C]
P_block_T1 = np.sum(pi[block_T1])

# Estados que bloqueiam T2: n1 + n2 = C ou n2 = R
block_T2 = [i for i, (n1, n2) in enumerate(states) if n1 + n2 == C or n2 == R]
P_block_T2 = np.sum(pi[block_T2])

# Utilização média
U = sum((n1 + n2) * pi[i] for i, (n1, n2) in enumerate(states)) / C

# Número médio de conexões simultâneas
L1 = sum(n1 * pi[i] for i, (n1, n2) in enumerate(states))
L2 = sum(n2 * pi[i] for i, (n1, n2) in enumerate(states))

# Tempo em estados de capacidade máxima
P_full = sum(pi[i] for i, (n1, n2) in enumerate(states) if n1 + n2 == C)

# ===============================
# SIMULAÇÃO DA CTMC — Abordagem A
# ===============================
T = 10000  # Tempo total de simulação (minutos)
current_state = (0, 0)
current_time = 0

state_counts = np.zeros(num_states)

while current_time < T:
    i = state_to_index[current_state]
    rates = []

    # Coleta taxas possíveis de transição
    n1, n2 = current_state

    if (n1 + 1, n2) in state_to_index:
        rates.append((lambda1, (n1 + 1, n2)))

    if (n1, n2 + 1) in state_to_index:
        rates.append((lambda2, (n1, n2 + 1)))

    if n1 > 0 and (n1 - 1, n2) in state_to_index:
        rates.append((n1 * mu1, (n1 - 1, n2)))

    if n2 > 0 and (n1, n2 - 1) in state_to_index:
        rates.append((n2 * mu2, (n1, n2 - 1)))

    total_rate = sum(rate for rate, _ in rates)
    if total_rate == 0:
        break

    # Tempo de estadia exponencial
    dt = np.random.exponential(1 / total_rate)
    current_time += dt
    state_counts[i] += dt

    # Sorteio do destino
    r = random.uniform(0, total_rate)
    acc = 0
    for rate, next_state in rates:
        acc += rate
        if r < acc:
            current_state = next_state
            break

# Estimativa de π por simulação
pi_sim = state_counts / np.sum(state_counts)

# ===============================
# COMPARAÇÃO
# ===============================
print("\n=== COMPARAÇÃO ANALÍTICA VS SIMULAÇÃO ===")
print(f"Prob. de bloqueio T1 (analítica): {P_block_T1:.4f}")
print(f"Prob. de bloqueio T1 (simulada):  {np.sum(pi_sim[block_T1]):.4f}")
print(f"Prob. de bloqueio T2 (analítica): {P_block_T2:.4f}")
print(f"Prob. de bloqueio T2 (simulada):  {np.sum(pi_sim[block_T2]):.4f}")
print(f"Utilização média (analítica):     {U:.4f}")
print(f"Utilização média (simulada):      {sum((n1 + n2) * pi_sim[i] for i, (n1, n2) in enumerate(states)) / C:.4f}")

# ===============================
# VISUALIZAÇÃO
# ===============================
plt.figure(figsize=(12, 6))
plt.plot(pi, label="Analítica")
plt.plot(pi_sim, label="Simulada", linestyle="dashed")
plt.title("Distribuição Estacionária: Analítica vs Simulada")
plt.xlabel("Índice do Estado")
plt.ylabel("Probabilidade")
plt.legend()
plt.grid()
plt.tight_layout()
plt.show()

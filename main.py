import time
import subprocess
import os
import signal
import csv

def get_eid(file: str) -> str:
    output = subprocess.check_output(f"sudo imunes -b {file} | grep 'ID'", shell=True)
    output = output.decode("utf-8")
    eid = output.split("\n")[-2].split(" = ")[1]
    return eid

file = "miniprojeto.imn"
eid = get_eid(file)

buffers = [64_000, 208_000]
packet_losses = [0, 1000000]

# Cria o arquivo CSV e escreve o cabeçalho
with open("resultados.csv", "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["packet_loss", "buffer", "bandwidth_mbps"])

    for i in range(0,8):
        for p in packet_losses:
            print("Packet Loss =====================================", p)
            subprocess.call(f"sudo vlink -BER {p} router1:pc1@{eid}", shell=True)

            time.sleep(2)

            for b in buffers:
                print("BUFFER ***************************", b)

                server_cmd = f"sudo himage pc4@{eid} iperf -s -w {b}"
                server_process = subprocess.Popen(server_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)

                time.sleep(2)

                client_cmd = f'sudo himage pc1@{eid} iperf -c 10.0.2.20 -n 100M -i 1'
                output = subprocess.check_output(client_cmd, shell=True).decode("utf-8")
                print(output)

                # Procura a última linha com "Mbits/sec" que contém a vazão total
                final_bandwidth = None
                for line in output.strip().split("\n")[::-1]:
                    if "Mbits/sec" in line:
                        try:
                            final_bandwidth = line.strip().split()[-2]  # valor numérico
                            break
                        except IndexError:
                            continue

                if final_bandwidth:
                    writer.writerow([p, b, final_bandwidth])
                else:
                    print("⚠️ Vazão não encontrada no output.")

                try:
                    os.killpg(os.getpgid(server_process.pid), signal.SIGTERM)
                except Exception as e:
                    print(f"Erro ao encerrar o servidor: {e}")

                time.sleep(2)

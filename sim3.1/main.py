import heapq
import random, heapq, itertools


class Event:
    def __init__(self, time):
        self.time = time  # Tempo em que o evento ocorre

    def __lt__(self, other):
        # Define a ordem de prioridade na fila de eventos (menor tempo vem primeiro)
        return self.time < other.time

    def processing_event(self, simulator):
        # Deve ser implementado pelas subclasses
        raise NotImplementedError("Subclasses devem implementar este método")

class Simulator:
    def __init__(self, end_time):
        self.current_time = 0              # Tempo atual da simulação
        self.event_queue = []              # Fila de eventos futuros (min-heap)
        self.end_time = end_time           # Tempo máximo da simulação

    def schedule(self, event):
        # Insere um evento na fila de eventos futuros
        heapq.heappush(self.event_queue, event)

    def run(self):
        # Executa a simulação, processando os eventos em ordem cronológica
        while self.event_queue and self.current_time < self.end_time:
            event = heapq.heappop(self.event_queue)
            self.current_time = event.time
            event.processing_event(self)


# ----------------- modelos básicos -----------------
class Channel:
    def __init__(self, prop_delay):
        self.prop_delay = prop_delay          # (s)
        self.active_txs = []                  # [(station, start_time, end_time)]
        self.collisions = 0

    def is_busy(self, now, local_station=None):
        return any(
            (now >= start + self.prop_delay) and (now < end)
            for st, start, end in self.active_txs
            if st != local_station
        )



    def register_tx(self, station, start, end):
        self.clear_finished(start)
        # Colisão se existe outra transmissão que começou há menos que prop_delay
        congested = [
            (st, s, e) for st, s, e in self.active_txs
            if abs(start - s) < self.prop_delay
        ]
        if congested:
            # marcar colisão de todos os envolvidos
            self.collisions += 1 + len({
                st for st, _, _ in congested if not st.in_collision
            })
            for st, *_ in congested:
                st.in_collision = True
            station.in_collision = True
        self.active_txs.append((station, start, end))

    def clear_finished(self, now):
        self.active_txs = [(st, s, e) for st, s, e in self.active_txs if e > now]


class Station:
    def __init__(self, name, sim, pkt_gen, max_queue_bytes=5000):
        self.name = name
        self.sim   = sim
        self.pkt_gen = pkt_gen              # gerador (iterable) de (arrival_time, pkt_size)
        self.queue_bytes = 0
        self.queue       = []               # [(pkt_size)]
        self.max_q       = max_queue_bytes
        # contadores
        self.tx_bytes_ok = 0
        self.backoffs    = 0                # backoffs por colisão
        self.busy_backoffs = 0              # backoffs por canal ocupado
        self.in_collision = False           # flag temporária

    # ---------- API usada pelos eventos ----------
    def enqueue(self, size):
        if self.queue_bytes + size <= self.max_q:
            self.queue.append(size)
            self.queue_bytes += size
            return True
        return False                         # descarta se fila cheia

    def schedule_next_tx_if_idle(self):
        if self.queue:
            # Verifica se o canal está ocupado antes de transmitir
            if self.sim.channel.is_busy(self.sim.current_time, local_station=self):
                # Canal ocupado: agenda backoff aleatório
                self.busy_backoffs += 1
                bo = self.sim.rng.uniform(self.sim.bo_min, self.sim.bo_max)
                self.sim.schedule(BackoffExpireEvent(self.sim.current_time + bo, self, None))
            else:
                # Canal livre: transmite imediatamente
                self.sim.schedule(StartTxEvent(self.sim.current_time, self))

class PacketArrivalEvent(Event):
    def __init__(self, time, station, pkt_size):
        super().__init__(time)
        self.station, self.pkt_size = station, pkt_size

    def processing_event(self, sim):
        self.station.enqueue(self.pkt_size)
        self.station.schedule_next_tx_if_idle()          # tenta transmitir
        # agenda próxima chegada (só se gerador ainda tiver pacotes)
        try:
            t, size = next(self.station.pkt_gen)
            sim.schedule(PacketArrivalEvent(t, self.station, size))
        except StopIteration:
            pass

class StartTxEvent(Event):
    def __init__(self, time, station):
        super().__init__(time)
        self.station = station

    def processing_event(self, sim):
        st, ch = self.station, sim.channel
        size = st.queue.pop(0); st.queue_bytes -= size
        st.in_collision = False
        tx_time = size*8 / sim.link_bps                       # s
        ch.register_tx(st, self.time, self.time+tx_time)
        sim.schedule(EndTxEvent(self.time + tx_time, st, size))

class EndTxEvent(Event):
    def __init__(self, time, station, size):
        super().__init__(time)
        self.station, self.size = station, size

    def processing_event(self, sim):
        ch = sim.channel
        ch.clear_finished(self.time)
        if self.station.in_collision:
            # colisão: pacote não chegou; agendar backoff
            bo = sim.rng.uniform(sim.bo_min, sim.bo_max)
            self.station.backoffs += 1
            sim.schedule(BackoffExpireEvent(self.time + bo, self.station, self.size))
        else:
            # sucesso: credita vazão
            self.station.tx_bytes_ok += self.size
        # tentar enviar próximo
        self.station.schedule_next_tx_if_idle()

class BackoffExpireEvent(Event):
    def __init__(self, time, station, pkt_size):
        super().__init__(time)
        self.station, self.pkt_size = station, pkt_size

    def processing_event(self, sim):
        if self.pkt_size is not None:
            # Backoff por colisão: devolve o pacote na frente da fila
            self.station.queue.insert(0, self.pkt_size)
            self.station.queue_bytes += self.pkt_size
        
        # Tenta transmitir novamente (pode ser canal ocupado ou retry de colisão)
        self.station.schedule_next_tx_if_idle()


class DESCollisionSim(Simulator):
    def __init__(self, end_time, seed=42):
        super().__init__(end_time)
        self.rng = random.Random(seed)
        self.link_bps = 10_000_000          # 10 Mbps
        self.channel  = Channel(prop_delay=0.00333)   # 3,33 ms
        # parâmetros de backoff (sugestão simples)
        self.bo_min, self.bo_max = 0.001, 0.02

        # ----- construir estações -----
        self.stationA = Station("A", self, pkt_gen=self._poisson_gen(lmbd_pps=50))  # λ=50 pps
        self.stationB = Station("B", self, pkt_gen=self._periodic_gen(period=0.040, size=500))  # 40ms = 25 pps
        # agendar chegadas iniciais
        #self._prime_arrivals()
        tA, sizeA = next(self.stationA.pkt_gen)
        tB, sizeB = next(self.stationB.pkt_gen)
        self.schedule(PacketArrivalEvent(tA, self.stationA, sizeA))
        self.schedule(PacketArrivalEvent(tB, self.stationB, sizeB))

    # ---------- Geradores de chegada ----------
    def _poisson_gen(self, lmbd_pps):
        t = self.current_time
        while True:
            t += self.rng.expovariate(lmbd_pps)
            size = self.rng.randint(20, 1000)
            yield t, size

    def _periodic_gen(self, period, size):
        t = self.current_time
        while True:
            t += period
            yield t, size

    def _prime_arrivals(self):
        # Força as duas estações a tentarem transmitir no mesmo instante
        t = self.current_time + 0.001
        sizeA = 1000
        sizeB = 1000
        self.schedule(PacketArrivalEvent(t, self.stationA, sizeA))
        self.schedule(PacketArrivalEvent(t, self.stationB, sizeB))

    # ---------- Relatório final ----------
    def report(self):
        def throughput(bytes_ok):               # bps
            return (bytes_ok * 8) / self.end_time
        print("=== Resultados ===")
        for st in (self.stationA, self.stationB):
            print(f"Estação {st.name}:")
            print(f"  Vazão efetiva     : {throughput(st.tx_bytes_ok):,.1f} bit/s")
            print(f"  Back‑offs (colisão): {st.backoffs}")
            print(f"  Back‑offs (ocupado): {st.busy_backoffs}")
            print(f"  Total back‑offs   : {st.backoffs + st.busy_backoffs}")
        print(f"Colisões totais       : {self.channel.collisions}")

if __name__ == "__main__":
    sim = DESCollisionSim(end_time=5.0)
    sim.run()
    sim.report()

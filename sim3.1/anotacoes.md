Classe simulação deve ter:

- fila de eventos
- método que escalona (que empurra pra dentro da fila)
- método run que é o loop principal da simulação
- construtor que zera o tempo inicial e inicializa a fila eventqueue

--------

Funcionamento do método run:
- enquanto a fila de eventos não for vazia, vai ficar no loop
e aí no loop:
	pega o cara que ta no topo da eventqueue
	desenfileira a fila
	pega o tempo do evento (evento tem um atributo time)
	processa o evento (nextevent)
	deleta o evento (nextevent)

-------
evento tem que ter sua timestamp


trabalho 1:
verificar se o meio está ocupado (colisão), se estiver espera um tempo e faz denovo (retry).

OBS:
Colisão ocorre quanto a estação manda um pacote e o meio não está ocupado
mas a propagação do pacote que a outra já mandou, ainda está ocorrendo.
# ProjetoAgentes

## Como testar pelo terminal

- Certifique-se de ter Python 3 instalado. Em alguns sistemas o comando e `python`, noutros `python3`.
- A partir do terminal:

### Executar a simulacao

Treino (Q-learning):
```
python3 main.py parametros_farol.json
python3 main.py parametros_foraging.json
```

Teste (Q-learning, politica aprendida fixa):
```
python3 main.py parametros_farol_teste.json
python3 main.py parametros_foraging_teste.json
```

Politica fixa (heuristica):
```
python3 main.py parametros_farol_fixo.json
python3 main.py parametros_foraging_fixo.json
```

Algoritmo genetico (treino):
```
python3 main.py parametros_farol_genetico.json
python3 main.py parametros_foraging_genetico.json
```

Algoritmo genetico (teste):
```
python3 main.py parametros_farol_genetico_teste.json
python3 main.py parametros_foraging_genetico_teste.json
```

### Comparar metricas (fixo vs Q-learning teste vs genetico teste)

Farol:
```
python3 compare_metricas.py metricas/farol/metricas_farol_fixo.json metricas/farol/metricas_farol_q_learning_teste.json metricas/farol/metricas_farol_genetico_teste.json
```

Foraging:
```
python3 compare_metricas.py metricas/foraging/metricas_foraging_fixo.json metricas/foraging/metricas_foraging_q_learning_teste.json metricas/foraging/metricas_foraging_genetico_teste.json
```

### Ver graficos das metricas

O `plot_metricas.py` mostra curvas de recompensa, passos e taxa de sucesso.
Requer `matplotlib` instalado.

Treino (Q-learning):
```
python3 plot_metricas.py metricas/farol/metricas_farol_q_learning.json
python3 plot_metricas.py metricas/foraging/metricas_foraging_q_learning.json
```

Treino (genetico):
```
python3 plot_metricas.py metricas/farol/metricas_farol_genetico.json
python3 plot_metricas.py metricas/foraging/metricas_foraging_genetico.json
```

Teste (politicas fixas aprendidas):
```
python3 plot_metricas.py metricas/farol/metricas_farol_q_learning_teste.json
python3 plot_metricas.py metricas/foraging/metricas_foraging_q_learning_teste.json
```

Pode passar varios ficheiros de uma vez; abre uma janela por ficheiro.
Ficheiros `_passos.json` guardam o historico passo a passo.

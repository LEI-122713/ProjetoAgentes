# ProjetoAgentes

## Como testar pelo terminal

- Certifique-se de ter Python 3 instalado. Em alguns sistemas o comando é `python`, noutros `python3`.
- A partir do terminal correr:

### Executar a simulação
```
python3 main.py parametros_farol.json
```
Troque o ficheiro de parâmetros para outro cenário, por exemplo:
- Farol (algoritmo genético): `python3 main.py parametros_farol_genetico.json`
- Farol (política fixa): `python3 main.py parametros_farol_fixo.json`
- Foraging (aprendizagem): `python3 main.py parametros_foraging.json`
- Foraging (algoritmo genético): `python3 main.py parametros_foraging_genetico.json`

### Comparar métricas (aprendizagem vs teste)
Use o script `compare_metricas.py` passando dois ficheiros `.json` de métricas:
```
python3 compare_metricas.py metricas/farol/metricas_farol_fixo.json metricas/farol/metricas_farol_q_learning.json
python3 compare_metricas.py metricas/foraging/metricas_foraging_fixo.json metricas/foraging/metricas_foraging_q_learning.json
```
Substitua pelos ficheiros que quiser comparar (há variantes `_politica_fixa` e `_passos`).

### Ver gráficos das métricas
O `plot_metricas.py` mostra curvas de recompensa, passos e taxa de sucesso:
```
python3 plot_metricas.py metricas/farol/metricas_farol_q_learning.json
```
Pode passar vários ficheiros de uma vez; abre uma janela por ficheiro.

import json
import time
from core.AgenteThread import AgenteThread


# Motor principal que carrega parametros, cria ambiente/agentes, corre episodios (observa-age-avalia), regista metricas e fecha threads
class MotorDeSimulacao:
    def __init__(self, ficheiro_parametros: str | None = None, parametros: dict | None = None):
        self.agentes = []
        self.agente_threads = []
        self.ambiente = None
        self.passo_atual = 0
        self.max_passos = 10
        self.ficheiro_parametros = ficheiro_parametros
        self.parametros = parametros or {}
        self.recompensa_total = 0.0
        self.historico_passos = []
        self.historico_passos_todos = []
        self.episodios = 1
        self.ficheiro_metricas = "metricas.json"
        self.ficheiro_passos = "metricas_passos.json"
        self.logger = None
        self.render = False
        self.render_window = False
        self.render_sleep = 0.0
        self.gamma_desconto = 1.0
        self.visualizador = None

    @staticmethod
    def cria(nome_do_ficheiro_parametros: str) -> "MotorDeSimulacao":
        with open(nome_do_ficheiro_parametros, "r", encoding="utf-8") as f:
            parametros = json.load(f)

        motor = MotorDeSimulacao(
            ficheiro_parametros=nome_do_ficheiro_parametros,
            parametros=parametros,
        )

        motor.max_passos = parametros.get("max_passos", motor.max_passos)
        motor.episodios = parametros.get("episodios", motor.episodios)
        motor.ficheiro_metricas = parametros.get("ficheiro_metricas", motor.ficheiro_metricas)
        motor.ficheiro_passos = parametros.get("ficheiro_passos", motor._derivar_ficheiro_passos())
        motor.render = parametros.get("render", motor.render)
        motor.render_window = parametros.get("render_window", motor.render_window)
        motor.render_sleep = parametros.get("render_sleep", motor.render_sleep)
        motor.gamma_desconto = parametros.get("gamma_desconto", motor.gamma_desconto)
        motor._construir_ambiente(parametros.get("ambiente", {}))
        motor._construir_agentes(parametros.get("agentes", []))
        motor._construir_logger()
        motor._construir_visualizador()

        return motor

    def _derivar_ficheiro_passos(self):
        base = self.ficheiro_metricas
        if base.endswith(".json"):
            return base.replace(".json", "_passos.json")
        return base + "_passos.json"

    def listaAgentes(self):
        return self.agentes

    def _construir_ambiente(self, cfg_ambiente: dict):
        tipo = cfg_ambiente.get("tipo", "farol")

        if tipo == "farol":
            from ambientes.AmbienteFarol import AmbienteFarol

            largura = cfg_ambiente.get("largura", 5)
            altura = cfg_ambiente.get("altura", 5)
            pos_farol = tuple(cfg_ambiente.get("farol", (largura - 1, altura - 1)))
            obstaculos = [tuple(o) for o in cfg_ambiente.get("obstaculos", [])]

            self.ambiente = AmbienteFarol(
                largura=largura,
                altura=altura,
                pos_farol=pos_farol,
                obstaculos=obstaculos,
            )
        elif tipo == "foraging":
            from ambientes.AmbienteForaging import AmbienteForaging

            largura = cfg_ambiente.get("largura", 7)
            altura = cfg_ambiente.get("altura", 7)
            recursos = [tuple(r) for r in cfg_ambiente.get("recursos", [])]
            valores_recursos = cfg_ambiente.get("valores_recursos", {})
            ninhos = [tuple(n) for n in cfg_ambiente.get("ninhos", [])]
            obstaculos = [tuple(o) for o in cfg_ambiente.get("obstaculos", [])]

            self.ambiente = AmbienteForaging(
                largura=largura,
                altura=altura,
                recursos=recursos,
                valores_recursos=valores_recursos,
                ninhos=ninhos,
                obstaculos=obstaculos,
            )
        else:
            raise ValueError(f"Ambiente desconhecido: {tipo}")

    def _construir_agentes(self, lista_cfg_agentes: list):
        for cfg in lista_cfg_agentes:
            tipo = cfg.get("tipo", "farol")
            algoritmo = cfg.get("algoritmo", "q_learning")
            nome = cfg.get("nome", "agente")
            posicao_inicial = tuple(cfg.get("posicao_inicial", (0, 0)))

            if tipo == "farol":
                if algoritmo == "genetico":
                    from agentes.AgenteFarolGenetico import AgenteFarolGenetico

                    agente = AgenteFarolGenetico(
                        nome,
                        modo=cfg.get("modo", "aprendizagem"),
                        ficheiro_genoma=cfg.get("ficheiro_genoma", None),
                        populacao=cfg.get("populacao", 12),
                        elitismo=cfg.get("elitismo", 2),
                        taxa_mutacao=cfg.get("taxa_mutacao", 0.1),
                        prob_cruzamento=cfg.get("prob_cruzamento", 0.7),
                    )
                else:
                    from agentes.AgenteFarol import AgenteFarol

                    agente = AgenteFarol(
                        nome,
                        modo=cfg.get("modo", "teste"),
                        ficheiro_qtable=cfg.get("q_table", None),
                        epsilon=cfg.get("epsilon", 0.2),
                        alpha=cfg.get("alpha", 0.5),
                        gamma=cfg.get("gamma", 0.9),
                        epsilon_min=cfg.get("epsilon_min", 0.05),
                        epsilon_decay=cfg.get("epsilon_decay", 0.99),
                    )
            elif tipo == "foraging":
                from agentes.AgenteForaging import AgenteForaging

                agente = AgenteForaging(
                    nome,
                    modo=cfg.get("modo", "teste"),
                    ficheiro_qtable=cfg.get("q_table", None),
                    epsilon=cfg.get("epsilon", 0.2),
                    alpha=cfg.get("alpha", 0.5),
                    gamma=cfg.get("gamma", 0.9),
                    epsilon_min=cfg.get("epsilon_min", 0.05),
                    epsilon_decay=cfg.get("epsilon_decay", 0.99),
                )
            else:
                raise ValueError(f"Tipo de agente desconhecido: {tipo}")

            self.agentes.append(agente)
            thr = AgenteThread(agente)
            thr.start()
            self.agente_threads.append(thr)

            if self.ambiente and hasattr(self.ambiente, "adicionaAgente"):
                self.ambiente.adicionaAgente(agente, posicao_inicial)

    def _construir_logger(self):
        from core.Logger import Logger

        self.logger = Logger()

    def _construir_visualizador(self):
        if not self.render_window:
            return
        try:
            from visualizacao import VisualizadorGrid
        except ImportError:
            print("Aviso: matplotlib nao disponivel; render_window desativado.")
            self.render_window = False
            return
        if hasattr(self.ambiente, "grid_state"):
            self.visualizador = VisualizadorGrid()

    def _extrair_resultado(self, resultado):
        recompensa = 0.0
        terminou = False

        if isinstance(resultado, dict):
            recompensa = float(resultado.get("recompensa", 0.0))
            terminou = bool(resultado.get("terminou", False))
        elif isinstance(resultado, (list, tuple)) and resultado:
            recompensa = float(resultado[0])
            if len(resultado) > 1:
                terminou = bool(resultado[1])
        elif isinstance(resultado, (int, float)):
            recompensa = float(resultado)

        return recompensa, terminou

    def executa(self):
        for ep in range(1, self.episodios + 1):
            print(f"===== EPISODIO {ep} =====")
            self._reset_episodio()
            sucesso_ep = False

            for _ in range(self.max_passos):
                self.passo_atual += 1
                terminou_episodio = False
                print(f"--- PASSO {self.passo_atual} ---")

                for thr in self.agente_threads:
                    agente = thr.agente
                    obs = self.ambiente.observacaoPara(agente)
                    accao = thr.passo(obs)

                    resultado = self.ambiente.agir(accao, agente)
                    recompensa, terminou = self._extrair_resultado(resultado)

                    nova_obs = self.ambiente.observacaoPara(agente)
                    thr.avaliar(recompensa, nova_obs, terminou)

                    pos = self.ambiente.posicoes_agentes.get(agente)
                    self.recompensa_total += recompensa
                    fator = self.gamma_desconto ** max(self.passo_atual - 1, 0)
                    self.recompensa_descontada_total += fator * recompensa
                    self.historico_passos.append({
                        "episodio": ep,
                        "passo": self.passo_atual,
                        "agente": agente.nome,
                        "accao": accao.tipo,
                        "recompensa": recompensa,
                        "posicao": pos,
                    })

                    print(f"> {agente.nome} faz {accao.tipo}, recompensa {recompensa}, posicao {pos}")
                    if terminou:
                        terminou_episodio = True
                        sucesso_ep = True

                self.ambiente.atualizacao()

                if self.render and hasattr(self.ambiente, "render"):
                    self.ambiente.render()
                    if self.render_sleep > 0:
                        time.sleep(self.render_sleep)
                if self.render_window and self.visualizador and hasattr(self.ambiente, "grid_state"):
                    grelha = self.ambiente.grid_state()
                    self.visualizador.mostra(grelha)
                    if self.render_sleep > 0:
                        time.sleep(self.render_sleep)

                if hasattr(self.ambiente, "terminou") and callable(self.ambiente.terminou):
                    if self.ambiente.terminou():
                        terminou_episodio = True
                        sucesso_ep = True

                if terminou_episodio:
                    print("Condicao de termino atingida pelo ambiente/acao.")
                    break

            if self.logger:
                self.logger.registar_episodio(
                    ep,
                    self.recompensa_total,
                    self.passo_atual,
                    self.recompensa_descontada_total,
                    sucesso_ep,
                )
            # guarda historico do episodio antes de reset
            self.historico_passos_todos.extend(self.historico_passos)
            self._guardar_politicas()

            print(f"Recompensa total do episodio {ep}: {self.recompensa_total}")
            print(f"Recompensa descontada do episodio {ep}: {self.recompensa_descontada_total}")
            print(f"Passos executados: {self.passo_atual}")

            self._reset_agentes()

        if self.logger:
            self.logger.guardar(self.ficheiro_metricas)
            if self.historico_passos_todos:
                self.logger.guardar_passos(self.historico_passos_todos, self.ficheiro_passos)
        self._parar_threads()

    def _reset_episodio(self):
        self.passo_atual = 0
        self.recompensa_total = 0.0
        self.recompensa_descontada_total = 0.0
        self.historico_passos = []
        if hasattr(self.ambiente, "reset"):
            self.ambiente.reset()

    def _reset_agentes(self):
        for agente in self.agentes:
            if hasattr(agente, "reset"):
                agente.reset()

    def _parar_threads(self):
        for thr in self.agente_threads:
            thr.parar()
        for thr in self.agente_threads:
            thr.join(timeout=1.0)

    def _guardar_politicas(self):
        for agente in self.agentes:
            if hasattr(agente, "guardar_politica") and callable(agente.guardar_politica):
                agente.guardar_politica()

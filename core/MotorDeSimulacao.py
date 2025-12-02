import json
import time


class MotorDeSimulacao:
    def __init__(self, ficheiro_parametros: str | None = None, parametros: dict | None = None):
        self.agentes = []
        self.ambiente = None
        self.passo_atual = 0
        self.max_passos = 10
        self.ficheiro_parametros = ficheiro_parametros
        self.parametros = parametros or {}
        self.recompensa_total = 0.0
        self.historico_passos = []
        self.episodios = 1
        self.ficheiro_metricas = "metricas.json"
        self.logger = None
        self.render = False
        self.render_sleep = 0.0

    # --- método estático pedido no enunciado ---
    @staticmethod
    def cria(nome_do_ficheiro_parametros: str) -> "MotorDeSimulacao":
        """
        Cria e devolve uma instância de MotorDeSimulacao
        a partir de um ficheiro de parâmetros JSON.
        """
        with open(nome_do_ficheiro_parametros, "r", encoding="utf-8") as f:
            parametros = json.load(f)

        motor = MotorDeSimulacao(
            ficheiro_parametros=nome_do_ficheiro_parametros,
            parametros=parametros,
        )

        motor.max_passos = parametros.get("max_passos", motor.max_passos)
        motor.episodios = parametros.get("episodios", motor.episodios)
        motor.ficheiro_metricas = parametros.get("ficheiro_metricas", motor.ficheiro_metricas)
        motor.render = parametros.get("render", motor.render)
        motor.render_sleep = parametros.get("render_sleep", motor.render_sleep)
        motor._construir_ambiente(parametros.get("ambiente", {}))
        motor._construir_agentes(parametros.get("agentes", []))
        motor._construir_logger()

        return motor

    # --- listaAgentes(): Agente[] ---
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
            nome = cfg.get("nome", "agente")
            posicao_inicial = tuple(cfg.get("posicao_inicial", (0, 0)))

            if tipo == "farol":
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

                agente = AgenteForaging(nome)
            else:
                raise ValueError(f"Tipo de agente desconhecido: {tipo}")

            self.agentes.append(agente)

            if self.ambiente and hasattr(self.ambiente, "adicionaAgente"):
                self.ambiente.adicionaAgente(agente, posicao_inicial)

    def _construir_logger(self):
        from core.Logger import Logger

        self.logger = Logger()

    def _extrair_resultado(self, resultado):
        """
        Aceita vários formatos de retorno do ambiente.agir:
        - dict com chaves recompensa, terminou
        - tuplo/lista (recompensa, terminou)
        - número (só recompensa)
        - None (sem recompensa)
        """
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

    # --- executa() ---
    def executa(self):
        """
        Loop principal com episódios: observa, delibera, age, regista métricas
        e pára ao atingir condição de término ou max_passos.
        """
        for ep in range(1, self.episodios + 1):
            print(f"===== EPISÓDIO {ep} =====")
            self._reset_episodio()

            for _ in range(self.max_passos):
                self.passo_atual += 1
                terminou_episodio = False
                print(f"--- PASSO {self.passo_atual} ---")

                for agente in self.agentes:
                    obs = self.ambiente.observacaoPara(agente)
                    agente.observacao(obs)
                    accao = agente.age()

                    resultado = self.ambiente.agir(accao, agente)
                    recompensa, terminou = self._extrair_resultado(resultado)

                    nova_obs = self.ambiente.observacaoPara(agente)
                    agente.avaliacaoEstadoAtual(recompensa, nova_obs, terminou)

                    pos = self.ambiente.posicoes_agentes.get(agente)
                    self.recompensa_total += recompensa
                    self.historico_passos.append({
                        "episodio": ep,
                        "passo": self.passo_atual,
                        "agente": agente.nome,
                        "accao": accao.tipo,
                        "recompensa": recompensa,
                        "posicao": pos,
                    })

                    print(f"> {agente.nome} faz {accao.tipo}, recompensa {recompensa}, posição {pos}")
                    if terminou:
                        terminou_episodio = True

                # Atualização global do ambiente
                self.ambiente.atualizacao()

                # Render opcional (grelha em texto)
                if self.render and hasattr(self.ambiente, "render"):
                    self.ambiente.render()
                    if self.render_sleep > 0:
                        time.sleep(self.render_sleep)

                # Perguntar ao ambiente se há condição de término global
                if hasattr(self.ambiente, "terminou") and callable(self.ambiente.terminou):
                    if self.ambiente.terminou():
                        terminou_episodio = True

                if terminou_episodio:
                    print("Condição de término atingida pelo ambiente/ação.")
                    break

            if self.logger:
                self.logger.registar_episodio(ep, self.recompensa_total, self.passo_atual)
            self._guardar_politicas()

            print(f"Recompensa total do episódio {ep}: {self.recompensa_total}")
            print(f"Passos executados: {self.passo_atual}")

            # preparar próximo episódio
            self._reset_agentes()

        if self.logger:
            self.logger.guardar(self.ficheiro_metricas)

    def _reset_episodio(self):
        self.passo_atual = 0
        self.recompensa_total = 0.0
        self.historico_passos = []
        if hasattr(self.ambiente, "reset"):
            self.ambiente.reset()

    def _reset_agentes(self):
        for agente in self.agentes:
            if hasattr(agente, "reset"):
                agente.reset()

    def _guardar_politicas(self):
        for agente in self.agentes:
            if hasattr(agente, "guardar_politica") and callable(agente.guardar_politica):
                agente.guardar_politica()

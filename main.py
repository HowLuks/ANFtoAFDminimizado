import pprint

SIMBOLO_EPSILON = "&" 

class FuncaoTransicaoNFA:
    def __init__(self):
        self.mapa = {}

    def adicionar(self, origem, simbolo, destino):
        if origem not in self.mapa:
            self.mapa[origem] = {}
        
        if simbolo not in self.mapa[origem]:
            self.mapa[origem][simbolo] = set()
            
        self.mapa[origem][simbolo].add(destino)

    def obter(self, origem, simbolo):
        return self.mapa.get(origem, {}).get(simbolo, set())

    def __str__(self):
        linhas = []
        for origem, transicoes in self.mapa.items():
            for simbolo, destinos in transicoes.items():
                simb_str = "ε" if simbolo == SIMBOLO_EPSILON else simbolo
                linhas.append(f"  δ({origem}, {simb_str}) = {destinos}")
        return "\n".join(linhas)

class AutomatoFinitoNaoDeterministico:
    def __init__(self, Q, Alfabeto, Transicoes, q0, F, simbolo_epsilon=SIMBOLO_EPSILON):
        self.Q = set(Q)
        self.Alfabeto = set(Alfabeto)
        self.Transicoes = Transicoes
        self.q0 = q0
        self.F = set(F)
        self.simbolo_epsilon = simbolo_epsilon
        self._validar()

    def _validar(self):
        if not self.Q:
            raise ValueError("Q (conjunto de estados) não pode ser vazio.")
            
        if self.q0 not in self.Q:
            raise ValueError(f"q0 (estado inicial '{self.q0}') não pertence a Q.")
        
        if not self.F.issubset(self.Q):
            raise ValueError(f"F (estados finais {self.F}) não é um subconjunto de Q.")
        
        for origem, transicoes in self.Transicoes.mapa.items():
            if origem not in self.Q:
                raise ValueError(f"Estado de origem '{origem}' em Transicoes não pertence a Q.")
            
            for simbolo, destinos in transicoes.items():
                if simbolo not in self.Alfabeto and simbolo != self.simbolo_epsilon:
                    raise ValueError(f"Símbolo '{simbolo}' em Transicoes não pertence a Alfabeto nem é épsilon.")
                
                for destino in destinos:
                    if destino not in self.Q:
                         raise ValueError(f"Estado de destino '{destino}' em Transicoes não pertence a Q.")

    def _fecho_epsilon_estado(self, estado):
        fecho = {estado}
        pilha_visitar = [estado]
        
        while pilha_visitar:
            estado_atual = pilha_visitar.pop()
            destinos_epsilon = self.Transicoes.obter(estado_atual, self.simbolo_epsilon)
            
            for destino in destinos_epsilon:
                if destino not in fecho:
                    fecho.add(destino)
                    pilha_visitar.append(destino)
                    
        return fecho

    def fecho_epsilon_conjunto(self, conjunto_estados):
        fecho_total = set()
        for estado in conjunto_estados:
            fecho_total.update(self._fecho_epsilon_estado(estado))
        return fecho_total

    def __str__(self):
        return (
            f"M = (Q, Σ, δ, q0, F)\n"
            f"Q = {self.Q}\n"
            f"Σ = {self.Alfabeto}\n"
            f"q0 = {self.q0}\n"
            f"F = {self.F}\n"
            f"ε = '{self.simbolo_epsilon}'\n"
            f"δ = \n{self.Transicoes}"
        )
    

    def _gerar_nome_estado(self, conjunto_fs, mapa_estados, contador_estados):
        if conjunto_fs not in mapa_estados:
            novo_nome = f"Q{contador_estados['count']}"
            mapa_estados[conjunto_fs] = novo_nome
            contador_estados['count'] += 1
            return novo_nome
        
        return mapa_estados[conjunto_fs]

    def converter_para_afn_sem_epsilon(self):
        print("Iniciando conversão de AFNe para AFN (sem épsilon)...")
        
        novos_q = self.Q
        novo_alfabeto = self.Alfabeto
        novo_q0 = self.q0
        
        novos_f = set()
        for estado in self.Q:
            fecho_do_estado = self._fecho_epsilon_estado(estado)
            if not fecho_do_estado.isdisjoint(self.F):
                novos_f.add(estado)
                
        novas_transicoes = FuncaoTransicaoNFA()
        
        for estado_origem in self.Q:
            fecho_origem = self._fecho_epsilon_estado(estado_origem)
            
            for simbolo in self.Alfabeto:
                
                conjunto_movimento = set()
                for estado_intermediario in fecho_origem:
                    destinos = self.Transicoes.obter(estado_intermediario, simbolo)
                    conjunto_movimento.update(destinos)
                
                novos_destinos = self.fecho_epsilon_conjunto(conjunto_movimento)
                
                if novos_destinos:
                    for destino_final in novos_destinos:
                        novas_transicoes.adicionar(estado_origem, simbolo, destino_final)

        print("Conversão para AFN (sem épsilon) concluída.")

        return AutomatoFinitoNaoDeterministico(
            Q=novos_q,
            Alfabeto=novo_alfabeto,
            Transicoes=novas_transicoes,
            q0=novo_q0,
            F=novos_f
        )

    def possui_transicoes_epsilon(self):
        for origem, transicoes in self.Transicoes.mapa.items():
            if self.simbolo_epsilon in transicoes:
                return True
        
        return False

    def converter_afn_para_afd(self):
        print("Iniciando conversão de AFN para AFD...")

        novos_estados_q = set()
        novos_estados_finais = set()
        novas_transicoes = FuncaoTransicaoDFA()
        
        mapa_estados = {}
        contador_estados = {'count': 0} 
        
        fila_processamento = []
        estados_processados = set()

        q0_conjunto = {self.q0}
        q0_fs = frozenset(q0_conjunto)
        
        q0_nome_afd = self._gerar_nome_estado(q0_fs, mapa_estados, contador_estados)
        
        novos_estados_q.add(q0_nome_afd)
        fila_processamento.append(q0_fs)
        estados_processados.add(q0_fs)

        if not q0_conjunto.isdisjoint(self.F):
            novos_estados_finais.add(q0_nome_afd)
            
        nome_estado_erro = "Q_ERRO"
        precisa_estado_erro = False

        while fila_processamento:
            super_estado_atual_fs = fila_processamento.pop(0)
            nome_estado_atual = mapa_estados[super_estado_atual_fs]
            
            for simbolo in self.Alfabeto:
                
                proximo_super_estado = set()
                for estado_nfa in super_estado_atual_fs:
                    proximo_super_estado.update(self.Transicoes.obter(estado_nfa, simbolo))
                
                proximo_super_estado_fs = frozenset(proximo_super_estado)
                
                nome_destino = ""

                if not proximo_super_estado_fs:
                    nome_destino = nome_estado_erro
                    precisa_estado_erro = True
                else:
                    nome_destino = self._gerar_nome_estado(
                        proximo_super_estado_fs, 
                        mapa_estados, 
                        contador_estados
                    )
                    
                    if proximo_super_estado_fs not in estados_processados:
                        novos_estados_q.add(nome_destino)
                        
                        if not proximo_super_estado.isdisjoint(self.F):
                            novos_estados_finais.add(nome_destino)
                        
                        fila_processamento.append(proximo_super_estado_fs)
                        estados_processados.add(proximo_super_estado_fs)

                novas_transicoes.adicionar(nome_estado_atual, simbolo, nome_destino)

        if precisa_estado_erro:
            novos_estados_q.add(nome_estado_erro)
            for simbolo in self.Alfabeto:
                novas_transicoes.adicionar(nome_estado_erro, simbolo, nome_estado_erro)
        
        print("Conversão de AFN para AFD concluída.")
        
        return AutomatoFinitoDeterministico(
            Q=novos_estados_q,
            Alfabeto=self.Alfabeto,
            Transicoes=novas_transicoes,
            q0=q0_nome_afd,
            F=novos_estados_finais
        )

class FuncaoTransicaoDFA:
    def __init__(self):
        self.mapa = {}

    def adicionar(self, origem, simbolo, destino):
        if origem not in self.mapa:
            self.mapa[origem] = {}
        self.mapa[origem][simbolo] = destino

    def obter(self, origem, simbolo):
        return self.mapa.get(origem, {}).get(simbolo)

    def __str__(self):
        linhas = []
        for origem, transicoes in self.mapa.items():
            for simbolo, destino in transicoes.items():
                linhas.append(f"  δ({origem}, {simbolo}) = {destino}")
        return "\n".join(linhas)
    
class AutomatoFinitoDeterministico:
    def __init__(self, Q, Alfabeto, Transicoes, q0, F):
        self.Q = set(Q)
        self.Alfabeto = set(Alfabeto)
        self.Transicoes = Transicoes
        self.q0 = q0
        self.F = set(F)
        self._validar()

    def _validar(self):
        if not self.Q:
            raise ValueError("Q (conjunto de estados) não pode ser vazio.")
        if self.q0 not in self.Q:
            raise ValueError(f"q0 (estado inicial '{self.q0}') não pertence a Q.")
        if not self.F.issubset(self.Q):
            raise ValueError(f"F (estados finais {self.F}) não é um subconjunto de Q.")
        
        for estado in self.Q:
            if estado not in self.Transicoes.mapa:
                raise ValueError(f"Função delta incompleta: Estado '{estado}' não possui transições.")
            
            for simbolo in self.Alfabeto:
                if simbolo not in self.Transicoes.mapa[estado]:
                    raise ValueError(f"Função delta incompleta: Estado '{estado}' não tem transição para o símbolo '{simbolo}'.")
                
                destino = self.Transicoes.mapa[estado][simbolo]
                if destino not in self.Q:
                    raise ValueError(f"Estado de destino '{destino}' (de δ({estado},{simbolo})) não pertence a Q.")
                

    def processar_cadeia(self, cadeia):
        estado_atual = self.q0
        for simbolo in cadeia:
            if simbolo not in self.Alfabeto:
                print(f"Símbolo '{simbolo}' não pertence ao alfabeto {self.Alfabeto}.")
                return False
            
            estado_atual = self.Transicoes.obter(estado_atual, simbolo)
            
            if estado_atual is None:
                return False
        
        return estado_atual in self.F

    def __str__(self):
        return (
            f"M = (Q, Σ, δ, q0, F)\n"
            f"Q = {self.Q}\n"
            f"Σ = {self.Alfabeto}\n"
            f"q0 = {self.q0}\n"
            f"F = {self.F}\n"
            f"δ = \n{self.Transicoes}"
        )

    def _remover_estados_inalcancaveis(self):
        estados_alcancados = {self.q0}
        fila_processamento = [self.q0]
        
        while fila_processamento:
            estado_atual = fila_processamento.pop(0)
            
            for simbolo in self.Alfabeto:
                estado_destino = self.Transicoes.obter(estado_atual, simbolo)
                
                if estado_destino not in estados_alcancados:
                    estados_alcancados.add(estado_destino)
                    fila_processamento.append(estado_destino)
        
        if estados_alcancados == self.Q:
            print("... (Minimização) Todos os estados são alcançáveis.")
            return self

        print(f"... (Minimização) Removendo estados inalcançáveis: {self.Q - estados_alcancados}")
        
        novo_Q = estados_alcancados
        novo_F = self.F.intersection(estados_alcancados)
        novo_q0 = self.q0
        novas_Transicoes = FuncaoTransicaoDFA()
        
        for estado_origem in novo_Q:
            for simbolo in self.Alfabeto:
                estado_destino = self.Transicoes.obter(estado_origem, simbolo)
                novas_Transicoes.adicionar(estado_origem, simbolo, estado_destino)
                
        return AutomatoFinitoDeterministico(
            Q=novo_Q,
            Alfabeto=self.Alfabeto,
            Transicoes=novas_Transicoes,
            q0=novo_q0,
            F=novo_F
        )

    def minimizar(self):
        print("Iniciando minimização do AFD...")
        
        afd = self._remover_estados_inalcancaveis()
        
        if len(afd.Q) <= 1:
            print(">>> AFD já é trivialmente mínimo.")
            return afd

        marked_pairs = {}
        states_list = sorted(list(afd.Q)) 
        pares_a_processar = []
        
        for i in range(len(states_list)):
            p = states_list[i]
            for j in range(i + 1, len(states_list)):
                q = states_list[j]
                par = (p, q)
                pares_a_processar.append(par)
                
                e_final_p = p in afd.F
                e_final_q = q in afd.F
                
                if e_final_p != e_final_q:
                    marked_pairs[par] = True
                else:
                    marked_pairs[par] = False

        houve_marcacao = True
        while houve_marcacao:
            houve_marcacao = False
            
            for (p, q) in pares_a_processar:
                if marked_pairs[(p, q)]:
                    continue
                
                for simbolo in afd.Alfabeto:
                    p_destino = afd.Transicoes.obter(p, simbolo)
                    q_destino = afd.Transicoes.obter(q, simbolo)
                    
                    if p_destino == q_destino:
                        continue
                    
                    if p_destino < q_destino:
                        par_destino = (p_destino, q_destino)
                    else:
                        par_destino = (q_destino, p_destino)
                    
                    if marked_pairs.get(par_destino, False):
                        marked_pairs[(p, q)] = True
                        houve_marcacao = True
                        break 

        grupos_equivalentes = []
        estados_processados = set()
        
        for estado_p in states_list:
            if estado_p in estados_processados:
                continue
            novo_grupo = {estado_p}
            estados_processados.add(estado_p)
            
            for estado_q in states_list:
                if estado_q in estados_processados:
                    continue
                
                if estado_p < estado_q:
                    par = (estado_p, estado_q)
                else:
                    par = (estado_q, estado_p)
                
                if not marked_pairs[par]:
                    novo_grupo.add(estado_q)
                    estados_processados.add(estado_q)
            
            grupos_equivalentes.append(novo_grupo)

        print(f"Novos grupos de estados equivalentes: {grupos_equivalentes}")

        if len(grupos_equivalentes) == len(afd.Q):
            print(">>> O AFD já é mínimo. Nenhum estado foi agrupado.")
            print("Minimização concluída. Nenhum estado foi alterado.")
            return afd

        mapa_novo_estado = {}
        mapa_nome_grupo = {}
        novo_Q = set()
        novo_F = set()
        novo_q0 = None
        
        for i, grupo in enumerate(grupos_equivalentes):
            nome_grupo = f"M{i}"
            novo_Q.add(nome_grupo)
            mapa_nome_grupo[frozenset(grupo)] = nome_grupo
            
            e_grupo_final = False
            e_grupo_inicial = False
            
            for estado_antigo in grupo:
                mapa_novo_estado[estado_antigo] = nome_grupo
                if estado_antigo in afd.F:
                    e_grupo_final = True
                if estado_antigo == afd.q0:
                    e_grupo_inicial = True
            
            if e_grupo_final:
                novo_F.add(nome_grupo)
            if e_grupo_inicial:
                novo_q0 = nome_grupo
                
        novas_Transicoes_min = FuncaoTransicaoDFA()
        
        for grupo in grupos_equivalentes:
            nome_origem = mapa_nome_grupo[frozenset(grupo)]
            representante = next(iter(grupo))
            
            for simbolo in afd.Alfabeto:
                destino_antigo = afd.Transicoes.obter(representante, simbolo)
                nome_destino = mapa_novo_estado[destino_antigo]
                novas_Transicoes_min.adicionar(nome_origem, simbolo, nome_destino)

        print(f"Minimização concluída. Estados reduzidos de {len(self.Q)} para {len(novo_Q)}.")
        
        return AutomatoFinitoDeterministico(
            Q=novo_Q,
            Alfabeto=afd.Alfabeto,
            Transicoes=novas_Transicoes_min,
            q0=novo_q0,
            F=novo_F
        )
    

def carregar_automato(caminho_arquivo):
    estados = set()
    alfabeto = set()
    estado_inicial = None
    estados_finais = set()
    
    transicoes_nfa = FuncaoTransicaoNFA()
    e_nao_deterministico = False
    tem_epsilon = False
    
    mapa_checa_determinismo = {}

    modo_atual = None
    
    print(f"Lendo arquivo de autômato de: {caminho_arquivo}")
    
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            for linha in f:
                linha = linha.strip()
                
                if not linha or linha.startswith('#'):
                    continue
                
                if linha.startswith('[') and linha.endswith(']'):
                    modo_atual = linha
                    continue
                
                if modo_atual == '[ESTADOS]':
                    estados.add(linha)
                
                elif modo_atual == '[ALFABETO]':
                    alfabeto.add(linha)
                    
                elif modo_atual == '[INICIAL]':
                    if estado_inicial:
                        raise ValueError("Erro: Múltiplos estados iniciais definidos.")
                    estado_inicial = linha
                    
                elif modo_atual == '[FINAIS]':
                    estados_finais.add(linha)
                    
                elif modo_atual == '[TRANSICOES]':
                    partes = linha.split()
                    if len(partes) != 3:
                        raise ValueError(f"Formato de transição inválido: '{linha}'")
                    
                    origem, simbolo, destino = partes
                    
                    transicoes_nfa.adicionar(origem, simbolo, destino)
                    
                    if simbolo == SIMBOLO_EPSILON:
                        tem_epsilon = True
                    else:
                        alfabeto.add(simbolo) 
                    
                    chave_transicao = (origem, simbolo)
                    if chave_transicao in mapa_checa_determinismo:
                        e_nao_deterministico = True
                    mapa_checa_determinismo[chave_transicao] = destino

    except FileNotFoundError:
        print(f"Erro: Arquivo não encontrado em '{caminho_arquivo}'")
        return None
    except Exception as e:
        print(f"Erro ao processar o arquivo: {e}")
        return None

    if not estado_inicial:
        raise ValueError("Erro: Nenhum estado inicial definido.")
    estados.update(estados_finais)
    estados.add(estado_inicial)
    
    if tem_epsilon or e_nao_deterministico:
        print(">>> Autômato detectado como AFN ou AFNe.")
        return AutomatoFinitoNaoDeterministico(
            Q=estados,
            Alfabeto=alfabeto,
            Transicoes=transicoes_nfa,
            q0=estado_inicial,
            F=estados_finais
        )
    
    else:
        print(">>> Autômato detectado como AFD.")
        transicoes_dfa = FuncaoTransicaoDFA()
        for origem, transicoes in transicoes_nfa.mapa.items():
            for simbolo, destinos in transicoes.items():
                destino_unico = list(destinos)[0]
                transicoes_dfa.adicionar(origem, simbolo, destino_unico)
                
        return AutomatoFinitoDeterministico(
            Q=estados,
            Alfabeto=alfabeto,
            Transicoes=transicoes_dfa,
            q0=estado_inicial,
            F=estados_finais
        )

def processar_automato_completo(automato_entrada):
    print("=============================================")
    print("=== INICIANDO PROCESSAMENTO DO AUTÔMATO ===")
    print("=============================================\n")

    afd_para_minimizar = None

    if isinstance(automato_entrada, AutomatoFinitoDeterministico):
        print(">>> TIPO DETECTADO: AFD (Autômato Finito Determinístico).")
        print(">>> O autômato já é determinístico. Pulando para minimização.")
        afd_para_minimizar = automato_entrada

    elif isinstance(automato_entrada, AutomatoFinitoNaoDeterministico):
        
        automato_afn = None
        
        if automato_entrada.possui_transicoes_epsilon():
            print(">>> TIPO DETECTADO: AFNe (Contém transições épsilon).")
            
            print("\n--- ETAPA 1: Convertendo AFNe para AFN (sem épsilon) ---")
            automato_afn = automato_entrada.converter_para_afn_sem_epsilon()
            
        else:
            print(">>> TIPO DETECTADO: AFN (Sem transições épsilon).")
            automato_afn = automato_entrada
        
        print("\n--- ETAPA 2: Convertendo AFN para AFD ---")
        afd_para_minimizar = automato_afn.converter_afn_para_afd()
        print("--- AFD Intermediário Gerado ---")
        print(afd_para_minimizar)

    else:
        print(f"TIPO DESCONHECIDO: O objeto fornecido não é um autômato válido.")
        return None

    if afd_para_minimizar:
        print("\n--- ETAPA 3: Minimizando o AFD ---")
        automato_minimizado = afd_para_minimizar.minimizar()
        
        print("\n=============================================")
        print("=== PROCESSAMENTO CONCLUÍDO ===")
        print("=============================================\n")
        print("--- AFD MÍNIMO FINAL ---")
        print(automato_minimizado)
        return automato_minimizado
    
    return None


try:
    meu_automato = carregar_automato("entrada.txt") 
    
    if meu_automato:
        afd_minimo_final = processar_automato_completo(meu_automato)

except Exception as e:
    print(f"\n--- Ocorreu um erro geral: {e} ---")
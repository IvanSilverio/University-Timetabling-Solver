# main.py
import pandas as pd
import networkx as nx
import sys
import random
import os
from collections import defaultdict
import time 

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 
ARQUIVO_DADOS = os.path.join(BASE_DIR, "dataset_processado.csv")



# Aumentamos o limite padrão de recursão para evitar erros de 'RecursionError' durante a execução de DFS.
sys.setrecursionlimit(10000)


# Definição de slots por cada curso (SIN e CCO)

SLOTS_CCO = ['M3_M4', 'M1_M2', 'T1_T2', 'T3_T4'] 
SLOTS_SIN = ['N1_N2', 'N3_N4', 'N3_N4_N5'] 

DIAS = ['SEG', 'TER', 'QUA', 'QUI', 'SEX']
SLOTS_TEMPO = []

# Gera a linha do tempo linear, para o algoritmo de backtracking, que tentará
# preencher um slot por vez. 

max_len = max(len(SLOTS_CCO), len(SLOTS_SIN))
for i in range(max_len):
    s_cco = SLOTS_CCO[i] if i < len(SLOTS_CCO) else ''
    s_sin = SLOTS_SIN[i] if i < len(SLOTS_SIN) else ''
    for dia in DIAS:
        if s_cco or s_sin:
            SLOTS_TEMPO.append((dia, s_cco, s_sin))



#Funcão identifica matérias optativas e atribui 'Trilhas' (1 ou 2) para permitir paralelismo.
def processar_trilhas_optativas(df):
    
    
 
    df['Tipo_Real'] = df['Nome'].apply(lambda x: 'OP' if '_OP_' in x else 'OB')
    df['Trilha'] = None 

    grupos = df[df['Tipo_Real'] == 'OP'].groupby(['Curso', 'Periodo'])

    for (curso, periodo), grupo in grupos:
        # Aplica trilhas apenas para períodos avançados (>= 5), onde optativas são mais comuns
        if int(periodo) >= 5:
            disciplinas_unicas = grupo['ID_Disciplina'].unique()
            # Mapa simples: Disciplina A -> Trilha 1, Disciplina B -> Trilha 2, etc.
            mapa_trilha = {disc: (i % 2) + 1 for i, disc in enumerate(disciplinas_unicas)}
            for idx, row in grupo.iterrows():
                df.at[idx, 'Trilha'] = mapa_trilha[row['ID_Disciplina']]
                
    print("Trilhas de optativas processadas com sucesso.")
    return df


# Funcao gera preferências simuladas para professores, usamos uma função baseada no hash do nome para 
# garantir reprodutibilidade , enquanto simulamos diversidade de horários (manhã/tarde vs noite).
def gerar_preferencias_ficticias(df):
    
    
    profs = df['Professor'].unique()
    prefs = {}
    for p in profs:
        if 'CCO' in p:
            # Simula professores com preferência por turnos específicos (Manhã vs Tarde)
            if hash(p) % 2 == 0: 
                prefs[p] = {'preferir': [f"{d}_M2_M3" for d in DIAS], 'evitar': [f"{d}_T3_T4" for d in DIAS]}
            else: 
                prefs[p] = {'preferir': [f"{d}_T3_T4" for d in DIAS], 'evitar': [f"{d}_M1_M2" for d in DIAS]}
        else:
            # Preferências Noturnas para cursos noturnos (SIN)
            prefs[p] = {'preferir': [f"{d}_N1_N2" for d in DIAS], 'evitar': [f"SEX_N3_N4", f"SEX_N3_N4_N5"]}
    return prefs

def carregar_dados():
    try: 
        df = pd.read_csv(ARQUIVO_DADOS)
        df = processar_trilhas_optativas(df)
        return df
    except Exception as e: 
        print(f"Erro ao carregar dados: {e}")
        return None


#A função constrói o grafo:
#   vértices são aulas/disciplinas.
#   Arestas representam incompatibilidades, seja por professor, turma ou lab.

#Depois da construção, implementa a lógica de restrições "Hard" do problema.
#Se existe uma aresta entre A e B, A e B nunca terão o mesmo horário na solução final.
def construir_grafos_multicamadas(df):
    
    
    print("Construindo Grafo Multicamadas (Turma + Prof + Recurso)...")
    G = nx.Graph()
    
    #adiciona cada aula como um vértice no grafo
    for _, row in df.iterrows():
        G.add_node(row['ID_Aula'], **row.to_dict())
    
    nodes = list(G.nodes(data=True))
    turmas = defaultdict(list)
    # Agrupa aulas por Turma (Curso + Período) para otimizar a verificação de conflitos de grade
    for nid, data in nodes:
        turmas[(data['Curso'], data['Periodo'])].append((nid, data))
    
    # CAMADA 1: CONFLITOS DE TURMA
    # Aulas do mesmo período do mesmo curso não podem colidir, pois os alunos devem assistir ambas.
    for lista in turmas.values():
        for i in range(len(lista)):
            u, data_u = lista[i]
            for j in range(i+1, len(lista)):
                v, data_v = lista[j]
                
                eh_conflito = True 
                
                tipo_u = data_u.get('Tipo_Real', 'OB')
                tipo_v = data_v.get('Tipo_Real', 'OB')
                trilha_u = data_u.get('Trilha')
                trilha_v = data_v.get('Trilha')
                
                # Aqui temos a exceção das optativas de trilhas diferentes que permite paralelismo.
                # se ambas forem optativas e estiverem em trilhas distintas, não tem conflito.
                if tipo_u == 'OP' and tipo_v == 'OP':
                    if trilha_u is not None and trilha_v is not None:
                        if trilha_u != trilha_v:
                            eh_conflito = False 

                if eh_conflito:
                    G.add_edge(u, v, tipo='Turma')

    #CAMADAS 2, 3: PROFESSOR E RECURSOS
    for i in range(len(nodes)):
        u, data_u = nodes[i]
        for j in range(i + 1, len(nodes)):
            v, data_v = nodes[j]
            
            #se já existe conflito de turma, não precisa verificar.)
            if G.has_edge(u, v): continue
            
            # Só verifica conflitos entre cursos. (SIN vs SIN, CCO vs CCO)
            eh_sin_u = 'SIN' in str(data_u['Curso'])
            eh_sin_v = 'SIN' in str(data_v['Curso'])
            
            if eh_sin_u == eh_sin_v:
                #conflito em que o mesmo professor não pode dar duas aulas ao mesmo tempo
                if data_u['Professor'] == data_v['Professor']:
                    G.add_edge(u, v, tipo='Professor')
                
                #conflito em que o mesmo lab não pode ser usado por 2 cursos ao mesmo tempo
                if pd.notna(data_u['Lab_Requerido']) and pd.notna(data_v['Lab_Requerido']):
                    if data_u['Lab_Requerido'] == data_v['Lab_Requerido']:
                        G.add_edge(u, v, tipo='Recurso_Fisico')


    print(f"Grafo construído: {len(G.nodes)} nós, {len(G.edges)} arestas de conflito.")
    
    #Retorna tanto o grafo de conflitos (G) quanto seu complemento (G_comp).
    # O grafo complemento é usado para buscar Cliques, ou seja,
    # um grupo de aulas que podem ser agendadas no mesmo horário.
    return G, nx.complement(G)


#Classe responsável por encontrar uma alocação válida de horários para as aulas.
#Utiliza uma abordagem baseada em Coloração de Grafos/Clique Maximal combinada junto Backtracking.


class SolucionadorTimetabling:
   
    def __init__(self, G_comp, df, prefs):
        self.G_comp = G_comp  # grafo complemento
        self.mapa = df.set_index('ID_Aula').to_dict('index') #acesso dados da aula
        self.prefs = prefs #preferências
        self.grade = {} # solução parcial ou final
        
        # auxiliares para validação rápida de carga horaria de prof e total de aulas
        self.carga_prof = defaultdict(lambda: defaultdict(int)) # carga horária diária do professor
        self.total_aulas_prof = df['Professor'].value_counts().to_dict() # prioridade
        
    def calcular_pontuacao_global(self):
        score = 0
        for id_aula, horario in self.grade.items():
            prof = self.mapa[id_aula]['Professor']
            prefs_prof = self.prefs.get(prof, {})
            
            if horario in prefs_prof.get('preferir', []): score += 10
            elif horario in prefs_prof.get('evitar', []): score -= 10
        return score

    def slots_overlap(self, s1, s2):
        d1, h1 = s1.split('_', 1)
        d2, h2 = s2.split('_', 1)
        if d1 != d2: return False
        set1 = set(h1.split('_'))
        set2 = set(h2.split('_'))
        return not set1.isdisjoint(set2)

    
    
    
       
    #Funcao que encontra um conjunto de aulas (clique) que podem ser agendadas simultaneamente
        
    #Filtra candidatos válidos.
    #Ordena por uma 'pontuação'/heuristica (preferência do professor + carga).
    #Constrói o clique de forma gulosa, adicionando a aula se ela for compatível com todas já adicionadas.
        
    def encontrar_clique_maximal(self, candidatos, dia, slot_nome):
        candidatos_lista = list(candidatos)
        # shuffle coloca aleatoriedade para explorar diferentes ramos da árvore de soluções em execuções distintas
        random.shuffle(candidatos_lista)
        
        def pontuacao(nid):
            # Prioriza aulas de professores que PREFEREM este horário
            # e professores com muitas aulas, pois são mais dificeis de alocar.
            prof = self.mapa[nid]['Professor']
            p = self.prefs.get(prof, {})
            score = 10
            if slot_nome in p.get('preferir', []): score = 100
            if slot_nome in p.get('evitar', []): score = 0
            carga = self.total_aulas_prof.get(prof, 0)
            return score + (carga * 0.5)

        fila = sorted(candidatos_lista, key=pontuacao, reverse=True)
        
        clique = []
        for node in fila:
            prof = self.mapa[node]['Professor']
            duracao = self.mapa[node]['CH_Aula'] 
            
            #Restrição Hard, professor não pode exceder 8 horas de aula no mesmo dia
            if self.carga_prof[prof][dia] + duracao > 8: continue
            
            # Checa compatibilidade com o Clique atual
            # Se vértice não é vizinho de 'membro' no grafo complemento, eles conflitam no grafo original.
            compativel = True
            for membro in clique:
                if not self.G_comp.has_edge(node, membro):
                    compativel = False; break
            if not compativel: continue
            
            # Validacoes cruzadas
            # Um problema como uma aula de 3h (N3_N4_N5) conflita com uma de 2h (N3_N4) mesmo não sendo o mesmo slot exato.
            # Precisa ser verificado manualmente contra a grade já alocada.
            
            nome_mat = self.mapa[node]['ID_Disciplina']
            curso_node = self.mapa[node]['Curso']
            periodo_node = self.mapa[node]['Periodo']
            tipo_node = self.mapa[node].get('Tipo_Real', 'OB')
            trilha_node = self.mapa[node].get('Trilha')

            for alocada, h in self.grade.items():
                #se houver sobreposição de tempo entre o slot atual e o da aula já alocada
                if self.slots_overlap(h, slot_nome):
                    #O mesmo professor não pode estar em dois slots sobrepostos
                    if self.mapa[alocada]['Professor'] == prof:
                        compativel = False; break
                    
                    #Evita que a mesma matéria (Turma A e B) ocorra no mesmo dia
                    if self.mapa[alocada]['ID_Disciplina'] == nome_mat:
                         if h.split('_')[0] == dia: # Mesmo dia
                            compativel = False; break

                    # Verifica conflito de grade para os alunos
                    if self.mapa[alocada]['Curso'] == curso_node and \
                       self.mapa[alocada]['Periodo'] == periodo_node:
                        
                        tipo_alocada = self.mapa[alocada].get('Tipo_Real', 'OB')
                        trilha_alocada = self.mapa[alocada].get('Trilha')
                        
                        eh_conflito_turma = True
                        
                        #lógica de trilhas optativas para validação cruzada
                        if tipo_node == 'OP' and tipo_alocada == 'OP':
                            if trilha_node is not None and trilha_alocada is not None:
                                if trilha_node != trilha_alocada:
                                    eh_conflito_turma = False
                        
                        if eh_conflito_turma:
                            compativel = False; break

            if compativel: clique.append(node)
            
        return clique


    #DFS para alocar aulas nos slots de tempo.
    #Parametros:
        #idx: Índice do slot de tempo atual sendo considerado.
        #restantes: Conjunto de iDs de aulas que ainda precisam ser alocadas.


    def dfs_slots(self, idx, restantes):
        

        
        
        
        #Caso base, se não há mais aulas para alocar
        if not restantes: return True
        #Caso base, se acabaram os slots de tempo e ainda há aulas, falha (backtrack).
        if idx >= len(SLOTS_TEMPO): return False

        dia, s_cco, s_sin = SLOTS_TEMPO[idx]
        
        # Filtra quais aulas do conjunto restantes podem ocorrer neste slot
        # baseado na duração e no tipo de curso, CCO ou SIN.
        validos = []
        duracao_sin = 3 if 'N5' in s_sin else (2 if s_sin else 0)
        duracao_cco = 2 if s_cco else 0

        for n in restantes:
            eh_sin = 'SIN' in str(self.mapa[n]['Curso'])
            ch_aula = self.mapa[n]['CH_Aula']
            
            if eh_sin:
                if s_sin == '' or ch_aula != duracao_sin: continue
            else:
                if s_cco == '' or ch_aula != duracao_cco: continue 
            validos.append(n)

        #Se nenhuma aula serve para este slot, vai para o próximo slot
        if not validos:
            return self.dfs_slots(idx + 1, restantes)

        slot_real = f"{dia}_{s_sin if s_sin else s_cco}"
        
        #Tenta encontrar o maior grupo de aulas possível para colocar neste slot
        clique = self.encontrar_clique_maximal(validos, dia, slot_real)
        
        #Se não conseguiu colocar nada, avança
        if not clique:
             return self.dfs_slots(idx + 1, restantes)

        #Decide um clique
        for n in clique:
            eh_sin = 'SIN' in str(self.mapa[n]['Curso'])
            self.grade[n] = f"{dia}_{s_sin}" if eh_sin else f"{dia}_{s_cco}"
            self.carga_prof[self.mapa[n]['Professor']][dia] += self.mapa[n]['CH_Aula']
        
        
        #Recursão tenta resolver o restante do problema com as aulas alocadas
        if self.dfs_slots(idx + 1, restantes - set(clique)):
            return True

        #Desfaz a decisão, ou seja, Se a recursão falhou, desfaz as alocações deste passo e tenta outro caminho.
        #Obs: Esta código é um híbrido Guloso/DFS. Ela é gulosa na escolha do clique por slot.
        for n in clique:
            del self.grade[n]
            self.carga_prof[self.mapa[n]['Professor']][dia] -= self.mapa[n]['CH_Aula']
            
        return False

def executar():
    df = carregar_dados()
    if df is None: return
    
    prefs = gerar_preferencias_ficticias(df)
    G, G_comp = construir_grafos_multicamadas(df)
    
    #Ordenacao dos slots:
    # Para maximizar a satisfação dos professores, tentamos preencher primeiro os slots, que são mais populares.
    # Isso aumenta a chance de um professor conseguir seu horário preferido antes que ele seja ocupado.
    def calcular_popularidade_slot(slot_tuple):
        dia, s_cco, s_sin = slot_tuple
        slot_real = f"{dia}_{s_sin if s_sin else s_cco}"
        
        popularidade = 0
        for prof, p_data in prefs.items():
            if slot_real in p_data.get('preferir', []):
                popularidade += 1
        return popularidade

    #Ordena SLOTS_TEMPO. Os Slots com mais populares aparecem primeiro na lista
    SLOTS_TEMPO.sort(key=calcular_popularidade_slot, reverse=True)
    
    TEMPO_LIMITE_SEGUNDOS = 15
    inicio = time.time()
    
    melhor_grade = None
    melhor_score = -float('inf')
    solucoes_encontradas = 0
    tentativas = 0
    
    print(f"Iniciando Otimização por {TEMPO_LIMITE_SEGUNDOS} segundos...")
    
  
    #Como o algoritmo tem componentes aleatórios (shuffle nos candidatos),
    # rodamos várias vezes dentro do tempo limite para tentar encontrar a melhor solução.
    while (time.time() - inicio) < TEMPO_LIMITE_SEGUNDOS:
        tentativas += 1
        solver = SolucionadorTimetabling(G_comp, df, prefs)
        sucesso = solver.dfs_slots(0, set(G_comp.nodes))
        
        if sucesso:
            solucoes_encontradas += 1
            score_atual = solver.calcular_pontuacao_global()
            tempo_decorrido = time.time() - inicio
            print(f"[T+{tempo_decorrido:.1f}s] Solução #{solucoes_encontradas} encontrada. Score: {score_atual}")
            
            if score_atual > melhor_score:
                melhor_score = score_atual
                melhor_grade = solver.grade.copy()
                print(f"   >>> NOVA MELHOR GRADE! (Score: {melhor_score})")
        
    print("\n" + "="*40)
    print(f"FIM. Soluções: {solucoes_encontradas}. Melhor Score: {melhor_score}")
    
    if melhor_grade:
        caminho_saida = os.path.join(BASE_DIR, "grade_final.csv")
        pd.DataFrame(list(melhor_grade.items()), columns=['Aula', 'Horario']).to_csv(caminho_saida, index=False)
        print(f"Melhor grade salva em '{caminho_saida}'.")
    else:
        print("FALHA: Nenhuma solução encontrada.")

if __name__ == "__main__":
    executar()
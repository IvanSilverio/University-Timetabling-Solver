# main.py
import pandas as pd
import networkx as nx
import sys
import random
import os
from collections import defaultdict
import time 

# Aumenta limite de recursão para o DFS
sys.setrecursionlimit(10000)

# --- CONFIGURAÇÕES ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 
ARQUIVO_DADOS = os.path.join(BASE_DIR, "dataset_processado.csv")

# --- DEFINIÇÃO DE SLOTES ---
# Voltamos ao padrão original: Todos os dias podem ter qualquer slot
SLOTS_CCO = ['M3_M4', 'M1_M2', 'T1_T2', 'T3_T4'] 
SLOTS_SIN = ['N1_N2', 'N3_N4', 'N3_N4_N5'] 

DIAS = ['SEG', 'TER', 'QUA', 'QUI', 'SEX']
SLOTS_TEMPO = []

# Gera a linha do tempo linear
max_len = max(len(SLOTS_CCO), len(SLOTS_SIN))
for i in range(max_len):
    s_cco = SLOTS_CCO[i] if i < len(SLOTS_CCO) else ''
    s_sin = SLOTS_SIN[i] if i < len(SLOTS_SIN) else ''
    for dia in DIAS:
        if s_cco or s_sin:
            SLOTS_TEMPO.append((dia, s_cco, s_sin))

# --- FUNÇÕES AUXILIARES ---

def processar_trilhas_optativas(df):
    """
    Identifica matérias optativas e atribui 'Trilhas' (1 ou 2) para permitir paralelismo.
    """
    df['Tipo_Real'] = df['Nome'].apply(lambda x: 'OP' if '_OP_' in x else 'OB')
    df['Trilha'] = None 

    grupos = df[df['Tipo_Real'] == 'OP'].groupby(['Curso', 'Periodo'])

    for (curso, periodo), grupo in grupos:
        if int(periodo) >= 5:
            disciplinas_unicas = grupo['ID_Disciplina'].unique()
            mapa_trilha = {disc: (i % 2) + 1 for i, disc in enumerate(disciplinas_unicas)}
            for idx, row in grupo.iterrows():
                df.at[idx, 'Trilha'] = mapa_trilha[row['ID_Disciplina']]
                
    print("Trilhas de optativas processadas com sucesso.")
    return df

def gerar_preferencias_ficticias(df):
    profs = df['Professor'].unique()
    prefs = {}
    for p in profs:
        if 'CCO' in p:
            if hash(p) % 2 == 0: 
                prefs[p] = {'preferir': [f"{d}_M2_M3" for d in DIAS], 'evitar': [f"{d}_T3_T4" for d in DIAS]}
            else: 
                prefs[p] = {'preferir': [f"{d}_T3_T4" for d in DIAS], 'evitar': [f"{d}_M1_M2" for d in DIAS]}
        else:
            # Preferências Noturnas
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

def construir_grafos_multicamadas(df):
    print("Construindo Grafo Multicamadas (Turma + Prof + Recurso)...")
    G = nx.Graph()
    
    for _, row in df.iterrows():
        G.add_node(row['ID_Aula'], **row.to_dict())
    
    nodes = list(G.nodes(data=True))
    turmas = defaultdict(list)
    for nid, data in nodes:
        turmas[(data['Curso'], data['Periodo'])].append((nid, data))
    
    # --- CAMADA 1: TURMA (COM TRILHAS) ---
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
                
                # Permite paralelismo apenas entre Optativas de trilhas diferentes
                if tipo_u == 'OP' and tipo_v == 'OP':
                    if trilha_u is not None and trilha_v is not None:
                        if trilha_u != trilha_v:
                            eh_conflito = False 

                if eh_conflito:
                    G.add_edge(u, v, tipo='Turma')

    # --- CAMADAS GERAIS ---
    for i in range(len(nodes)):
        u, data_u = nodes[i]
        for j in range(i + 1, len(nodes)):
            v, data_v = nodes[j]
            
            if G.has_edge(u, v): continue
            
            eh_sin_u = 'SIN' in str(data_u['Curso'])
            eh_sin_v = 'SIN' in str(data_v['Curso'])
            
            if eh_sin_u == eh_sin_v:
                if data_u['Professor'] == data_v['Professor']:
                    G.add_edge(u, v, tipo='Professor')
                
                if pd.notna(data_u['Lab_Requerido']) and pd.notna(data_v['Lab_Requerido']):
                    if data_u['Lab_Requerido'] == data_v['Lab_Requerido']:
                        G.add_edge(u, v, tipo='Recurso_Fisico')

                if data_u['ID_Disciplina'] == data_v['ID_Disciplina']:
                    G.add_edge(u, v, tipo='Disciplina')

    print(f"Grafo construído: {len(G.nodes)} nós, {len(G.edges)} arestas de conflito.")
    return G, nx.complement(G)


# TODO: Implementar classe do Solver (Carlos/Dev3)

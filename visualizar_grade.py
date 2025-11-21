# visualizar_grade.py
import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 

ARQUIVO_DADOS = os.path.join(BASE_DIR, "dataset_processado.csv")
ARQUIVO_GRADE = os.path.join(BASE_DIR, "grade_final.csv")

# Cria a pasta 'visualizar'
output_dir = os.path.join(BASE_DIR)
os.makedirs(output_dir, exist_ok=True)
ARQUIVO_SAIDA = os.path.join(output_dir, "grade_visual.html")

# Configurações de Slots
ORDEM_SLOTS = ['M1_M2', 'M3_M4', 'T1_T2', 'T3_T4', 'N1_N2', 'N3_N4', 'N3_N4_N5']
ORDEM_DIAS = ['SEG', 'TER', 'QUA', 'QUI', 'SEX']

def aplicar_trilhas(df):
    """Recalcula a lógica de trilhas para visualização"""
    df['Tipo_Real'] = df['Nome'].apply(lambda x: 'OP' if '_OP_' in x else 'OB')
    df['Trilha'] = 0 # 0 = Nenhuma/Obrigatória
    
    # Agrupa e aplica a mesma lógica do main.py
    grupos = df[df['Tipo_Real'] == 'OP'].groupby(['Curso', 'Periodo'])
    
    for (curso, periodo), grupo in grupos:
        if int(periodo) >= 5:
            disciplinas_unicas = grupo['ID_Disciplina'].unique()
            # Mapa determinístico: índice par = Trilha 1, ímpar = Trilha 2
            mapa_trilha = {disc: (i % 2) + 1 for i, disc in enumerate(disciplinas_unicas)}
            
            for idx, row in grupo.iterrows():
                if row['ID_Disciplina'] in mapa_trilha:
                    df.at[idx, 'Trilha'] = mapa_trilha[row['ID_Disciplina']]
    return df

def gerar_visualizacao():
    if not os.path.exists(ARQUIVO_GRADE): 
        print("Arquivo grade_final.csv não encontrado!")
        return
        
    df_dados = pd.read_csv(ARQUIVO_DADOS)
    df_grade = pd.read_csv(ARQUIVO_GRADE)
    
    # Merge
    df = pd.merge(df_grade, df_dados, left_on='Aula', right_on='ID_Aula', how='left')
    
    # Aplica identificação de Trilhas
    df = aplicar_trilhas(df)
    
    # Extrai slot e dia
    df['Dia'] = df['Horario'].apply(lambda x: x.split('_')[0])
    df['Slot'] = df['Horario'].apply(lambda x: '_'.join(x.split('_')[1:]))
    
    grupos = df.groupby(['Curso', 'Periodo'])
    
    # --- HTML ---
    html = """
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Grade Universitária - Trilhas de Optativas</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { background-color: #f0f2f5; padding-top: 20px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
            
            /* Estilo Base do Card */
            .aula-card { 
                background-color: #fff; 
                border-left: 5px solid #0d6efd; /* Azul padrão (OB) */
                padding: 10px; 
                margin-bottom: 8px; 
                box-shadow: 0 2px 5px rgba(0,0,0,0.08);
                border-radius: 6px;
                font-size: 0.85rem;
                position: relative;
                transition: transform 0.2s;
            }
            .aula-card:hover { transform: scale(1.02); box-shadow: 0 4px 10px rgba(0,0,0,0.15); z-index: 10; }
            
            /* Estilos de Trilha */
            .aula-card.trilha-1 { 
                border-left-color: #0dcaf0; /* Ciano */
                background-color: #faffff;
            }
            .aula-card.trilha-2 { 
                border-left-color: #ffc107; /* Amarelo/Laranja */
                background-color: #fffff5;
            }
            
            /* Tipografia */
            .materia { font-weight: 700; color: #343a40; display: block; margin-bottom: 4px; line-height: 1.2; }
            .prof { font-size: 0.8rem; color: #6c757d; display: block; }
            .lab { font-size: 0.75rem; color: #dc3545; font-weight: bold; display: block; margin-top: 4px; }
            
            /* Badges */
            .badge-trilha {
                position: absolute;
                top: 5px;
                right: 5px;
                font-size: 0.65rem;
                padding: 3px 6px;
                border-radius: 4px;
                text-transform: uppercase;
                font-weight: bold;
            }
            .bg-t1 { background-color: #0dcaf0; color: #000; }
            .bg-t2 { background-color: #ffc107; color: #000; }
            
            /* Tabela */
            .slot-cell { 
                vertical-align: middle; 
                font-weight: bold; 
                background-color: #e9ecef; 
                color: #495057;
                width: 100px; 
                text-align: center; 
                font-size: 0.8rem;
            }
            .table th { text-align: center; background-color: #212529; color: white; border: none;}
            
            /* Navegação */
            .nav-pills .nav-link.active { background-color: #0d6efd; }
            .tab-content { background-color: white; padding: 20px; border-radius: 0 0 8px 8px; border: 1px solid #dee2e6; border-top: none; }
        </style>
    </head>
    <body>
    <div class="container-fluid px-4">
        <h2 class="text-center mb-4">Grade Horária Otimizada <small class="text-muted fs-6">Com Visualização de Trilhas</small></h2>
    """

    # --- NAVEGAÇÃO POR CURSO ---
    cursos = sorted(df['Curso'].unique())
    html += '<ul class="nav nav-tabs" id="cursoTabs" role="tablist">'
    for i, curso in enumerate(cursos):
        active = 'active' if i == 0 else ''
        html += f"""
        <li class="nav-item">
            <button class="nav-link {active}" id="{curso}-tab" data-bs-toggle="tab" data-bs-target="#{curso}-pane" type="button" role="tab">{curso}</button>
        </li>"""
    html += '</ul>'
    
    html += '<div class="tab-content">'
    for i, curso in enumerate(cursos):
        active = 'show active' if i == 0 else ''
        html += f'<div class="tab-pane fade {active}" id="{curso}-pane" role="tabpanel">'
        
        # --- NAVEGAÇÃO POR PERÍODO ---
        periodos = sorted(df[df['Curso'] == curso]['Periodo'].unique())
        html += f'<div class="d-flex align-items-start mt-3"><div class="nav flex-column nav-pills me-3" role="tablist" aria-orientation="vertical">'
        
        for j, p in enumerate(periodos):
            p_active = 'active' if j == 0 else ''
            html += f'<button class="nav-link {p_active} text-start" id="v-pills-{curso}-{p}-tab" data-bs-toggle="pill" data-bs-target="#v-pills-{curso}-{p}" type="button" role="tab">Periodo {p}</button>'
        
        html += '</div><div class="tab-content w-100">'
        
        for j, p in enumerate(periodos):
            p_active = 'show active' if j == 0 else ''
            html += f'<div class="tab-pane fade {p_active}" id="v-pills-{curso}-{p}" role="tabpanel">'
            
            # --- CONSTRUÇÃO DOS CARDS ---
            grupo = grupos.get_group((curso, p))
            mapa_aulas = {}
            
            for _, row in grupo.iterrows():
                key = (row['Slot'], row['Dia'])
                if key not in mapa_aulas: mapa_aulas[key] = []
                
                # Definição visual baseada na Trilha
                classe_css = ""
                badge_html = ""
                
                trilha = int(row['Trilha']) if pd.notna(row['Trilha']) else 0
                
                if trilha == 1:
                    classe_css = "trilha-1"
                    badge_html = "<span class='badge-trilha bg-t1'>Trilha 1</span>"
                elif trilha == 2:
                    classe_css = "trilha-2"
                    badge_html = "<span class='badge-trilha bg-t2'>Trilha 2</span>"
                
                lab_html = f"<span class='lab'>{row['Lab_Requerido']}</span>" if pd.notna(row['Lab_Requerido']) else ""
                
                card = f"""
                <div class='aula-card {classe_css}'>
                    {badge_html}
                    <span class='materia'>{row['Nome']}</span>
                    <span class='prof'>{row['Professor']}</span>
                    {lab_html}
                </div>
                """
                mapa_aulas[key].append(card)
            
            # --- TABELA HTML ---
            html += '<div class="table-responsive"><table class="table table-bordered mb-0">'
            html += '<thead><tr><th>Horário</th>' + "".join([f"<th>{d}</th>" for d in ORDEM_DIAS]) + '</tr></thead><tbody>'
            
            slots_ver = [s for s in ORDEM_SLOTS if ('N' in s) == ('SIN' in curso)]
            
            for slot in slots_ver:
                nome_vis = slot.replace('_', '<br>')
                if slot == 'N3_N4_N5': nome_vis = "N3 - N5<br>(3h)"
                
                html += f"<tr><td class='slot-cell'>{nome_vis}</td>"
                for d in ORDEM_DIAS:
                    key = (slot, d)
                    content = "".join(mapa_aulas.get(key, []))
                    html += f"<td style='min-width: 140px; vertical-align: top;'>{content}</td>"
                html += "</tr>"
            
            html += '</tbody></table></div>'
            html += '</div>' # Fim Tab Pane Periodo
            
        html += '</div></div>' # Fim Layout Flex
        html += '</div>' # Fim Tab Pane Curso

    html += """
    </div></div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """
    
    with open(ARQUIVO_SAIDA, "w", encoding="utf-8") as f: f.write(html)
    print(f"Visualização salva em {ARQUIVO_SAIDA}")

if __name__ == "__main__":
    gerar_visualizacao()
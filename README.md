# University Timetabling Solver: Otimização de Grades Horárias com Grafos


## 👥 Integrantes da Equipe

| Nome Completo | Matrícula |
|:---|:---:|
| [IVAN MATHEUS RIBEIRO SILVERIO] | [2024006649] |
| [JOAO VITOR PINHEIRO FORTUNATO] | [2024003315] |
| [PEDRO LUIZ DE MORAES FERREIRA] | [2024008830] |
| [THEO HENRIQUE AZEVEDO DE CARVALHO PEREIRA] | [2024006729] |



## 🔗 Links Importantes

- **Vídeo de Apresentação**: [[Insira o link do YouTube aqui](https://youtu.be/Nst9dYsIEVo)]

---

## 📝 Introdução e Contexto

O **Problema de Cronograma Universitário (University Timetabling Problem)** é um desafio clássico de otimização combinatória. O objetivo é alocar aulas em horários e salas limitados, respeitando uma série de restrições (disponibilidade de professores, não sobreposição de turmas, capacidade de salas, etc.).

**Nossa Solução:**
Implementamos uma abordagem baseada em **Grafos Multicamadas**, onde as restrições (Turma, Professor, Recurso) formam camadas de conflito sobrepostas. A alocação de horários é resolvida encontrando **Cliques Maximais** no grafo complemento — identificando o maior conjunto de aulas compatíveis para cada slot de tempo. O algoritmo utiliza **Backtracking** guiado por uma **Função de Score**, que pontua as soluções baseando-se nas preferências dos professores e na distribuição de carga horária.

## 📂 Estrutura do Projeto

A organização dos arquivos no repositório é a seguinte:

- **`main.py`**: O coração do projeto. Contém a lógica de construção do grafo de conflitos, o algoritmo de backtracking para alocação de slots e a função objetivo para otimização.
- **`dataset_processado.csv`**: Base de dados de entrada contendo as disciplinas, professores, cargas horárias e restrições.
- **`grade_final.csv`**: Arquivo de saída gerado pelo algoritmo com a grade horária otimizada.
- **`visualizar_grade.py`**: Script auxiliar que lê o CSV final e gera uma visualização HTML amigável da grade (`grade_visual.html`).


## 🛠️ Tecnologias Utilizadas

O projeto foi desenvolvido inteiramente em **Python 3.10+**, utilizando as seguintes bibliotecas:

- **[NetworkX](https://networkx.org/)**: Para modelagem, manipulação e algoritmos de grafos.
- **[Pandas](https://pandas.pydata.org/)**: Para manipulação eficiente de dados tabulares (CSV).


## 🚀 Como Rodar o Projeto

Siga os passos abaixo para executar o otimizador em sua máquina local.

### 1. Clonar o Repositório
```bash
git clone https://github.com/IvanSilverio/University-Timetabling-Solver.git
cd University-Timetabling-Solver
```

### 2. Configurar o Ambiente Virtual (Recomendado)
Crie e ative um ambiente virtual para isolar as dependências:

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependências
Instale as bibliotecas necessárias listadas acima:
```bash
pip install pandas networkx 
```

### 4. Executar o Solucionador
Para rodar o algoritmo principal e gerar a grade:
```bash
python main.py
```
*O programa exibirá o progresso da otimização no terminal e salvará o resultado em `grade_final.csv`.*

### 5. Visualizar os Resultados
Para gerar a visualização da grade em HTML:
```bash
python visualizar_grade.py
```
*Abra o arquivo `grade_visual.html` gerado no seu navegador.*

## 💡 Exemplos de Uso

Ao executar o `main.py`, o sistema realiza múltiplas iterações de otimização dentro de um tempo limite. A saída típica no terminal será:

```text
Iniciando Otimização por 15 segundos...
[T+0.5s] Solução #1 encontrada. Score: 120
[T+1.2s] Solução #2 encontrada. Score: 150
   >>> NOVA MELHOR GRADE! (Score: 150)
...
FIM. Soluções: 528. Melhor Score: 350
Melhor grade salva em 'grade_final.csv'.
```

Você pode ajustar o tempo de execução ou as preferências dos professores diretamente no arquivo `main.py`.


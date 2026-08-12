# Sistema de Alta Performance para Concursos (Foco DATAPREV) 🚀

Este projeto é um ecossistema completo e inteligente de estudos voltado para a preparação estratégica do concurso da DATAPREV (prova em 11/10/2026). Ele não é apenas um banco de questões, mas sim um "treinador pessoal" implacável que força a disciplina, controla o tempo e gera conteúdo direcionado com Inteligência Artificial.

## 🏗️ Arquitetura do Sistema

A aplicação é dividida em dois grandes blocos: o Pipeline de Ingestão (Backend offline) e o Aplicativo de Estudos (Frontend interativo em Streamlit).

### 1. Pipeline de Ingestão (`backend/ingest/`)
O motor de processamento de PDFs responsável por ler provas passadas e extrair questões para o banco de dados.
- **Leitura e Extração:** Usa PyMuPDF (`fitz`) para ler PDFs e limpar o texto.
- **Inteligência Local (Ollama/Qwen):** Envia os blocos de texto para um modelo LLM local (Qwen 7B/3B) com um prompt rígido pedindo a extração das questões em formato JSON.
- **Resiliência e Auto-Cura:** Conta com um algoritmo avançado de *fallback* que detecta se o modelo perdeu o fôlego (truncou o JSON no limite de tokens) e tenta resgatar e salvar as questões que foram processadas corretamente, evitando perda de trabalho.
- **Persistência:** Valida o formato e salva no banco SQLite (`data/db.sqlite`).

### 2. Aplicativo Principal (`app.py` - Streamlit)
A interface de linha de frente, dividida estrategicamente em 4 abas para cobrir todo o ciclo PDCA do concurseiro.

#### Aba 1: 📅 Hoje (O Modo Sprint)
É o coração disciplinador da aplicação.
- **Trava de Calendário:** A aba consulta o banco de dados e o relógio do seu computador. Se for dia útil, o sistema trava você exatamente nos 2 tópicos programados pelo cronograma para aquele dia específico. Não há livre arbítrio.
- **Estudo Livre (Finais de Semana):** Se for Sábado ou Domingo, o sistema entra em modo livre, habilitando menus suspensos para você focar nas suas maiores deficiências.
- **Controle de Meta (5 Horas/Dia):** Uma barra de progresso cronometra e acumula os segundos gastos lendo a teoria e os segundos gastos pensando nas questões, até atingir a meta diária de 5 horas.
- **Máquina de Estados de Estudo (Flashcards):**
  1. **Ler Resumo:** O sistema busca instantaneamente o resumo no SQLite local. Se não existir, chama a API do Groq (Llama 3 70b) para gerar um focado em "como as bancas cobram".
  2. **Gerar Questão:** Aciona o Groq para criar uma questão inédita nível "HARD".
  3. **Responder e Analisar:** Ao errar ou acertar, o Groq atua como um professor particular e explica de forma cirúrgica o erro do candidato.
- **Alta Disponibilidade (Fallback Local):** Qualquer requisição ao Groq (API Nuvem) está protegida. Se a internet cair, a chave falhar ou a API sair do ar, o sistema silenciosamente direciona o pedido para o seu **Qwen Local**, garantindo que seus estudos nunca parem.

#### Aba 2: 🗺️ Cronograma
O mapa mental estratégico. 
- Gerado pelo algoritmo (`gerar_cronograma.py`), ele mapeou todos os 139 subgrupos do edital e calculou o peso de cada disciplina (ex: Conhecimentos Específicos valem 65.2% da prova).
- Com base nesse peso, ele distribuiu matematicamente 140 "Slots" de estudo pelas 14 semanas até a prova. Ex: Você repetirá o slot de "Inglês" exatamente 15 vezes ao longo dos 70 dias úteis, garantindo que o tempo gasto seja proporcional ao que vai te dar pontos no dia da prova.

#### Aba 3: 📝 Modo Prova
O ambiente de simulação real.
- **Prova por Tema:** Puxa questões avulsas do banco local sobre o tema selecionado.
- **Simulado Geral DATAPREV:** Recria a estrutura idêntica do edital:
  - Módulo I (Básicos): 40 questões, peso 1.0 (Português, Inglês, RLM, Atualidades/IA e Legislação).
  - Módulo II (Específicos): 30 questões, peso 2.5.
- Ao finalizar, calcula sua pontuação final exata no formato da prova (Total: 115 pontos).

#### Aba 4: 📊 Estatísticas (Radar do Edital)
Painel de Business Intelligence pessoal.
- **Projeção de Pontuação Real (Simulado Dinâmico):** Consolida em tempo real todas as suas questões respondidas, categorizando nas 6 disciplinas do edital. Aplica os devidos pesos (1.0 para básicos e 2.5 para específicos) e apresenta uma tabela final com a "Nota Projetada" se a prova fosse realizada naquele exato momento.
- **Evolução Temporal:** Gráfico de linhas dinâmico plotando o histórico e a progressão de sua taxa de acertos (%) ao longo dos dias, fundamental para visualizar ganho de consistência.
- **Raio-X por Tópico:** Tabela detalhada combinando o tempo gasto lendo teorias e respondendo questões. Permite identificar em quais subgrupos você gasta mais tempo e tem as piores taxas de acerto.

---
**Tech Stack:** Python, Streamlit, SQLite, Pandas, LangChain (Groq API Cloud + Ollama Local), PyMuPDF.

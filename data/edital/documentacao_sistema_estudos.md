# Sistema Inteligente de Preparação para Concursos (Foco DATAPREV)

Este documento detalha a arquitetura, os componentes e a metodologia educacional do sistema de estudos personalizado desenvolvido para otimizar sua aprovação no concurso. O sistema foi desenhado para ser uma "máquina de aprendizado" autônoma, que coleta, classifica e testa seu conhecimento de forma inteligente.

---

## 🏗️ 1. Visão Geral da Arquitetura

A aplicação é dividida em três pilares principais: **Coleta (Crawler)**, **Processamento (LLM Classifier)** e **Consumo (Plataforma Streamlit)**. Todos os dados gravitam em torno do banco de dados relacional `db_novo.sqlite` e do seu `mapa_mental.json` (que define as regras do edital).

### 🕷️ O Crawler (Coletor)
- **Tecnologia:** Python com `Playwright` e `BeautifulSoup`.
- **Objetivo:** Navegar autonomamente no site *Estude Grátis* (ou outros bancos), filtrando pela banca FGV, e extrair milhares de questões.
- **Inteligência:** Possui um sistema de resiliência a quedas (tentativas automáticas em caso de Timeout), burla bloqueios do Cloudflare e encerra automaticamente a extração de uma matéria quando detecta que a paginação entrou em loop ou não há mais questões inéditas.

### 🧠 O Classificador (Motor LLM)
- **Tecnologia:** Python integrando múltiplas APIs de IA (`Groq`, `OpenRouter`, `Gemini`).
- **Objetivo:** Pegar as questões "cruas" trazidas pelo Crawler e analisá-las uma a uma usando Inteligência Artificial.
- **Inteligência:** O script (`classificar.py`) roda em *looping*, enviando a questão para a IA e exigindo que ela responda no formato JSON com qual Grupo e Subgrupo exato aquela questão pertence, baseando-se estritamente no seu `mapa_mental.json`. Se uma chave de API bater no limite de requisições, ele rotaciona silenciosamente para a próxima.

### 💻 A Interface (Streamlit)
- **Tecnologia:** Streamlit (App Web) + Pandas + SQLite.
- **Objetivo:** Ser o seu "Tutor de Bolso" e painel de controle. É aqui que o estudo prático acontece.

---

## 🎯 2. Como a Plataforma Impulsiona seus Estudos

A aplicação (`app.py`) não é apenas um banco de questões estático; ela foi desenhada baseada em **ciência cognitiva** (Active Recall e Spaced Repetition) e fatiada em 5 abas principais:

### 📅 A. Hoje (Plano de Operações Diárias - POD)
Esta aba é o coração da sua aprovação. Todo dia o sistema calcula o que você deve estudar:
1. **Teoria Sob Demanda:** Ao se deparar com um tema novo (ex: "Computação em Nuvem"), se você não tiver o material, pode pedir para a IA gerar o resumo na hora.
2. **Active Recall (Lembrança Ativa):** Antes de fazer questões, o sistema te força a tentar lembrar o que acabou de ler sem olhar o texto. Isso cimenta a sinapse no seu cérebro.
3. **Avaliação Prática:** Em seguida, ele puxa uma questão inédita daquele assunto.
4. **Tutor IA:** Se você errar a questão, pode clicar no botão de "Análise Cirúrgica", onde a IA explica exatamente o porquê a alternativa que você marcou está errada e por que o gabarito está certo. Se uma questão do banco não tiver o gabarito oficial, a própria IA resolve e salva no banco.

### 📝 B. Modo Prova (Simulado de Resistência)
Construído para simular a pressão real:
- **Filtro Laser:** Você pode escolher exatamente qual "Tema" (Grupo) quer estudar e selecionar a dedo os "Subgrupos" originários do seu Mapa Mental (com caixas de seleção dinâmicas).
- **Sem Spoilers:** Existe um filtro (`Somente inéditas`) que vasculha seu histórico e proíbe o SQL de sortear questões que você já respondeu no passado, evitando falsos positivos na sua taxa de acerto.
- **Pesos Reais:** O sistema já entende automaticamente que matérias básicas (como *LÍNGUA PORTUGUESA*) valem **Peso 1.0**, enquanto conhecimentos específicos valem **Peso 2.5**, calculando seu score final com altíssima precisão.

### 📊 C. Estatísticas
Seu painel de métricas. Ele analisa a tabela de `respostas` e exibe:
- Taxa de acerto global e por matéria.
- Progresso do aprendizado (quais subgrupos você já domina e quais estão pendentes).
- Ajuda a identificar gargalos (matérias de Peso 2.5 onde o rendimento está baixo e precisam de mais revisão).

### 🛠️ D. Gerenciador
Permite que você assuma o controle do banco de dados sem precisar digitar código:
- Adicionar questões manualmente (ou importá-las via JSON/TXT script `import_questoes_ia.py`).
- Editar o texto de questões defeituosas.
- **Remover/Invalidar:** Se cruzar com uma questão desatualizada (ex: lei revogada) na prova, um clique a remove para sempre dos seus sorteios.

---

## 🚀 3. Fluxo de Trabalho (O Seu Dia a Dia)

Para extrair o máximo desse sistema, o seu ciclo de vida concurseiro funciona assim:

1. **Alimentação (Background):** Enquanto você dorme ou estuda, os scripts `crawler.py` e `classificar.py` podem rodar no terminal, engordando o banco com questões frescas da FGV e classificando-as com IA.
2. **Estudo Diário (Modo Hoje):** Você acorda, abre o app e cumpre seu "POD". Lê a teoria, tenta lembrar (Active Recall) e valida o conhecimento em 1 questão.
3. **Bateria de Testes (Modo Prova):** Depois de aprender a teoria, você vai para o Modo Prova e gera um simulado filtrado daquela matéria para fixar o conteúdo através da exaustão e repetição.
4. **Análise de IA (Tutor):** Errou? Não procure no Google. Peça para a IA explicar o erro diretamente na interface.
5. **Ajuste de Rota (Estatísticas):** No final da semana, olhe suas métricas e ajuste o foco para a semana seguinte.

**Resumo:** O sistema elimina a necessidade de planilhas complexas, assinaturas caras de sites de cursinhos e PDFs estáticos. Ele é vivo, focado exclusivamente no seu edital (Dataprev) e automatiza a curadoria de conteúdo para que você gaste 100% da sua energia apenas na absorção de conhecimento.

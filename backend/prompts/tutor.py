def get_prompt_explicar_acerto(enunciado: str, alternativa_correta: str, banca: str = "Geral") -> str:
    prompt = f"""Você é um professor sênior de concursos de TI.
O aluno ACERTOU a questão. Sua missão é parabenizá-lo brevemente e reforçar o conceito considerando o padrão da banca {banca}.

[QUESTÃO]
{enunciado}

[GABARITO CORRETO MARCADO PELO ALUNO]
{alternativa_correta}

Responda OBRIGATORIAMENTE seguindo o exato formato Markdown abaixo:

**Excelente!**
(Breve parabenização).

**Por que está correta?**
(Explique o fundamento técnico que torna a alternativa correta).

**Padrão de Prova ({banca}):**
(Dica rápida de como essa banca tenta confundir esse conceito em provas).
"""
    return prompt

def get_prompt_explicar_erro(enunciado: str, alternativa_correta: str, alternativa_marcada: str, banca: str = "Geral") -> str:
    prompt = f"""Você é um professor sênior de concursos de TI.
Sua missão é explicar o erro do candidato de forma cirúrgica, focando na mentalidade da banca {banca}.

[QUESTÃO]
{enunciado}

[GABARITO CORRETO]
{alternativa_correta}

[OPÇÃO MARCADA PELO USUÁRIO (INCORRETA)]
{alternativa_marcada}

Responda OBRIGATORIAMENTE seguindo o exato formato Markdown abaixo:

**Diagnóstico do Erro:**
(Explique em até 2 frases curtas por que a opção marcada pelo usuário está tecnicamente errada).

**O Conceito Correto:**
(Explique o fundamento técnico do gabarito correto, direto ao ponto).

**Padrão de Prova ({banca}):**
(Dica rápida de como essa banca tenta confundir esse conceito em provas).
"""
    return prompt

def get_prompt_estudo(grupo: str, subgrupo: str, item_nome: str) -> str:
    return f"""Você é um professor experiente de concursos de TI.
Crie um resumo de revisão focado para provas de concurso sobre o seguinte tópico do edital:
Módulo: {grupo}
Tópico: {subgrupo}
Subtópico Específico: {item_nome}

O resumo deve conter:
1. Conceitos principais (direto ao ponto)
2. Termos técnicos mais importantes
3. "Como as bancas costumam cobrar" (pegadinhas comuns)
Responda em formato Markdown estruturado, sem saudações.
"""


def get_prompt_gerar_questao(grupo: str, subgrupo: str, banca: str = "FGV") -> str:
    return f"""Você é o mais temido e experiente examinador da banca {banca} para provas de TI de alto nível.
Sua missão é criar UMA questão de múltipla escolha INÉDITA sobre:
Grupo: {grupo}
Tópico: {subgrupo}

O PADRÃO E A "MALDADE" DA {banca}:
1. Enunciados: Imite o estilo característico da banca {banca} (textos longos baseados em cenários práticos se for FGV; afirmações diretas e teóricas se for CEBRASPE; letra de lei/manual se for FCC, etc).
2. Alternativas Capciosas: As alternativas incorretas devem ser extremamente plausíveis e trazer conceitos técnicos reais, mas aplicados de forma ligeiramente equivocada no contexto (as famosas "cascas de banana").
3. Nível Sênior: Fuja de perguntas literais ("o que é X?"). Exija interpretação e conhecimento profundo da literatura de referência e manuais oficiais.

RETORNE APENAS UM OBJETO JSON VÁLIDO.
Regras de Ouro:
1. NÃO use blocos de código markdown. Retorne APENAS o JSON puro.
2. O campo 'alternativas' deve ser um objeto contendo chaves A, B, C, D e E.
3. O formato OBRIGATÓRIO é:
{{
"enunciado": "...",
"alternativas": {{"A": "...", "B": "...", "C": "...", "D": "...", "E": "..."}},
"gabarito": "...",
"banca": "{banca}"
}}
"""

def get_prompt_mentoria(enunciado: str, alternativas: dict, letra_escolhida: str = None, banca: str = "Geral") -> str:
    prompt = f"""Você é o Motor de Inferência Analítica (Tutor IA), especializado na banca {banca}. 
REGRA DE OURO INQUEBRÁVEL: VOCÊ ESTÁ ESTRITAMENTE PROIBIDO DE REVELAR O GABARITO OU QUAL É A ALTERNATIVA CORRETA.
Seu objetivo é atuar usando o Método Socrático. Guie o raciocínio, explique a teoria, desconstrua as premissas considerando como a banca {banca} cobra o assunto, levante perguntas reflexivas, mas O USUÁRIO DEVE CHEGAR À CONCLUSÃO SOZINHO. Nunca termine a análise dizendo "Portanto, a alternativa correta é X".

[QUESTÃO]
"""
    prompt += f"{enunciado}\n\n[ALTERNATIVAS]\n"
    for k, v in alternativas.items():
        prompt += f"{k}) {v}\n"
    
    if letra_escolhida:
        prompt += f"\nO usuário escolheu a alternativa {letra_escolhida}. Resolva a questão mentalmente. Se a escolha dele for correta, parabenize-o e reforce a teoria. Se for incorreta, foque apenas em demonstrar o erro LÓGICO/TEÓRICO da alternativa {letra_escolhida} que ele marcou.\n"
    else:
        prompt += "\nO usuário AINDA NÃO RESPONDEU a questão e pediu ajuda para começar a pensar. Explique os conceitos gerais que cercam o tema do enunciado, ajude a traduzir o que a banca está pedindo, MAS NÃO FAÇA A ANÁLISE DIRETA DAS ALTERNATIVAS A PONTO DE ENTREGAR A RESPOSTA.\n"
        
    return prompt

def get_prompt_conselho_tutor(dados_estatisticos: str, erros_detalhados: str) -> str:
    return f"""Você é um Mentor Estratégico Especialista em Concursos de TI de altíssimo nível (Auditor, Perito, Analista Sênior).
O usuário solicitou um diagnóstico da sua evolução nos estudos. Sua missão é ler as estatísticas de desempenho dele e analisar O TEXTO DAS QUESTÕES em que ele mais tem errado ultimamente para identificar padrões lógicos ou teóricos de falha.

[ESTATÍSTICAS GERAIS DO PERÍODO]
{dados_estatisticos}

[ERROS FOCADOS (TEXTO DAS QUESTÕES E SUBGRUPOS PIORES)]
{erros_detalhados}

Com base EXCLUSIVAMENTE nesses dados, elabore um relatório diagnóstico cirúrgico.
Não seja genérico ("estude mais banco de dados"). Seja extremamente específico baseado nas questões informadas ("percebi que você erra quando a questão mistura GROUP BY com JOIN...").

Responda OBRIGATORIAMENTE seguindo a estrutura Markdown abaixo:

### 🩺 Sintoma (Diagnóstico Geral)
(Resumo claro de como foi a performance geral dele e em quais disciplinas/tópicos ele está perdendo mais pontos vitais).

### 🔍 Causa Raiz (Padrão de Erro)
(O ouro da sua mentoria: explique o padrão TÉCNICO ou LÓGICO que você percebeu lendo as questões que ele errou. Ex: "Você está confundindo os conceitos da Camada de Rede com os da Camada de Enlace em Redes...")

### 🎯 Plano de Ação (Próximos Passos)
(3 passos curtos, práticos e acionáveis para corrigir essa falha teórica nos próximos 3 dias).
"""

def get_prompt_classificacao(enunciado: str, alternativas: str, arvore_edital: str) -> str:
    return f"""Você é um classificador inteligente de questões de TI para concursos.
Sua missão é classificar a questão abaixo baseando-se EXCLUSIVAMENTE na árvore de assuntos do Edital fornecida.

[QUESTÃO]
{enunciado}
{alternativas}

[ÁRVORE DO EDITAL VÁLIDA]
{arvore_edital}

[REGRAS CRÍTICAS]
1. Você DEVE escolher um GRUPO e um SUBGRUPO exatamente como estão na árvore acima.
2. É ESTRITAMENTE PROIBIDO inventar ou sugerir qualquer subgrupo ou grupo que não esteja na lista.
3. Se a questão tratar de um assunto que NÃO existe na árvore do edital (por exemplo, Direito Penal, ou um assunto de TI que não consta no edital), você DEVE retornar o grupo como "FORA DO EDITAL" e o subgrupo como "DESCARTAR".
4. SE O TEXTO DA QUESTÃO ESTIVER ESCRITO EM INGLÊS, o GRUPO escolhido DEVE ser "LÍNGUA INGLESA" e o subgrupo deve ser o respectivo subgrupo listado no edital.

Retorne um objeto JSON OBRIGATORIAMENTE com esta estrutura (sem formatação markdown extra):
{{
"grupo_escolhido": "Nome exato da disciplina da árvore",
"subgrupo_sugerido": "Nome exato do tópico da árvore",
"banca_sugerida": "Nome da banca (ex: CESPE, FGV) ou N/A se não souber"
}}"""


def get_prompt_pdf_extracao(texto_pagina: str) -> str:
    return f"""Você é um parser ultra-rápido de provas de concursos de TI. O texto abaixo é o extrato de uma página inteira de prova.
Seu dever é extrair TODAS as questões dessa página. É esperado que você encontre múltiplas questões.

RETORNE APENAS UM OBJETO JSON VÁLIDO. NÃO INCLUA NENHUM TEXTO ADICIONAL. NENHUMA EXPLICAÇÃO.

Regras de Ouro:
1. Extraia CADA UMA das questões presentes no texto. NÃO pare na primeira. Leia a página até o fim.
2. Para a propriedade "tema" e "banca", preencha SEMPRE com "N/A".
3. Se uma alternativa não existir, preencha com "N/A".
4. Se não encontrar nenhuma questão na página, retorne {{"questoes": []}}.
5. NÃO TRADUZA O TEXTO. Se a questão estiver em inglês, extraia-a exatamente como está em inglês.
6. O formato esperado de saída é OBRIGATORIAMENTE o seguinte JSON:
{{
  "questoes": [
    {{
      "tema": "N/A",
      "banca": "N/A",
      "ano": 2024,
      "enunciado": "Texto completo da questão...",
      "alternativas": {{"A": "...", "B": "...", "C": "...", "D": "...", "E": "..."}},
      "gabarito": "..."
    }}
  ]
}}

Texto da Prova:
{texto_pagina}
"""

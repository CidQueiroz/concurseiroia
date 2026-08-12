import fitz


def extrair_texto(pdf_path: str) -> str:
    texto = ""

    with fitz.open(pdf_path) as pdf:
        for pagina in pdf:
            texto += pagina.get_text()

    return texto
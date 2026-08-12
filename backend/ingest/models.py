from pydantic import BaseModel
from typing import Optional

class Questao(BaseModel):
    tema: str
    banca: str = "N/A"
    ano: Optional[int] = None
    enunciado: str
    # Tornamos cada alternativa opcional para o Pydantic não quebrar
    alternativas: dict[str, Optional[str]] = {
        "A": None, "B": None, "C": None, "D": None, "E": None
    }
    gabarito: Optional[str] = None
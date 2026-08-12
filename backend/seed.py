import sqlite3
import os
from database import DB_PATH

def seed_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Limpa dados anteriores para evitar duplicação em testes
    cursor.execute("DELETE FROM questoes")
    cursor.execute("DELETE FROM assuntos")

    # Inserir Assuntos (Edital Dataprev - Perfil 2)
    assuntos = [
        ("Arquitetura e Engenharia de Software", 5, 0),
        ("Computação em Nuvem e Automação", 5, 0),
        ("Bancos de Dados", 4, 0),
        ("Redes de Computadores", 3, 0),
        ("Gestão e Governança (ITIL/COBIT)", 3, 0),
        ("Língua Portuguesa", 2, 0)
    ]
    cursor.executemany('INSERT INTO assuntos (nome, peso, dominio) VALUES (?, ?, ?)', assuntos)

    # Inserir Questão Fake (FGV - Cloud)
    questoes = [
        (2, "FGV", 2024, "Média", 
         "Na arquitetura de computação em nuvem, qual o principal benefício do uso de containers (como Docker) em comparação às máquinas virtuais tradicionais?", 
         "Isolamento a nível de hardware dedicado.", 
         "Compartilhamento do kernel do sistema operacional host.", 
         "Maior consumo de recursos de disco e memória.", 
         "Necessidade obrigatória de um hypervisor tipo 1.", 
         "Incompatibilidade com esteiras de CI/CD.", 
         "B")
    ]
    cursor.executemany('''
        INSERT INTO questoes (assunto_id, banca, ano, dificuldade, enunciado, alternativa_a, alternativa_b, alternativa_c, alternativa_d, alternativa_e, gabarito)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', questoes)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    seed_data()
    print("Operação Nominal: Dados iniciais injetados no banco.")
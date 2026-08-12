import sqlite3
import os

DB_PATH = "data/bancos/db_novo.sqlite"

def get_connection():
    """Retorna a conexão com o banco SQLite, garantindo que o diretório exista."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_db():
    """Inicializa as tabelas do sistema de estudos."""
    conn = get_connection()
    cursor = conn.cursor()

    # Tabela: grupos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS grupos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE
    )
    ''')

    # Tabela: subgrupos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS subgrupos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        grupo_id INTEGER,
        nome TEXT NOT NULL,
        peso INTEGER DEFAULT 1,
        dominio INTEGER DEFAULT 0,
        ultima_revisao DATE,
        proxima_revisao DATE,
        FOREIGN KEY (grupo_id) REFERENCES grupos (id),
        UNIQUE(grupo_id, nome)
    )
    ''')

    # Tabela: questoes
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS questoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subgrupo_id INTEGER,
        banca TEXT,
        ano INTEGER,
        dificuldade TEXT,
        enunciado TEXT,
        alternativa_a TEXT,
        alternativa_b TEXT,
        alternativa_c TEXT,
        alternativa_d TEXT,
        alternativa_e TEXT,
        gabarito TEXT,
        FOREIGN KEY (subgrupo_id) REFERENCES subgrupos (id)
    )
    ''')

    # Tabela: respostas (Métricas de Desempenho)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS respostas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        questao_id INTEGER,
        acertou BOOLEAN,
        tempo_segundos INTEGER,
        data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (questao_id) REFERENCES questoes (id)
    )
    ''')

    # Tabela: estudos_teoria (Métricas de tempo de leitura)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS estudos_teoria (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subgrupo_id INTEGER,
        tempo_segundos INTEGER,
        data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (subgrupo_id) REFERENCES subgrupos (id)
    )
    ''')

    # Tabela: sessoes (Histórico de Foco)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sessoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        inicio TIMESTAMP,
        fim TIMESTAMP,
        tempo_total INTEGER,
        nota REAL
    )
    ''')

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Operação Nominal: Banco de dados inicializado em data/bancos/db_novo.sqlite.")
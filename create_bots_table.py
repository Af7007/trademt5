"""
Cria tabela para armazenar bots no banco de dados
"""
import sqlite3
from datetime import datetime

DB_PATH = "mlp_data.db"

def create_bots_table():
    """Cria tabela de bots"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Criar tabela de bots
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bots (
            bot_id TEXT PRIMARY KEY,
            config TEXT NOT NULL,
            is_running BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP,
            stopped_at TIMESTAMP,
            total_trades INTEGER DEFAULT 0,
            total_profit REAL DEFAULT 0.0,
            winning_trades INTEGER DEFAULT 0,
            losing_trades INTEGER DEFAULT 0,
            notes TEXT
        )
    """)
    
    print("✓ Tabela 'bots' criada com sucesso!")
    
    # Criar tabela de histórico de ações dos bots
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bot_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bot_id TEXT NOT NULL,
            action TEXT NOT NULL,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (bot_id) REFERENCES bots(bot_id)
        )
    """)
    
    print("✓ Tabela 'bot_actions' criada com sucesso!")
    
    # Criar índices
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_bots_is_running 
        ON bots(is_running)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_bot_actions_bot_id 
        ON bot_actions(bot_id)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_bot_actions_timestamp 
        ON bot_actions(timestamp)
    """)
    
    print("✓ Índices criados com sucesso!")
    
    conn.commit()
    conn.close()

def show_schema():
    """Mostra estrutura das tabelas"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n" + "="*70)
    print("  ESTRUTURA DAS TABELAS")
    print("="*70)
    
    # Tabela bots
    print("\nTabela: bots")
    cursor.execute("PRAGMA table_info(bots)")
    for row in cursor.fetchall():
        print(f"  {row[1]:20} {row[2]:15} {'NOT NULL' if row[3] else ''}")
    
    # Tabela bot_actions
    print("\nTabela: bot_actions")
    cursor.execute("PRAGMA table_info(bot_actions)")
    for row in cursor.fetchall():
        print(f"  {row[1]:20} {row[2]:15} {'NOT NULL' if row[3] else ''}")
    
    conn.close()

def main():
    print("="*70)
    print("  CRIAÇÃO DE TABELAS DE BOTS")
    print("="*70)
    
    create_bots_table()
    show_schema()
    
    print("\n" + "="*70)
    print("  TABELAS CRIADAS COM SUCESSO!")
    print("="*70)
    print("\nAgora os bots serão salvos no banco de dados.")
    print("Benefícios:")
    print("  ✅ Bots persistem após reiniciar servidor")
    print("  ✅ Histórico de ações registrado")
    print("  ✅ Estatísticas mantidas")
    print("  ✅ Recuperação automática")

if __name__ == "__main__":
    main()

"""
Limpar TODOS os bots do banco de dados
"""
import sqlite3

DB_PATH = "mlp_data.db"

print("="*80)
print("  LIMPEZA COMPLETA DO BANCO DE DADOS")
print("="*80)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Contar bots
cursor.execute("SELECT COUNT(*) FROM bots")
count = cursor.fetchone()[0]

print(f"\nBots no banco: {count}")

if count > 0:
    # Deletar todos
    cursor.execute("DELETE FROM bots")
    cursor.execute("DELETE FROM bot_actions")
    
    conn.commit()
    print(f"✓ {count} bots deletados do banco")
    print("✓ Histórico de ações limpo")
else:
    print("\nNenhum bot no banco")

conn.close()

print("\n" + "="*80)
print("  BANCO LIMPO!")
print("="*80)
print("\nAgora crie bots novos que terão o código correto.")

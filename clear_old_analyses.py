"""
Limpar análises antigas do banco
"""
import sqlite3

DB_PATH = "mlp_data.db"

print("="*80)
print("  LIMPEZA DE ANÁLISES ANTIGAS")
print("="*80)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Contar análises
cursor.execute("SELECT COUNT(*) FROM mlp_analyses")
count = cursor.fetchone()[0]

print(f"\nAnálises no banco: {count}")

if count > 0:
    # Deletar todas
    cursor.execute("DELETE FROM mlp_analyses")
    
    conn.commit()
    print(f"✓ {count} análises deletadas")
else:
    print("\nNenhuma análise no banco")

conn.close()

print("\n" + "="*80)
print("  BANCO LIMPO!")
print("="*80)
print("\nAgora as análises serão apenas as novas (com sinais corretos).")

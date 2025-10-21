"""
Corrigir timezone das análises no banco de dados
"""
import sqlite3
from datetime import datetime, timedelta

DB_PATH = "mlp_data.db"

print("="*80)
print("  CORREÇÃO DE TIMEZONE")
print("="*80)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Verificar timezone atual
cursor.execute("SELECT datetime('now')")
db_time = cursor.fetchone()[0]
print(f"\nHorário do banco (UTC): {db_time}")

local_time = datetime.now()
print(f"Horário local (sistema): {local_time.strftime('%Y-%m-%d %H:%M:%S')}")

# Calcular diferença
db_dt = datetime.strptime(db_time, '%Y-%m-%d %H:%M:%S')
diff_hours = (local_time - db_dt).total_seconds() / 3600
print(f"Diferença: {diff_hours:.1f} horas")

# Atualizar todas as análises para horário local
print("\nAtualizando timestamps das análises...")

cursor.execute("""
    UPDATE mlp_analyses 
    SET timestamp = datetime(timestamp, 'localtime')
    WHERE timestamp NOT LIKE '%-%-%T%'
""")

affected = cursor.rowcount
print(f"  {affected} análises atualizadas")

conn.commit()

# Verificar resultado
cursor.execute("SELECT timestamp FROM mlp_analyses ORDER BY timestamp DESC LIMIT 5")
print("\nÚltimas 5 análises após correção:")
for row in cursor.fetchall():
    print(f"  {row[0]}")

conn.close()

print("\n" + "="*80)
print("  CORREÇÃO CONCLUÍDA")
print("="*80)
print("\nAgora as análises devem mostrar horário local correto.")
print("Recarregue a página do Bot Manager Pro (Ctrl+F5)")

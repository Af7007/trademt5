"""
Script para testar o Bot Manager via API
"""
import requests
import time
import webbrowser

FLASK_URL = "http://localhost:5000"

def test_bot_manager():
    print("="*70)
    print("  TESTE DO BOT MANAGER")
    print("="*70)
    
    # 1. Verificar se servidor está rodando
    print("\n1. Verificando servidor...")
    try:
        response = requests.get(f"{FLASK_URL}/health", timeout=5)
        if response.status_code == 200:
            print("   ✓ Servidor Flask rodando")
        else:
            print("   ✗ Servidor retornou erro")
            return
    except:
        print("   ✗ Servidor não está rodando")
        print("   Execute: .\\start_final.cmd")
        return
    
    # 2. Abrir interface no navegador
    print("\n2. Abrindo Bot Manager no navegador...")
    url = f"{FLASK_URL}/bot-manager"
    print(f"   URL: {url}")
    
    try:
        webbrowser.open(url)
        print("   ✓ Navegador aberto")
    except:
        print("   ⚠ Não foi possível abrir automaticamente")
        print(f"   Abra manualmente: {url}")
    
    print("\n" + "="*70)
    print("  BOT MANAGER PRONTO PARA USO!")
    print("="*70)
    print("\nInstruções:")
    print("  1. Use os templates BTC ou XAU")
    print("  2. Clique em 'INICIAR BOT'")
    print("  3. Monitore em tempo real")
    print("  4. Use 'PARAR BOT' quando necessário")
    print("\nPressione Ctrl+C para sair deste script")
    print("(O Bot Manager continuará funcionando)")
    
    # Manter script rodando
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nScript encerrado. Bot Manager ainda está ativo!")

if __name__ == "__main__":
    test_bot_manager()

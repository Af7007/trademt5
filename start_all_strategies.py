#!/usr/bin/env python3
"""
START ALL TRADING STRATEGIES
Executa BTC, XAU e GBP simultaneamente
"""

import subprocess
import sys
import time
import signal
import os

def run_strategy(script_name, display_name):
    """Executa uma estratégia específica em janela separada"""
    try:
        print("[OPENING] {} em janela separada...".format(display_name))
        # Abre em janela separada usando start command
        cmd = 'start "{}" cmd /k python {}'.format(display_name, script_name)
        proc = subprocess.Popen(cmd, shell=True)
        return proc
    except Exception as e:
        print("[ERROR] Failed to open {}: {}".format(display_name, e))
        return None

def stop_all(processes):
    """Para todos os processos"""
    print("\n[STOPPING] Todas as estratégias...")

    for proc in processes:
        if proc and proc.poll() is None:  # Ainda rodando
            try:
                proc.terminate()
                # Espera um pouco
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
            except Exception as e:
                print("[ERROR] Problema ao parar processo: {}".format(e))

def main():
    print("=" * 80)
    print("MULTI-SYMBOL TRADING SYSTEM")
    print("=" * 80)
    print("Iniciando 2 estratégias agressivas simultâneas:")
    print("• BTCUSDc - Bitcoin 24/7 (Agressivo)")
    print("• XAUUSDc - Ouro Forex Hours (Agressivo)")
    print("=" * 80)

    # Definição das estratégias - BTC e XAU mais agressivos
    strategies = [
        ('btc_scalp_strategy.py', 'BTC Strategy'),
        ('xau_scalp_strategy.py', 'XAU Strategy')
    ]

    processes = []
    strategy_info = []

    # Verificar se arquivos existem
    for script, name in strategies:
        if not os.path.exists(script):
            print("[ERROR] Arquivo {} não encontrado!".format(script))
            return
        strategy_info.append((script, name))

    print("Arquivos verificados OK!\n")

    try:
        # Iniciar todas as estratégias
        for script, name in strategy_info:
            # Pequena pausa entre inícios
            if processes:  # Não pausa na primeira
                time.sleep(1)

            proc = run_strategy(script, name)
            if proc:
                processes.append(proc)

        if not processes:
            print("[ERROR] Nenhuma estratégia foi iniciada!")
            return

        print("\n" + "=" * 80)
        print("ESTRATÉGIAS INICIADAS EM JANELAS SEPARADAS!")
        print("\nJANELA 1: BTC Strategy - Python btc_scalp_strategy.py")
        print("JANELA 2: XAU Strategy - Python xau_scalp_strategy.py")
        print("\nLOGs AUTOMÁTICOS:")
        print("• btc_scalp_strategy_YYYYMMDD_HHMMSS.log")
        print("• xau_scalp_strategy_YYYYMMDD_HHMMSS.log")
        print("\nPARAR INDIVIDUAL: Feche cada janela ou CTRL+C em cada uma")
        print("=" * 80)

        # Finalizar o launcher já que as janelas estão abertas
        print("Launcher finalizado - estratégias rodando independentemente")
        return

    except KeyboardInterrupt:
        print("\n[SIGNAL] Interrupção do usuário detectada...")
        stop_all(processes)
        print("\n" + "=" * 80)
        print("MULTI-SYMBOL SYSTEM ENCERRADO")
        print("=" * 80)

    except Exception as e:
        print("\n[ERROR] Erro no sistema principal: {}".format(e))
        stop_all(processes)

if __name__ == "__main__":
    main()

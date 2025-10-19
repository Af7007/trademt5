#!/usr/bin/env python3
"""
Script de teste para verificar se todas as dependências estão instaladas
"""
import sys
import os

# Adicionar diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_import(module_name):
    """Testa import de um módulo"""
    try:
        __import__(module_name)
        print(f"OK {module_name}")
        return True
    except ImportError as e:
        print(f"ERROR {module_name}: {e}")
        return False

def main():
    """Função principal de teste"""
    print("Testando imports do Bot MT5-MLP...\n")

    modules_to_test = [
        'MetaTrader5',
        'tensorflow',
        'pandas',
        'numpy',
        'flask',
        'sklearn',
        'dotenv'
    ]

    success_count = 0
    for module in modules_to_test:
        if test_import(module):
            success_count += 1

    print(f"\nResultado: {success_count}/{len(modules_to_test)} módulos OK")

    if success_count == len(modules_to_test):
        print("Todas as dependências estão instaladas!")
        return True
    else:
        print("Algumas dependências estão faltando")
        return False

if __name__ == "__main__":
    main()

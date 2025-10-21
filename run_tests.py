#!/usr/bin/env python3
"""
Script para executar os testes Flask-Testing
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description=""):
    """Executa comando e retorna resultado"""
    print(f"\n{'='*60}")
    print(f"Executando: {description}")
    print(f"Comando: {' '.join(cmd)}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')

        if result.stdout:
            print("STDOUT:")
            print(result.stdout)

        if result.stderr:
            print("STDERR:")
            print(result.stderr)

        return result.returncode == 0, result
    except Exception as e:
        print(f"Erro ao executar comando: {e}")
        return False, None


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description='Executar testes Flask-Testing')
    parser.add_argument('--coverage', action='store_true', help='Gerar relatório de cobertura')
    parser.add_argument('--unit', action='store_true', help='Apenas testes unitários')
    parser.add_argument('--integration', action='store_true', help='Apenas testes de integração')
    parser.add_argument('--api', action='store_true', help='Apenas testes de API')
    parser.add_argument('--mlp', action='store_true', help='Apenas testes MLP')
    parser.add_argument('--btc', action='store_true', help='Apenas testes BTC')
    parser.add_argument('--verbose', '-v', action='store_true', help='Modo verboso')
    parser.add_argument('--quick', action='store_true', help='Testes rápidos (sem cobertura)')

    args = parser.parse_args()

    # Verificar se está no diretório correto
    if not os.path.exists('app.py'):
        print("Erro: Execute este script a partir do diretório raiz do projeto")
        sys.exit(1)

    # Instalar dependências se necessário
    print("Verificando dependências...")
    success, _ = run_command([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', '--upgrade', '-r', 'requirements.txt'],
                           "Instalando dependências")
    if not success:
        print("Erro ao instalar dependências")
        sys.exit(1)

    # Construir comando pytest
    cmd = [sys.executable, '-m', 'pytest']

    if args.verbose:
        cmd.append('-v')

    # Adicionar opções de cobertura se necessário
    if args.coverage and not args.quick:
        cmd.extend([
            '--cov=app',
            '--cov-report=term-missing',
            '--cov-report=html:htmlcov',
            '--cov-fail-under=70'
        ])

    # Filtros de teste
    if args.unit:
        cmd.extend(['-m', 'unit'])
    elif args.integration:
        cmd.extend(['-m', 'integration'])
    elif args.api:
        cmd.extend(['-m', 'api'])
    elif args.mlp:
        cmd.extend(['-m', 'mlp'])
    elif args.btc:
        cmd.extend(['-m', 'btc'])

    # Executar testes
    print("Executando testes...")
    success, result = run_command(cmd, "Testes Flask-Testing")

    if success:
        print(f"\n{'='*60}")
        print("[SUCCESS] TESTES EXECUTADOS COM SUCESSO!")
        print(f"{'='*60}")

        if args.coverage and not args.quick:
            print("[COVERAGE] Relatório de cobertura gerado em: htmlcov/index.html")
            print("   Abra no navegador para visualizar detalhes")

        print("\n📋 Resumo dos testes:")
        if result and result.stdout:
            lines = result.stdout.strip().split('\n')
            for line in lines[-10:]:  # Últimas 10 linhas
                if any(keyword in line.lower() for keyword in ['passed', 'failed', 'error', 'warning']):
                    print(f"   {line}")

        return 0
    else:
        print(f"\n{'='*60}")
        print("[FAILURE] ALGUNS TESTES FALHARAM!")
        print(f"{'='*60}")

        if result and result.stdout:
            print("Detalhes dos erros:")
            print(result.stdout[-1000:])  # Últimos 1000 caracteres

        return 1


if __name__ == '__main__':
    sys.exit(main())

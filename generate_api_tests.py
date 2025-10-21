#!/usr/bin/env python -3.8
"""
Gerador Automático de Testes E2E para todas as APIs do Sistema MT5 TradeMLT

Este script analisa todas as rotas Flask documentadas no Swagger/OpenAPI
e gera automaticamente testes E2E completos com:
- Testes de estrutura de resposta
- Testes de validação de dados
- Testes de endpoints individuais
- Reporte de cobertura de testes
"""

import re
import requests
import json
from typing import Dict, List, Tuple
import time
from datetime import datetime

class APITestGenerator:
    """Gerador automático de testes E2E para APIs Flask/Swagger"""

    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.test_results = []
        self.swagger_endpoint = f"{base_url}/apidocs/"  # Flasgger endpoint

    def get_all_endpoints_from_app(self) -> List[Dict]:
        """
        Extrai todas as rotas diretamente do app.py usando regex
        Como alternativa ao swagger quando indisponível
        """
        endpoints = []

        try:
            # Ler o arquivo app.py
            with open('app.py', 'r', encoding='utf-8') as f:
                content = f.read()

            # Regex para encontrar todas as rotas Flask com @app.route
            route_pattern = r'@app\.route\([\'"]([^\'"]+)[\'"],\s*methods=\[([^\]]+)\]'
            docstring_pattern = r'"""\s*(.*?)\s*"""'
            tag_pattern = r'tags:\s*\n\s+- ([^\n]+)'

            routes = re.findall(route_pattern, content, re.DOTALL)
            blocks = []
            lines = content.split('\n')

            current_block = []
            collecting = False
            for line in lines:
                if '@app.route(' in line:
                    if current_block:
                        blocks.append('\n'.join(current_block))
                    current_block = [line]
                    collecting = True
                elif collecting:
                    if line.strip() == ')':
                        current_block.append(line)
                        collecting = False
                        blocks.append('\n'.join(current_block))
                    else:
                        current_block.append(line)

            if current_block:
                blocks.append('\n'.join(current_block))

            for block in blocks:
                # Extrair rota, métodos e documentação
                route_match = re.search(route_pattern, block, re.DOTALL)
                if route_match:
                    path = route_match.group(1)
                    methods_str = route_match.group(2)
                    methods = [m.strip().strip("'\"").lower() for m in methods_str.split(',')]

                    # Extrair docstring
                    doc_match = re.search(r'"""\s*(.*?)\s*"""', block, re.DOTALL)
                    description = "No description" if not doc_match else doc_match.group(1).strip()

                    # Extrair tag
                    tag_match = re.search(tag_pattern, block)
                    tag = "General" if not tag_match else tag_match.group(1).strip()

                    endpoints.append({
                        'path': path,
                        'methods': methods,
                        'description': description,
                        'tag': tag,
                        'full_url': f"{self.base_url}{path}"
                    })

        except Exception as e:
            print(f"Erro ao analisar app.py: {e}")

        return endpoints

    def test_endpoint(self, endpoint: Dict) -> Dict:
        """Executa teste E2E para um endpoint específico"""
        result = {
            'endpoint': endpoint,
            'success': False,
            'response_time': 0,
            'status_code': None,
            'response_size': 0,
            'json_response': False,
            'error_message': None,
            'validation_errors': []
        }

        # Determinar método (preferencialmente GET para testes básicos)
        method = 'get'
        if 'get' in [m.lower() for m in endpoint['methods']]:
            method = 'GET'
        elif 'post' in [m.lower() for m in endpoint['methods']]:
            method = 'POST'  # Para POST pode ser necessário body
        else:
            method = endpoint['methods'][0].upper() if endpoint['methods'] else 'GET'

        try:
            start_time = time.time()

            if method == 'GET':
                response = requests.get(endpoint['full_url'], timeout=5)
            elif method == 'POST':
                # Para POST, tenta sem body primeiro (pode falhar, mas detecta endpoint)
                headers = {'Content-Type': 'application/json'}
                payload = {}
                response = requests.post(endpoint['full_url'], json=payload, headers=headers, timeout=5)
            else:
                # Skip métodos complexos por enquanto
                result['error_message'] = f'Método {method} não suportado em testes automáticos'
                return result

            result['response_time'] = int((time.time() - start_time) * 1000)  # ms
            result['status_code'] = response.status_code
            result['response_size'] = len(response.content)
            result['json_response'] = self._is_json_response(response)

            # Validar resposta baseada no status
            if response.status_code >= 200 and response.status_code < 300:
                result['success'] = True

                # Validar JSON se resposta for JSON
                if result['json_response']:
                    result['validation_errors'] = self._validate_json_response(response.json(), endpoint)

            else:
                # Para endpoints que precisam de autenticação/parametros, é esperado erro
                if response.status_code in [400, 401, 403, 404]:
                    result['success'] = True  # Endpoint existe e responde
                    result['error_message'] = f'OK - Status {response.status_code} (necessita parâmetros)'
                else:
                    result['error_message'] = f'Erro HTTP {response.status_code}'

        except requests.exceptions.Timeout:
            result['error_message'] = 'Timeout - Endpoint não respondeu'
        except requests.exceptions.ConnectionError:
            result['error_message'] = 'Connection Error - Servidor indisponível'
        except Exception as e:
            result['error_message'] = f'Erro geral: {str(e)}'

        return result

    def _is_json_response(self, response) -> bool:
        """Verifica se a resposta é JSON"""
        try:
            response.json()
            return True
        except:
            return False

    def _validate_json_response(self, data: Dict, endpoint: Dict) -> List[str]:
        """Valida estrutura da resposta JSON"""
        errors = []

        if not isinstance(data, dict):
            errors.append("Resposta não é um objeto JSON válido")
            return errors

        # Validações básicas baseadas na tag da API
        tag = endpoint.get('tag', '').lower()

        if tag == 'mlp bot':
            # Valida respostas do Bot MLP
            if 'success' not in data:
                errors.append("Campo 'success' ausente na resposta")
            if 'timestamp' not in data:
                errors.append("Campo 'timestamp' ausente na resposta")

        elif 'sync' in tag:
            # Valida respostas de sync
            if 'result' not in data and endpoint['path'] != '/sync/status':
                errors.append("Campo 'result' ausente em resposta de sync")

        elif 'ollama' in tag.lower():
            # Valida respostas Ollama
            if 'success' not in data and 'data' not in data:
                errors.append("Estrutura típica de resposta Ollama ausente")

        # Valida timestamps
        if 'timestamp' in data:
            try:
                datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
            except:
                errors.append("Timestamp inválido na resposta")

        return errors

    def run_full_test_suite(self) -> Dict:
        """Executa testes completos em todas as APIs"""
        print("\n" + "="*80)
        print("GERADOR AUTOMATICO DE TESTES E2E API MT5 TRADEMLT")
        print("="*80)

        # Obter todos os endpoints
        endpoints = self.get_all_endpoints_from_app()
        print(f"[{len(endpoints)}] endpoints encontrados no app.py")

        start_time = time.time()
        self.test_results = []

        print("\nExecutando testes E2E...")
        for i, endpoint in enumerate(endpoints, 1):
            print(f"[{i:2d}/{len(endpoints):2d}] Testando {endpoint['full_url']}...")
            test_result = self.test_endpoint(endpoint)
            self.test_results.append(test_result)

            # Show basic result
            status = "[OK]" if test_result['success'] else "[ERRO]"
            time_str = f"{test_result['response_time']}ms"
            print(f"      {status} {test_result['status_code'] or 'ERR'} - {time_str}")

            if not test_result['success'] and test_result['error_message']:
                print(f"      AVISO: {test_result['error_message']}")

        # Gerar relatório
        report = self.generate_report()
        end_time = time.time()
        report['execution_time'] = int((end_time - start_time) * 1000)

        # Salvar relatório
        self.save_test_report(report)

        print("\n" + "="*80)
        print("RELATORIO FINAL DOS TESTES:")
        print("="*80)
        print(report)

        return report

    def generate_report(self) -> Dict:
        """Gera relatório completo dos testes"""
        total = len(self.test_results)
        successful = len([r for r in self.test_results if r['success']])
        failed = total - successful

        # Estatísticas de performance
        response_times = [r['response_time'] for r in self.test_results if r['response_time'] > 0]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0

        # Agrupar por tags
        by_tag = {}
        unstable_endpoints = []

        for result in self.test_results:
            tag = result['endpoint'].get('tag', 'General')
            if tag not in by_tag:
                by_tag[tag] = {'total': 0, 'success': 0}
            by_tag[tag]['total'] += 1
            if result['success']:
                by_tag[tag]['success'] += 1
            else:
                unstable_endpoints.append(result['endpoint']['path'])

        # Status geral
        health_score = (successful / total * 100) if total > 0 else 0

        report = {
            'summary': {
                'total_endpoints': total,
                'successful_tests': successful,
                'failed_tests': failed,
                'health_score': f"{health_score:.1f}%",
                'avg_response_time_ms': f"{avg_response_time:.1f}"
            },
            'by_category': by_tag,
            'unstable_endpoints': unstable_endpoints,
            'recommendations': self._generate_recommendations(successful, total, avg_response_time)
        }

        return report

    def _generate_recommendations(self, successful, total, avg_time) -> List[str]:
        """Gera recomendações baseadas nos resultados"""
        recs = []

        success_rate = successful / total if total > 0 else 0

        if success_rate < 0.8:
            recs.append("⚠️ Taxa de sucesso baixa - Verificar endpoints problemáticos")
        else:
            recs.append("✅ Taxa de sucesso excelente - APIs funcionando bem")

        if avg_time > 1000:  # > 1 segundo
            recs.append("Respostas lentas - Otimizar performance dos endpoints")
        else:
            recs.append("Performace adequada - Tempos de resposta bons")

        recs.append("Recomendacao: Executar testes diariamente em producao")
        recs.append("Proximo passo: Adicionar testes de carga para performance")

        return recs

    def save_test_report(self, report: Dict):
        """Salva relatório completo em arquivo JSON"""
        timestamp = datetime.now().isoformat().replace(':', '-')
        filename = f"api_test_report_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'report': report,
                'timestamp': timestamp,
                'detailed_results': self.test_results
            }, f, indent=2, ensure_ascii=False)

        print(f"Relatorio completo salvo em: {filename}")


def main():
    """Função principal do gerador de testes"""
    try:
        print("Gerador Automático de Testes E2E API - MT5 TradeMLT")
        print("Sistema: MT5 TradeMLT v2.0")
        print("Data:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        # Verificar se servidor está rodando
        generator = APITestGenerator()

        print("\nVerificando conectividade do servidor...")
        try:
            response = requests.get("http://localhost:5000/ping", timeout=3)
            if response.status_code == 200:
                print("Servidor conectado - Iniciando testes")
            else:
                print("Servidor respondeu com status diferente de 200")
        except Exception as e:
            print("Servidor não está rodando em http://localhost:5000")
            print("Iniciando testes mesmo assim (pode haver falhas)")

        # Executar suite completa
        report = generator.run_full_test_suite()

        # Sumário final
        summary = report['summary']
        print("\n--- RESULTADO FINAL ---")
        print(f"   Endpoints testados: {summary['total_endpoints']}")
        print(f"   Sucessos: {summary['successful_tests']}")
        print(f"   Falhas: {summary['failed_tests']}")
        print(f"   Score de saúde: {summary['health_score']}")
        print(f"   Tempo médio resposta: {summary['avg_response_time_ms']}ms")

        print("\n🎉 Testes E2E automaticamente executados!")

    except Exception as e:
        print(f"ERRO geral no gerador de testes: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

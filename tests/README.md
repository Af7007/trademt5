# Testes Flask-Testing - MT5 Trading Platform

Este diretório contém a estrutura completa de testes para a plataforma de trading MT5 usando Flask-Testing.

## 📁 Estrutura dos Testes

```
tests/
├── __init__.py              # Pacote de testes
├── conftest.py              # Configurações compartilhadas (fixtures)
├── README.md               # Esta documentação
├── test_app.py             # Testes básicos da aplicação
├── test_mlp_bot.py         # Testes específicos do bot MLP
└── test_btc_apis.py        # Testes das APIs BTC e mercado
```

## 🚀 Executando os Testes

### Instalação das Dependências

```bash
# Instalar dependências de teste
pip install -r requirements.txt

# Ou instalar apenas as dependências de teste
pip install pytest pytest-flask pytest-cov flask-testing responses
```

### Comandos Básicos

```bash
# Executar todos os testes
python run_tests.py

# Executar com relatório de cobertura
python run_tests.py --coverage

# Apenas testes unitários
python run_tests.py --unit

# Apenas testes de integração
python run_tests.py --integration

# Apenas testes de API
python run_tests.py --api

# Apenas testes MLP
python run_tests.py --mlp

# Apenas testes BTC
python run_tests.py --btc

# Modo verboso
python run_tests.py --verbose

# Testes rápidos (sem cobertura)
python run_tests.py --quick
```

### Usando pytest diretamente

```bash
# Todos os testes
pytest

# Com cobertura
pytest --cov=app --cov-report=html

# Apenas testes marcados como MLP
pytest -m mlp

# Apenas testes marcados como BTC
pytest -m btc

# Apenas testes marcados como API
pytest -m api

# Testes lentos (mais de 30 segundos)
pytest -m slow
```

## 🏷️ Marcadores de Teste

Os testes estão organizados com marcadores para facilitar a execução seletiva:

- `@pytest.mark.unit` - Testes unitários rápidos
- `@pytest.mark.integration` - Testes de integração
- `@pytest.mark.api` - Testes de API endpoints
- `@pytest.mark.mlp` - Testes específicos do bot MLP
- `@pytest.mark.mt5` - Testes que requerem conexão MT5
- `@pytest.mark.slow` - Testes que demoram mais de 30 segundos
- `@pytest.mark.btc` - Testes relacionados a dados BTC
- `@pytest.mark.ollama` - Testes que requerem Ollama AI

## 🔧 Fixtures Disponíveis

As fixtures estão definidas em `conftest.py`:

### `client`
Cliente de teste Flask configurado para testing.

### `mock_mt5`
Mock completo do MetaTrader5 para testes sem conexão real.

### `temp_db`
Banco de dados SQLite temporário para testes de integração.

### `sample_market_data`
Dados de mercado de exemplo para testes.

### `sample_mlp_analysis`
Análise MLP de exemplo para testes.

### `sample_trade`
Trade de exemplo para testes.

## 📋 Tipos de Teste Implementados

### 1. Testes Básicos da Aplicação (`test_app.py`)
- ✅ Testes de inicialização da aplicação
- ✅ Testes de endpoints básicos (ping, health)
- ✅ Testes de tratamento de erros
- ✅ Testes de documentação Swagger
- ✅ Testes de performance básicos
- ✅ Testes de headers CORS

### 2. Testes do Bot MLP (`test_mlp_bot.py`)
- ✅ Testes de todos os endpoints MLP (/mlp/* e /bot/*)
- ✅ Testes de validação de sinais (BUY, SELL, HOLD)
- ✅ Testes de tratamento de erro
- ✅ Testes de integração com banco de dados
- ✅ Testes de configuração do bot

### 3. Testes das APIs BTC (`test_btc_apis.py`)
- ✅ Testes de endpoints BTC (stats, indicators, analysis, candles)
- ✅ Testes de validação de dados de mercado
- ✅ Testes de tratamento de erro MT5
- ✅ Testes de cache e performance
- ✅ Testes de integração entre endpoints

## 🎯 Cobertura de Teste

### Objetivos de Cobertura:
- **Aplicação principal**: ≥ 80%
- **Serviços críticos**: ≥ 90%
- **APIs públicas**: ≥ 85%

### Arquivos Prioritários:
1. `app.py` - Arquivo principal da aplicação
2. `services/mlp_bot.py` - Serviço do bot MLP
3. `services/mlp_storage.py` - Storage do MLP
4. `bot/trading_engine.py` - Engine de trading
5. `routes/*.py` - Todas as rotas da API

## 🔍 Estratégias de Teste

### Testes Unitários
- Testar funções individuais isoladamente
- Usar mocks para dependências externas
- Testar validações de entrada
- Testar tratamento de erro

### Testes de Integração
- Testar interação entre componentes
- Testar fluxos completos
- Testar integração com banco de dados
- Testar APIs externas (MT5, etc.)

### Testes de API
- Testar todos os endpoints
- Testar códigos de status HTTP
- Testar formatos de resposta
- Testar validação de parâmetros
- Testar autenticação/autorização

## 🚨 Tratamento de Erros

### Cenários de Erro Testados:
- ❌ Conexão MT5 indisponível
- ❌ Banco de dados inacessível
- ❌ Parâmetros inválidos
- ❌ Sinais de trading inválidos
- ❌ Timeouts e timeouts
- ❌ Erros de rede
- ❌ Dados malformados

## 📊 Relatórios e Métricas

### Relatório de Cobertura
```bash
pytest --cov=app --cov-report=html
# Abre htmlcov/index.html no navegador
```

### Relatório de Testes
```bash
pytest --html=report.html --self-contained-html
# Abre report.html no navegador
```

### Métricas de Performance
- Tempo de resposta < 1s para endpoints básicos
- Tempo de resposta < 5s para endpoints complexos
- Suporte a múltiplas requisições simultâneas

## 🔧 Configuração de Desenvolvimento

### pytest.ini
Arquivo de configuração com:
- Caminhos de teste
- Marcadores personalizados
- Opções de cobertura
- Filtros de warning

### conftest.py
Fixtures compartilhadas:
- Configuração da aplicação de teste
- Mocks de serviços externos
- Dados de teste padronizados
- Cleanup automático

## 🚀 Boas Práticas

### Organização
- ✅ Um arquivo de teste por módulo principal
- ✅ Testes agrupados por funcionalidade
- ✅ Nomes descritivos de teste
- ✅ Documentação clara

### Manutenção
- ✅ Testes independentes entre si
- ✅ Setup e cleanup adequados
- ✅ Uso de fixtures para recursos compartilhados
- ✅ Mocks para dependências externas

### Performance
- ✅ Testes rápidos para desenvolvimento
- ✅ Testes marcados como slow para CI
- ✅ Paralelização quando possível
- ✅ Cleanup de recursos

## 🔮 Próximos Passos

### Melhorias Planejadas:
1. **Testes de Carga** - Testar com múltiplos usuários
2. **Testes de Segurança** - Validar autenticação/autorização
3. **Testes de WebSocket** - Testar conexões em tempo real
4. **Testes de Banco de Dados** - Testes mais avançados de persistência
5. **Testes de Monitoramento** - Health checks e métricas

### Ferramentas Adicionais:
- **pytest-benchmark** - Performance benchmarking
- **pytest-asyncio** - Testes assíncronos
- **pytest-mock** - Mocks avançados
- **factory-boy** - Factories para dados de teste

## 📞 Suporte

Para dúvidas sobre os testes:
1. Consulte esta documentação
2. Verifique os exemplos em `conftest.py`
3. Analise os testes existentes como referência
4. Execute testes específicos para debugar

## 🎉 Conclusão

Esta estrutura de testes fornece cobertura abrangente da plataforma MT5, garantindo:
- ✅ Qualidade do código
- ✅ Funcionalidades funcionando corretamente
- ✅ Regressões detectadas rapidamente
- ✅ Documentação viva dos requisitos
- ✅ Confiança para deploy em produção

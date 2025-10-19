# 🤖 Bot de Trading MT5 com MLP Neural Network

Um bot avançado de trading automatizado que utiliza redes neurais MLP (Multi-Layer Perceptron) para análise de mercado e execução de operações no MetaTrader 5.

## 🚀 Características

- **Modelo MLP Avançado**: Rede neural para predição de sinais de trading
- **Integração MT5 Completa**: Conexão nativa com MetaTrader 5
- **API REST**: Controle remoto via API HTTP
- **Análise Técnica**: Indicadores técnicos integrados (RSI, MACD, Bollinger, etc.)
- **Gerenciamento de Risco**: Stop Loss e Take Profit automáticos
- **Monitoramento em Tempo Real**: Acompanhamento de posições e performance
- **Logging Completo**: Sistema de logs detalhado
- **Treinamento Automático**: Modelo treinado com dados históricos

## 📁 Estrutura do Projeto

```
bot/
├── __init__.py              # Inicialização do pacote
├── config.py                # Configurações do bot
├── mlp_model.py             # Modelo de rede neural MLP
├── mt5_connector.py         # Conexão com MetaTrader 5
├── trading_engine.py        # Motor de execução de operações
├── api_controller.py        # API REST para controle remoto
├── main.py                  # Arquivo principal
├── requirements.txt         # Dependências Python
├── .env.example            # Exemplo de configuração
└── README.md               # Esta documentação
```

## 🛠️ Instalação

### 1. Pré-requisitos

- **Python 3.8+**
- **MetaTrader 5** instalado
- **Conta MT5** (demo ou real)

### 2. Dependências

```bash
# Instalar dependências
pip install -r bot/requirements.txt

# Ou instalar manualmente as principais
pip install MetaTrader5 tensorflow pandas numpy flask scikit-learn
```

### 3. Configuração

```bash
# Copiar arquivo de exemplo
cp bot/.env.example bot/.env

# Editar configurações
nano bot/.env
```

Configure especialmente:
- `MT5_LOGIN`: Seu número de conta MT5
- `MT5_PASSWORD`: Sua senha MT5
- `MT5_SERVER`: Servidor MT5 (ex: MetaQuotes-Demo)

## 🎯 Uso Básico

### Modo Treinamento

```bash
# Treinar modelo com 30 dias de dados
python -m bot.main train --days 30

# Treinar com mais dados históricos
python -m bot.main train --days 90
```

### Modo API

```bash
# Iniciar apenas API
python -m bot.main api --port 5002

# Com debug
python -m bot.main api --debug
```

### Modo Bot Completo

```bash
# Iniciar bot completo (API + Trading automático)
python -m bot.main bot --start-bot

# Especificar porta
python -m bot.main bot --port 5002 --start-bot
```

## 🌐 API Endpoints

### Status e Controle

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/health` | Verificar saúde da API |
| POST | `/bot/start` | Iniciar bot de trading |
| POST | `/bot/stop` | Parar bot de trading |
| GET | `/bot/status` | Status atual do bot |

### Execução de Operações

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/bot/execute` | Executar sinal de trading |
| POST | `/bot/analyze` | Análise automática e execução |
| POST | `/bot/train` | Treinar modelo |

### Dados e Monitoramento

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/bot/positions` | Posições abertas |
| GET | `/bot/performance` | Relatório de performance |
| GET | `/bot/market-data` | Dados de mercado |
| POST | `/bot/emergency-close` | Fechar todas as posições |

### Exemplo de Uso da API

```bash
# Executar sinal BUY
curl -X POST http://localhost:5002/bot/execute \
  -H "Content-Type: application/json" \
  -d '{"signal": "BUY", "confidence": 0.8}'

# Obter status
curl http://localhost:5002/bot/status

# Análise automática
curl -X POST http://localhost:5002/bot/analyze
```

## ⚙️ Configuração Avançada

### Arquivo de Configuração

```python
# bot/config.py
@dataclass
class TradingConfig:
    symbol: str = "BTCUSDc"           # Símbolo para operar
    lot_size: float = 0.01            # Tamanho do lote
    max_positions: int = 3            # Máximo de posições
    stop_loss_pips: int = 100         # Stop Loss em pips
    take_profit_pips: int = 200       # Take Profit em pips
    magic_number: int = 123456        # Número mágico para identificar ordens

@dataclass
class MLPConfig:
    hidden_layers: List[int] = [128, 64, 32]  # Arquitetura da rede
    learning_rate: float = 0.001              # Taxa de aprendizado
    epochs: int = 100                         # Épocas de treinamento
    batch_size: int = 32                      # Tamanho do batch
    sequence_length: int = 60                 # Candles para análise
```

### Variáveis de Ambiente

```bash
# Configurações MT5
MT5_PATH=C:\Program Files\MetaTrader 5\terminal64.exe
MT5_LOGIN=12345678
MT5_PASSWORD=sua_senha
MT5_SERVER=MetaQuotes-Demo

# Configurações de Trading
MT5_SYMBOL=BTCUSDc
MT5_LOT_SIZE=0.01
MT5_STOP_LOSS=100
MT5_TAKE_PROFIT=200

# Modelo MLP
MLP_LEARNING_RATE=0.001
MLP_EPOCHS=100

# API
API_PORT=5002

# Logging
LOG_LEVEL=INFO
```

## 📊 Indicadores Técnicos

O modelo utiliza os seguintes indicadores:

- **RSI** (Relative Strength Index)
- **MACD** (Moving Average Convergence Divergence)
- **Bandas de Bollinger**
- **Médias Móveis** (SMA 20, 50)
- **Williams %R**
- **Volume** e **Price Action**

## 🎛️ Sinais de Trading

O modelo gera 3 tipos de sinais:

- **BUY** (Compra): Modelo detecta oportunidade de alta
- **SELL** (Venda): Modelo detecta oportunidade de baixa
- **HOLD** (Aguardar): Condições neutras, não operar

## 📈 Gerenciamento de Risco

- **Stop Loss**: Proteção contra perdas (configurável em pips)
- **Take Profit**: Realização de lucros (configurável em pips)
- **Máximo de Posições**: Limite de operações simultâneas
- **Controle de Lote**: Tamanho fixo de posição
- **Magic Number**: Identificação única das ordens do bot

## 🔍 Monitoramento

### Logs

```bash
# Ver logs em tempo real
tail -f bot/logs/trading_bot.log

# Logs incluem:
# - Conexões MT5
# - Análises de mercado
# - Execução de operações
# - Erros e warnings
# - Performance metrics
```

### Status via API

```bash
# Status completo
curl http://localhost:5002/bot/status

# Resposta inclui:
{
  "is_running": true,
  "mt5_connected": true,
  "positions_count": 2,
  "positions": [...],
  "account_info": {...},
  "performance": {...}
}
```

## 🚨 Recursos de Emergência

### Fechar Todas as Posições

```bash
curl -X POST http://localhost:5002/bot/emergency-close
```

### Parar Bot

```bash
curl -X POST http://localhost:5002/bot/stop
```

## 🧪 Testes

```bash
# Testes unitários
python -m pytest bot/tests/

# Cobertura de testes
python -m pytest --cov=bot bot/tests/

# Teste de integração
python -m bot.main train --days 7  # Treino rápido para teste
```

## 🔧 Desenvolvimento

### Adicionar Novos Indicadores

1. Editar `bot/mlp_model.py`
2. Adicionar cálculo no `MarketDataPreprocessor`
3. Incluir na lista de features em `config.py`

### Modificar Arquitetura MLP

1. Ajustar `hidden_layers` em `config.py`
2. Modificar `build_model()` em `mlp_model.py`
3. Retreinar modelo

### Debugging

```python
import logging

# Habilitar debug
logging.getLogger().setLevel(logging.DEBUG)

# Logs detalhados do TensorFlow
logging.getLogger('tensorflow').setLevel(logging.DEBUG)
```

## 📋 Checklist de Setup

- [ ] Instalar MetaTrader 5
- [ ] Configurar conta MT5
- [ ] Instalar dependências Python
- [ ] Configurar `.env`
- [ ] Testar conexão MT5
- [ ] Treinar modelo inicial
- [ ] Iniciar bot em modo teste

## 🆘 Suporte

Para problemas comuns:

1. **Erro de conexão MT5**: Verificar credenciais e path
2. **Modelo não converge**: Ajustar learning rate ou arquitetura
3. **API não responde**: Verificar porta e firewall
4. **Baixa performance**: Aumentar dados de treinamento

## 📄 Licença

Este projeto é para fins educacionais e de pesquisa. Use por sua conta e risco.

---

**⚠️ Aviso**: Trading envolve riscos significativos. Este bot é uma ferramenta automatizada que pode resultar em perdas financeiras. Use apenas com contas demo inicialmente e monitore sempre as operações.

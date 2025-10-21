# 🔮 Motor de Predição de Trading MT5

## Visão Geral

O **Motor de Predição** é um módulo avançado que analisa dados reais do MetaTrader 5 para gerar predições inteligentes sobre operações de trading. Ele combina análise técnica, machine learning e estatísticas para prever:

- ✅ Número de operações necessárias para atingir um objetivo de lucro
- ⏱️ Tempo estimado para alcançar a meta
- 📊 Melhores momentos para entrar no mercado
- 💰 Gestão de risco otimizada
- 🎯 Recomendações específicas de trades

## Características Principais

### 🎯 Análise Inteligente
- Coleta de dados em tempo real do MT5
- Análise de múltiplos indicadores técnicos (RSI, MACD, Bollinger Bands, ATR)
- Identificação automática de tendências e padrões
- Análise de suporte e resistência
- Avaliação de volatilidade do mercado

### 💡 Predições Precisas
- Estimativa de operações necessárias
- Cálculo de probabilidade de sucesso
- Previsão de tempo para atingir objetivos
- Identificação dos melhores timeframes
- Recomendações baseadas em dados históricos

### ⚙️ Configuração Flexível
- Suporte para qualquer símbolo do MT5
- Configuração de timeframes (M1 a D1)
- Parâmetros personalizáveis (lote, TP, SL)
- Gerenciamento de risco ajustável
- Limites de operações opcionais

### 🏆 Otimizado para Exness
- Consideração de spreads baixos da Exness
- Sem comissões em muitas contas
- Ideal para scalping e day trading
- Aproveitamento das melhores condições de mercado

## Estrutura do Módulo

```
prediction/
├── __init__.py                  # Exportações do módulo
├── data_collector.py            # Coleta de dados do MT5
├── prediction_engine.py         # Motor principal de predição
├── prediction_helpers.py        # Funções auxiliares
└── models.py                    # Modelos de dados
```

## Como Usar

### 1. API REST

#### Endpoint Principal: `/prediction/analyze`

**Exemplo de Requisição:**

```json
{
  "symbol": "XAUUSDc",
  "target_profit": 30.0,
  "balance": 1000.0,
  "timeframe": "M1",
  "risk_percentage": 2.0
}
```

**Parâmetros:**

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `symbol` | string | ✅ | Símbolo do ativo (ex: XAUUSDc, BTCUSDc) |
| `target_profit` | float | ✅ | Lucro alvo em USD |
| `balance` | float | ✅ | Banca disponível em USD |
| `timeframe` | string | ❌ | Timeframe (M1, M5, M15, H1, H4, D1) |
| `lot_size` | float | ❌ | Tamanho do lote (auto se não informado) |
| `take_profit` | float | ❌ | TP em pontos (auto se não informado) |
| `stop_loss` | float | ❌ | SL em pontos (auto se não informado) |
| `max_operations` | int | ❌ | Limite de operações |
| `risk_percentage` | float | ❌ | % de risco por operação (padrão: 2.0) |

**Resposta de Sucesso:**

```json
{
  "success": true,
  "result": {
    "predictions": {
      "estimated_operations": 5,
      "estimated_duration_hours": 2.5,
      "estimated_duration_description": "Aproximadamente 2 horas",
      "success_probability": 0.72
    },
    "recommended_trades": [
      {
        "direction": "BUY",
        "entry_price": 2645.80,
        "stop_loss": 2644.30,
        "take_profit": 2648.80,
        "lot_size": 0.01,
        "confidence": 0.75,
        "expected_profit": 30.0,
        "expected_loss": 15.0,
        "risk_reward_ratio": 2.0,
        "reasoning": "RSI em zona de sobrevenda. MACD com histograma positivo. Tendência de alta identificada."
      }
    ],
    "market_analysis": {
      "trend": {
        "direction": "BULLISH",
        "strength": 0.8
      },
      "volatility": {
        "level": "NORMAL",
        "atr": 1.5
      }
    },
    "timing": {
      "best_entry_times": ["09:00", "14:00", "20:00"],
      "best_timeframe": "M1"
    },
    "risk_management": {
      "total_risk": 20.0,
      "max_drawdown": 40.0,
      "risk_level": "MEDIUM"
    },
    "warnings": [
      "⚠️ Alta volatilidade detectada - stops mais largos recomendados"
    ],
    "recommendations": [
      "✓ Use sempre stop loss em todas as operações",
      "✓ Não arrisque mais que 2% da banca por operação"
    ]
  }
}
```

### 2. Interface Web

Acesse a interface gráfica em: **http://localhost:5000/prediction/dashboard**

A interface oferece:
- 📝 Formulário interativo para configuração
- 📊 Visualização detalhada dos resultados
- 📈 Gráficos e métricas em tempo real
- ⚡ Predições rápidas e intuitivas

### 3. Outros Endpoints

#### Análise de Mercado
```
GET /prediction/market-analysis/{symbol}?timeframe=M1
```

Retorna análise completa do mercado para um símbolo específico.

#### Informações do Símbolo
```
GET /prediction/symbol-info/{symbol}
```

Retorna informações detalhadas sobre o símbolo (spreads, lotes, etc).

#### Predição Rápida
```
POST /prediction/quick-prediction
```

Versão simplificada que requer apenas `symbol` e `target_profit`.

#### Exemplos
```
GET /prediction/examples
```

Retorna exemplos de requisições prontos para uso.

## Exemplos de Uso

### Exemplo 1: Predição Básica para XAUUSDc

**Objetivo:** Ganhar $30 com banca de $1000

```bash
curl -X POST http://localhost:5000/prediction/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "XAUUSDc",
    "target_profit": 30,
    "balance": 1000,
    "timeframe": "M1"
  }'
```

### Exemplo 2: Predição Avançada com Parâmetros Customizados

```bash
curl -X POST http://localhost:5000/prediction/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "XAUUSDc",
    "target_profit": 50,
    "balance": 2000,
    "timeframe": "M5",
    "lot_size": 0.02,
    "take_profit": 150,
    "stop_loss": 75,
    "max_operations": 20,
    "risk_percentage": 1.5
  }'
```

### Exemplo 3: Python

```python
import requests
import json

# Configurar predição
data = {
    "symbol": "XAUUSDc",
    "target_profit": 30.0,
    "balance": 1000.0,
    "timeframe": "M1",
    "risk_percentage": 2.0
}

# Fazer requisição
response = requests.post(
    'http://localhost:5000/prediction/analyze',
    json=data
)

# Processar resultado
result = response.json()
if result['success']:
    prediction = result['result']
    print(f"Operações estimadas: {prediction['predictions']['estimated_operations']}")
    print(f"Tempo estimado: {prediction['predictions']['estimated_duration_description']}")
    print(f"Probabilidade de sucesso: {prediction['predictions']['success_probability'] * 100:.1f}%")
    
    if prediction['recommended_trades']:
        trade = prediction['recommended_trades'][0]
        print(f"\nRecomendação: {trade['direction']} a {trade['entry_price']}")
        print(f"TP: {trade['take_profit']} | SL: {trade['stop_loss']}")
        print(f"Confiança: {trade['confidence'] * 100:.1f}%")
```

## Indicadores Técnicos Utilizados

### Médias Móveis
- **SMA 20, 50, 200**: Identificação de tendência
- **EMA 12, 26**: Cálculo do MACD

### Osciladores
- **RSI (14)**: Sobrecompra/sobrevenda
- **MACD**: Momentum e cruzamentos

### Volatilidade
- **ATR (14)**: Average True Range
- **Bollinger Bands (20, 2)**: Amplitude de preço

### Volume
- **Volume Ratio**: Análise de atividade
- **Volume SMA**: Média de volume

## Gestão de Risco

O motor implementa práticas robustas de gestão de risco:

1. **Cálculo Automático de Lote**: Baseado na % de risco desejada
2. **Stop Loss Dinâmico**: Ajustado pela volatilidade (ATR)
3. **Take Profit Otimizado**: Risk/Reward ratio de 2:1 ou melhor
4. **Máximo Drawdown**: Estimativa conservadora
5. **Avisos de Risco**: Alertas em condições adversas

## Considerações Exness

O módulo foi otimizado para a corretora Exness:

- ✅ Spreads 30% menores considerados
- ✅ Sem comissões na maioria das contas
- ✅ Ideal para estratégias de scalping
- ✅ Suporte para micro-lotes (0.01)

## Limitações e Avisos

⚠️ **Importante:**

1. **Não é garantia de lucro**: Predições são baseadas em probabilidades
2. **Mercado é volátil**: Condições podem mudar rapidamente
3. **Use sempre stop loss**: Proteja seu capital
4. **Teste em demo primeiro**: Valide a estratégia antes de operar real
5. **Gestão de risco é essencial**: Nunca arrisque mais que 2% por operação

## Requisitos do Sistema

- Python 3.8+
- MetaTrader 5 instalado e em execução
- Conexão estável com a internet
- Conta MT5 configurada

## Troubleshooting

### Erro: "Símbolo não encontrado"
- Verifique se o símbolo está disponível no seu MT5
- Use o nome exato do símbolo (case-sensitive)
- Certifique-se que o MT5 está conectado

### Erro: "MT5 não está conectado"
- Abra o MetaTrader 5
- Faça login na sua conta
- Verifique a conexão com o servidor

### Predições inconsistentes
- Aguarde dados suficientes (mínimo 1000 barras)
- Verifique se há liquidez no símbolo
- Considere usar timeframes maiores

## Suporte

Para questões ou sugestões:
- 📧 Email: suporte@exemplo.com
- 📖 Documentação completa: [Link]
- 🐛 Issues: [GitHub]

## Licença

Propriedade privada. Todos os direitos reservados.

---

**Desenvolvido com ❤️ para traders que buscam vantagem competitiva no mercado.**

# 🤖 Trading Automático - Guia Completo

## ✅ Sistema Implementado!

O sistema agora suporta **execução automática de trades** baseada nas análises MLP.

## 📋 Configuração do Bot

### Estrutura Completa

```json
{
  "symbol": "BTCUSDc",
  "timeframe": "M1",
  "lot_size": 0.01,
  "take_profit": 5000,
  "stop_loss": 10000,
  "max_positions": 1,
  "confidence_threshold": 0.70,
  
  "trading": {
    "enabled": true,
    "auto_execute": true,
    "max_daily_trades": 10
  },
  
  "signals": {
    "min_confidence": 0.70,
    "rsi_oversold": 30,
    "rsi_overbought": 70
  },
  
  "advanced": {
    "magic_number": 123456,
    "deviation": 10
  }
}
```

## 🎯 Parâmetros Principais

### Básicos
- **symbol**: Símbolo a operar (BTCUSDc, XAUUSDc, etc.)
- **timeframe**: Timeframe (M1, M5, M15, etc.)
- **lot_size**: Tamanho do lote (0.01 = 1 micro lote)
- **take_profit**: Take Profit em pips
- **stop_loss**: Stop Loss em pips
- **max_positions**: Máximo de posições simultâneas

### Trading
- **enabled**: Habilita/desabilita trading
- **auto_execute**: Executa trades automaticamente
- **max_daily_trades**: Limite de trades por dia

### Signals
- **min_confidence**: Confiança mínima para executar (0.0 a 1.0)
- **rsi_oversold**: RSI considerado sobrevendido (padrão: 30)
- **rsi_overbought**: RSI considerado sobrecomprado (padrão: 70)

### Advanced
- **magic_number**: Número mágico para identificar ordens
- **deviation**: Desvio máximo de preço permitido

## 🚀 Como Usar

### 1. Modo Análise (Sem Executar)

```json
{
  "symbol": "BTCUSDc",
  "lot_size": 0.01,
  "take_profit": 5000,
  "stop_loss": 10000,
  "trading": {
    "enabled": false,
    "auto_execute": false
  }
}
```

**Resultado**: Bot apenas analisa e mostra sinais, não executa trades.

### 2. Modo Trading Automático

```json
{
  "symbol": "BTCUSDc",
  "lot_size": 0.01,
  "take_profit": 5000,
  "stop_loss": 10000,
  "trading": {
    "enabled": true,
    "auto_execute": true
  },
  "signals": {
    "min_confidence": 0.70
  }
}
```

**Resultado**: Bot executa trades automaticamente quando:
- Sinal é BUY ou SELL (não HOLD)
- Confiança >= 0.70
- Não tem posições abertas (ou < max_positions)

## 📊 Lógica de Execução

### Condições para Executar Trade

1. ✅ **auto_execute = true**
2. ✅ **Sinal = BUY ou SELL** (não HOLD)
3. ✅ **Confiança >= min_confidence**
4. ✅ **Posições abertas < max_positions**

### Exemplo Prático

**Análise Gerada**:
- RSI: 75.2
- Sinal: SELL
- Confiança: 85%

**Config**:
```json
{
  "trading": {"auto_execute": true},
  "signals": {"min_confidence": 0.70},
  "max_positions": 1
}
```

**Resultado**: ✅ Trade executado (85% >= 70% e sem posições abertas)

## 🎯 Templates Prontos

### Template 1: Análise Apenas
```json
{
  "symbol": "BTCUSDc",
  "lot_size": 0.01,
  "take_profit": 5000,
  "stop_loss": 10000,
  "trading": {"auto_execute": false}
}
```

### Template 2: Trading Conservador
```json
{
  "symbol": "XAUUSDc",
  "lot_size": 0.01,
  "take_profit": 500,
  "stop_loss": 1000,
  "max_positions": 1,
  "trading": {
    "auto_execute": true,
    "max_daily_trades": 5
  },
  "signals": {
    "min_confidence": 0.80
  }
}
```

### Template 3: Trading Agressivo
```json
{
  "symbol": "BTCUSDc",
  "lot_size": 0.02,
  "take_profit": 3000,
  "stop_loss": 5000,
  "max_positions": 3,
  "trading": {
    "auto_execute": true,
    "max_daily_trades": 20
  },
  "signals": {
    "min_confidence": 0.60
  }
}
```

## 📝 Logs de Execução

Quando um trade é executado, você verá nos logs:

```
Bot abc123: Enviando ordem SELL para BTCUSDc @ 110702.91
  Lote: 0.01, TP: 110202.91, SL: 111702.91
Bot abc123: ✓ Ordem executada! Ticket: 123456789
  Volume: 0.01, Preço: 110702.91
```

## ⚠️ Avisos Importantes

### Segurança
1. **Teste primeiro em conta demo**
2. **Comece com lotes pequenos** (0.01)
3. **Use stop loss sempre**
4. **Monitore regularmente**

### Riscos
- Trading automático pode gerar perdas
- Sempre use gerenciamento de risco
- Não arrisque mais do que pode perder
- Monitore o bot regularmente

### Recomendações
- **Lote inicial**: 0.01 (micro lote)
- **Max positions**: 1 (para começar)
- **Min confidence**: 0.70 ou maior
- **Stop loss**: Sempre configurado

## 🔧 Troubleshooting

### Trade não executou
**Possíveis causas**:
1. `auto_execute = false`
2. Confiança < min_confidence
3. Já tem max_positions abertas
4. Sinal é HOLD
5. Saldo insuficiente

**Solução**: Verificar logs do servidor para mensagens como:
```
Bot abc: Confiança 0.65 < 0.70, trade ignorado
Bot abc: Já tem 1 posições abertas (max: 1)
```

### Erro ao executar ordem
**Possíveis causas**:
1. Mercado fechado
2. Símbolo não disponível
3. Lote inválido
4. Margem insuficiente

**Solução**: Verificar logs para retcode e mensagem de erro.

## 📊 Monitoramento

### Console do Servidor
Monitore o console Flask para ver:
- Análises geradas
- Trades executados
- Erros e avisos

### Interface Web
- **Active Bots**: Mostra bots rodando
- **MLP Analysis**: Mostra sinais gerados
- **Positions**: Mostra posições abertas (em breve)
- **Trades**: Mostra histórico de trades (em breve)

## 🎉 Pronto para Usar!

Agora você tem um sistema completo de trading automático com:
- ✅ Análise MLP em tempo real
- ✅ Sinais BUY/SELL/HOLD
- ✅ Execução automática configurável
- ✅ Gerenciamento de risco
- ✅ Múltiplos bots simultâneos
- ✅ Configuração flexível

**Comece com modo análise, depois ative trading automático!** 🚀

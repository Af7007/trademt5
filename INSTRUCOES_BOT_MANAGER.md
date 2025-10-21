# 🤖 BOT MANAGER - Sistema de Gerenciamento de Bots

## 🚀 Como Usar

### 1. Acessar a Interface

Abra seu navegador e acesse:
```
http://localhost:5000/bot-manager
```

### 2. Criar um Bot

**Opção A - Usar Template:**
1. Clique em "Template BTC" ou "Template XAU"
2. O JSON será preenchido automaticamente
3. Clique em "INICIAR BOT"

**Opção B - Configuração Manual:**
1. Cole o JSON de configuração no campo de texto
2. Clique em "Validar JSON" para verificar
3. Clique em "INICIAR BOT"

### 3. Monitorar Bots

A lista de bots atualiza automaticamente a cada 2 segundos mostrando:
- Status (Running/Stopped)
- Símbolo e Timeframe
- TP/SL configurados
- Posições abertas
- Total de trades
- Profit total
- Win rate
- Uptime

### 4. Parar um Bot

Na linha do bot ativo, você tem 2 opções:

**⬛ PARAR BOT**
- Para o bot normalmente
- Aguarda fechamento de posições

**🚨 EMERGÊNCIA**
- Fecha TODAS as posições imediatamente
- Para o bot instantaneamente

## 📋 Configurações Disponíveis

### Template BTC (Bitcoin)
```json
{
  "symbol": "BTCUSDc",
  "timeframe": "M1",
  "lot_size": 0.01,
  "take_profit": 5000,
  "stop_loss": 10000,
  "confidence_threshold": 0.65,
  "max_positions": 1,
  "auto_trading_enabled": true
}
```

### Template XAU (Ouro)
```json
{
  "symbol": "XAUUSDc",
  "timeframe": "M1",
  "lot_size": 0.01,
  "take_profit": 500,
  "stop_loss": 1000,
  "confidence_threshold": 0.65,
  "max_positions": 1,
  "auto_trading_enabled": true
}
```

## 🔧 Parâmetros Explicados

| Parâmetro | Descrição | Exemplo |
|-----------|-----------|---------|
| `symbol` | Símbolo a operar | "BTCUSDc", "XAUUSDc" |
| `timeframe` | Período do gráfico | "M1", "M5", "M15" |
| `lot_size` | Tamanho do lote | 0.01 |
| `take_profit` | TP em pontos | 5000 (BTC), 500 (XAU) |
| `stop_loss` | SL em pontos | 10000 (BTC), 1000 (XAU) |
| `confidence_threshold` | Threshold de confiança | 0.65 (65%) |
| `max_positions` | Máximo de posições simultâneas | 1 |
| `auto_trading_enabled` | Trading automático | true/false |

## 📊 Valores para $0.50 de Lucro (0.01 lote)

### BTCUSDc
- **TP**: 5000 pontos = 50.0 em preço = ~$0.50
- **SL**: 10000 pontos = 100.0 em preço = ~$1.00

### XAUUSDc
- **TP**: 500 pontos = 0.5 em preço = ~$0.50
- **SL**: 1000 pontos = 1.0 em preço = ~$1.00

## 🎯 Funcionalidades

### ✅ Implementado
- ✅ Campo JSON para configuração
- ✅ Templates pré-configurados (BTC/XAU)
- ✅ Validação de JSON
- ✅ Botão de iniciar bot
- ✅ Lista de bots ativos em tempo real
- ✅ Botão de parar bot na linha do bot
- ✅ Botão de emergência
- ✅ Auto-refresh a cada 2 segundos
- ✅ Logs do sistema em tempo real
- ✅ Exibição de métricas (trades, profit, win rate)

### 🎨 Design
- Interface minimalista estilo terminal
- Foco em funcionalidade e confiabilidade
- Cores: Verde (#00ff00) para sucesso, Vermelho para perigo
- Fonte monoespaçada para melhor legibilidade de dados

## 🔄 Fluxo de Operação

1. **Configurar** → Cole JSON ou use template
2. **Validar** → Verifica se JSON está correto
3. **Iniciar** → Bot começa a operar
4. **Monitorar** → Acompanha em tempo real
5. **Parar** → Encerra operação quando necessário

## 🚨 Parada de Emergência

Quando acionar a parada de emergência:
1. Todas as posições abertas são fechadas imediatamente
2. O bot é parado
3. Não aguarda condições de mercado
4. Use apenas em situações críticas

## 📝 Logs

Os logs mostram:
- ✅ Ações bem-sucedidas (verde)
- ⚠️ Avisos (amarelo)
- ❌ Erros (vermelho)
- ℹ️ Informações (azul)

Mantém os últimos 50 eventos.

## 🔗 Endpoints Utilizados

- `POST /mlp/config` - Configurar bot
- `POST /mlp/start` - Iniciar bot
- `POST /mlp/stop` - Parar bot
- `POST /mlp/emergency-close` - Parada de emergência
- `GET /mlp/status` - Status do bot

## ⚡ Dicas

1. **Sempre valide o JSON** antes de iniciar
2. **Use templates** para configurações testadas
3. **Monitore os logs** para identificar problemas
4. **Parada normal** é preferível à emergência
5. **Um bot por vez** para melhor controle

## 🛠️ Troubleshooting

### Bot não inicia
- Verifique se o JSON está válido
- Confirme que o MT5 está conectado
- Veja os logs para detalhes do erro

### Bot não para
- Use a parada de emergência
- Verifique se há posições abertas
- Reinicie o servidor se necessário

### Dados não atualizam
- Verifique a conexão com o servidor
- Recarregue a página
- Confirme que o servidor Flask está rodando

## 📞 Suporte

Em caso de problemas:
1. Verifique os logs do sistema
2. Confirme status do MT5
3. Reinicie o servidor: `.\start_final.cmd`

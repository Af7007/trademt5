# 🤖 MULTI-BOT MANAGER - Sistema de Múltiplos Bots

## 🎯 Visão Geral

Sistema completo para gerenciar **múltiplos bots simultaneamente**, cada um operando um símbolo diferente de forma independente.

## 🚀 Acesso

```
http://localhost:5000/multi-bot-manager
```

Ou execute:
```bash
python abrir_multi_bot_manager.py
```

## ✨ Funcionalidades

### ✅ Múltiplos Bots Simultâneos
- Crie quantos bots quiser
- Cada bot opera independentemente
- Símbolos diferentes (BTC, XAU, EUR, etc.)
- Configurações individuais por bot

### ✅ Controle Individual
- Iniciar/Parar cada bot separadamente
- Remover bots específicos
- Monitorar performance individual
- Configurações únicas por bot

### ✅ Estatísticas Consolidadas
- Total de bots ativos
- Posições abertas (todos os bots)
- Total de trades executados
- Dashboard em tempo real

### ✅ Parada de Emergência
- Botão para parar TODOS os bots
- Fecha todas as posições
- Ação imediata

## 📋 Como Usar

### 1. Criar Primeiro Bot (BTC)
```
1. Clique em "Template BTC"
2. Clique em "CRIAR E INICIAR BOT"
3. Bot aparece na lista como "BOT #xxxx - BTCUSDc"
```

### 2. Criar Segundo Bot (XAU)
```
1. Clique em "Template XAU"
2. Clique em "CRIAR E INICIAR BOT"
3. Segundo bot aparece na lista como "BOT #yyyy - XAUUSDc"
```

### 3. Criar Mais Bots
```
1. Configure JSON manualmente ou use template
2. Clique em "CRIAR E INICIAR BOT"
3. Repita quantas vezes quiser
```

### 4. Gerenciar Bots
Cada bot na lista tem:
- **▶ INICIAR**: Se estiver parado
- **⬛ PARAR**: Se estiver rodando
- **🗑 REMOVER**: Deleta o bot

## 🎨 Interface

### Barra de Estatísticas
```
┌─────────────┬─────────────┬─────────────┬─────────────┐
│ TOTAL BOTS  │   ATIVOS    │  POSIÇÕES   │   TRADES    │
│      3      │      2      │      1      │     15      │
└─────────────┴─────────────┴─────────────┴─────────────┘
```

### Lista de Bots
```
BOT #a1b2 - BTCUSDc                    ● RUNNING
Symbol: BTCUSDc    TP: 5000 pts    Positions: 1
Timeframe: M1      SL: 10000 pts   Trades: 5
[⬛ PARAR] [🗑 REMOVER]

BOT #c3d4 - XAUUSDc                    ● RUNNING
Symbol: XAUUSDc    TP: 500 pts     Positions: 0
Timeframe: M1      SL: 1000 pts    Trades: 3
[⬛ PARAR] [🗑 REMOVER]

BOT #e5f6 - BTCUSDc                    ○ STOPPED
Symbol: BTCUSDc    TP: 5000 pts    Positions: 0
Timeframe: M1      SL: 10000 pts    Trades: 7
[▶ INICIAR] [🗑 REMOVER]
```

## 🔧 Arquitetura

### Backend

**Serviço**: `services/bot_manager_service.py`
- Classe `BotManagerService`: Gerencia múltiplos bots
- Classe `BotInstance`: Representa cada bot
- Thread-safe com Lock
- UUID único para cada bot

**Rotas**: `routes/bot_manager_routes.py`
- `GET /bots` - Lista todos os bots
- `GET /bots/active` - Lista bots ativos
- `POST /bots/create` - Cria novo bot
- `GET /bots/<id>` - Detalhes de um bot
- `POST /bots/<id>/start` - Inicia bot
- `POST /bots/<id>/stop` - Para bot
- `DELETE /bots/<id>/delete` - Remove bot
- `POST /bots/emergency-stop-all` - Para todos

### Frontend

**Interface**: `templates/bot_manager_multi.html`
- Auto-refresh a cada 2 segundos
- Estatísticas consolidadas
- Controle individual de cada bot
- Logs em tempo real

## 📊 Endpoints API

### Listar Todos os Bots
```bash
GET /bots
```
Resposta:
```json
{
  "success": true,
  "bots": [
    {
      "bot_id": "a1b2c3d4",
      "config": {...},
      "is_running": true,
      "uptime": "0:05:23",
      "positions_count": 1
    }
  ],
  "total": 2
}
```

### Criar Bot
```bash
POST /bots/create
Content-Type: application/json

{
  "symbol": "BTCUSDc",
  "timeframe": "M1",
  "lot_size": 0.01,
  "take_profit": 5000,
  "stop_loss": 10000,
  "confidence_threshold": 0.65,
  "max_positions": 1
}
```

### Parar Bot
```bash
POST /bots/{bot_id}/stop
```

### Remover Bot
```bash
DELETE /bots/{bot_id}/delete
```

## 🎯 Casos de Uso

### Caso 1: Diversificação
```
Bot 1: BTCUSDc (Crypto)
Bot 2: XAUUSDc (Commodity)
Bot 3: EURUSD (Forex)
```
**Benefício**: Diversificação de ativos

### Caso 2: Múltiplas Estratégias
```
Bot 1: BTCUSDc - TP 5000, Agressivo
Bot 2: BTCUSDc - TP 2000, Conservador
Bot 3: BTCUSDc - TP 10000, Long-term
```
**Benefício**: Testar estratégias diferentes

### Caso 3: Timeframes Diferentes
```
Bot 1: BTCUSDc M1 - Scalping
Bot 2: BTCUSDc M5 - Day trade
Bot 3: BTCUSDc M15 - Swing
```
**Benefício**: Operar em múltiplos timeframes

## ⚠️ Limitações e Cuidados

### Recursos do Sistema
- Cada bot consome memória e CPU
- Recomendado: Máximo 5-10 bots simultâneos
- Monitorar uso de recursos

### Margem e Saldo
- Cada bot pode abrir posições
- Verificar margem disponível
- Evitar overtrading

### Conexão MT5
- Todos os bots usam a mesma conexão MT5
- Se MT5 desconectar, todos os bots param
- Manter MT5 estável

## 🔄 Diferenças vs Single Bot

| Recurso | Single Bot | Multi-Bot |
|---------|-----------|-----------|
| Bots simultâneos | 1 | Ilimitado |
| Símbolos diferentes | Não | Sim |
| Controle individual | N/A | Sim |
| Estatísticas consolidadas | N/A | Sim |
| Complexidade | Simples | Moderada |
| Uso de recursos | Baixo | Médio/Alto |

## 🚀 Migração do Single Bot

Se você estava usando o single bot (`/bot-manager`):

1. **Acesse a nova interface**: `/multi-bot-manager`
2. **Crie seus bots**: Use os mesmos templates
3. **Benefícios adicionais**: 
   - Múltiplos símbolos
   - Controle individual
   - Estatísticas consolidadas

**Nota**: O single bot ainda está disponível em `/bot-manager` para compatibilidade.

## 📝 Exemplo Prático

### Criar 3 Bots Diferentes

**Bot 1 - BTC Agressivo**:
```json
{
  "symbol": "BTCUSDc",
  "lot_size": 0.01,
  "take_profit": 5000,
  "stop_loss": 10000
}
```

**Bot 2 - XAU Conservador**:
```json
{
  "symbol": "XAUUSDc",
  "lot_size": 0.01,
  "take_profit": 500,
  "stop_loss": 1000
}
```

**Bot 3 - BTC Long-term**:
```json
{
  "symbol": "BTCUSDc",
  "lot_size": 0.02,
  "take_profit": 10000,
  "stop_loss": 20000
}
```

## ✅ Checklist de Uso

### Antes de Criar Bots
- [ ] Servidor Flask rodando
- [ ] MT5 conectado
- [ ] Saldo suficiente
- [ ] Margem disponível

### Ao Criar Cada Bot
- [ ] Configuração validada
- [ ] Símbolo disponível no MT5
- [ ] TP/SL adequados
- [ ] Lote apropriado

### Durante Operação
- [ ] Monitorar estatísticas
- [ ] Verificar margem
- [ ] Acompanhar logs
- [ ] Observar performance

### Ao Encerrar
- [ ] Parar bots individualmente
- [ ] Ou usar parada de emergência
- [ ] Verificar posições fechadas
- [ ] Remover bots não utilizados

## 🎉 Sistema Pronto!

O Multi-Bot Manager está **100% funcional** e pronto para gerenciar múltiplos bots simultaneamente!

**Acesse agora**: http://localhost:5000/multi-bot-manager

**Recursos**:
- ✅ Múltiplos bots simultâneos
- ✅ Controle individual
- ✅ Estatísticas consolidadas
- ✅ Parada de emergência
- ✅ Interface em tempo real
- ✅ Logs detalhados

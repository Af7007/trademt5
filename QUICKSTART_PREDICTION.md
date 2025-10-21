# 🚀 Início Rápido - Motor de Predição

## Passo 1: Iniciar o Servidor

```bash
python app.py
```

O servidor estará disponível em: `http://localhost:5000`

## Passo 2: Acessar a Interface Web

Abra seu navegador e acesse:

```
http://localhost:5000/prediction/dashboard
```

## Passo 3: Fazer sua Primeira Predição

### Opção A: Interface Web (Recomendado)

1. Selecione o **Símbolo** (ex: XAUUSDc)
2. Defina o **Lucro Alvo** (ex: $30)
3. Informe sua **Banca** (ex: $1000)
4. Escolha o **Timeframe** (ex: M1)
5. Clique em **"Gerar Predição"**

### Opção B: Via API (cURL)

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

### Opção C: Python Script

```python
import requests

response = requests.post('http://localhost:5000/prediction/analyze', json={
    "symbol": "XAUUSDc",
    "target_profit": 30,
    "balance": 1000,
    "timeframe": "M1"
})

result = response.json()
print(f"Operações necessárias: {result['result']['predictions']['estimated_operations']}")
```

### Opção D: Script de Teste

```bash
python test_prediction.py
```

## Passo 4: Interpretar os Resultados

### Resumo da Predição
- **Operações Estimadas**: Quantas operações são necessárias
- **Tempo Estimado**: Quanto tempo levará para atingir o objetivo
- **Probabilidade**: Chance de sucesso baseada em dados históricos
- **Nível de Risco**: LOW, MEDIUM ou HIGH

### Recomendações de Trade
- **Direção**: BUY ou SELL
- **Confiança**: Nível de certeza da recomendação
- **Entrada/TP/SL**: Preços específicos
- **Lote**: Tamanho recomendado da posição

### Análise de Mercado
- **Tendência**: Direção e força do mercado
- **Volatilidade**: Nível de movimento esperado
- **Indicadores**: RSI, MACD, etc.

## Exemplos Práticos

### Exemplo 1: Scalping no Ouro
```json
{
  "symbol": "XAUUSDc",
  "target_profit": 20,
  "balance": 500,
  "timeframe": "M1",
  "risk_percentage": 1.5
}
```
**Resultado esperado:** 3-5 operações em ~1 hora

### Exemplo 2: Day Trading no Bitcoin
```json
{
  "symbol": "BTCUSDc",
  "target_profit": 100,
  "balance": 5000,
  "timeframe": "M15",
  "risk_percentage": 2.0
}
```
**Resultado esperado:** 5-8 operações em ~4 horas

### Exemplo 3: Swing Trading
```json
{
  "symbol": "EURUSDc",
  "target_profit": 50,
  "balance": 2000,
  "timeframe": "H1",
  "risk_percentage": 1.0
}
```
**Resultado esperado:** 8-12 operações em 1-2 dias

## Dicas Importantes

### ✅ Fazer
- Use sempre stop loss
- Comece com risk_percentage de 1-2%
- Teste em conta demo primeiro
- Siga as recomendações de horário
- Monitore a volatilidade

### ❌ Evitar
- Não opere sem stop loss
- Não arrisque mais de 5% da banca
- Não ignore os avisos do sistema
- Não opere em alta volatilidade sem experiência
- Não opere contra a tendência forte

## Troubleshooting Rápido

### Erro: "MT5 não conectado"
**Solução:** Abra o MetaTrader 5 e faça login

### Erro: "Símbolo não encontrado"
**Solução:** Verifique se o símbolo está correto e disponível no seu MT5

### Predição demora muito
**Solução:** Reduzir o número de barras ou usar timeframe maior

### Resultados diferentes a cada execução
**Solução:** Normal - o mercado muda constantemente

## Próximos Passos

1. ✅ Familiarize-se com a interface
2. ✅ Teste diferentes símbolos e timeframes
3. ✅ Compare predições com resultados reais
4. ✅ Ajuste parâmetros conforme sua estratégia
5. ✅ Integre com seu sistema de trading

## Suporte

- 📖 Documentação completa: `README_PREDICTION.md`
- 🧪 Testes automáticos: `python test_prediction.py`
- 🌐 Interface web: `http://localhost:5000/prediction/dashboard`
- 📊 Exemplos de API: `http://localhost:5000/prediction/examples`

---

**Boa sorte com suas operações! 🎯**

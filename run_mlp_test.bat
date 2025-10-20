@echo off
chcp 65001 >nul
REM Script de Teste Automatizado do Bot MLP
REM Executa: configuracao -> inicio -> trade -> fechamento -> parada

echo.
echo ============================================================
echo TESTE AUTOMATICO COMPLETO - BOT MLP COM OPERACAO REAL
echo ============================================================
echo.
echo Este script ira:
echo   1. Configurar TP para $0.50
echo   2. Iniciar o bot MLP
echo   3. Aguardar execucao de 1 trade
echo   4. Aguardar fechamento com TP/SL
echo   5. Parar o bot
echo.
echo AVISO: Executara trades REAIS no MT5!
echo CERTIFIQUE-SE que MT5 esta conectado!
echo.
pause

echo.
echo [FASE 1] CONFIGURANDO TP para $0.50...
curl -s -X POST http://localhost:5000/mlp/config ^
  -H "Content-Type: application/json" ^
  -d "{\"take_profit\": 0.50, \"confidence_threshold\": 0.85, \"auto_trading_enabled\": true}"
echo.

echo [FASE 2] INICIANDO Bot MLP...
curl -s -X POST http://localhost:5000/mlp/start
echo.

echo [FASE 3] AGUARDANDO execucao de trade...
echo      (Pode levar ate 5 minutos enquanto bot analisa mercado)
py -3.8 test_mlp_trade.py
echo.

echo [FASE 4] Teste concluido!
echo.

echo [FASE 5] Verificando trades realizados...
echo Resumo dos ultimos 5 trades:
curl -s "http://localhost:5000/mlp/trades?days=1"
echo.

echo [FASE 6] Finalizando...
curl -s -X POST http://localhost:5000/mlp/stop >nul
echo.

echo.
echo ============================================================
echo TESTE CONCLUIDO! Verifique os logs acima.
echo ============================================================
echo.
echo DICAS ADICIONAIS:
echo   - Analise manual: py -3.8 test_mlp_trade.py --analyze
echo   - Dashboard:     http://localhost:5001/quant/mlp/
echo   - Health Check:  http://localhost:5000/mlp/health
echo.
pause

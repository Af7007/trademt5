@echo off
REM Sistema COMPLETO MLP Trading - 3 Serviços
REM Plataforma + Dashboards + MCP Server

echo.
echo ==================================================
echo     SISTEMA MLP TRADING COMPLETO
echo ==================================================

:: Limpeza completa do sistema
echo [1/4] Limpando sistema...
echo        Parando processos Python...
taskkill /im python.exe /t /f >nul 2>&1
taskkill /im python3.exe /t /f >nul 2>&1

echo        Parando processos Node.js...
taskkill /im node.exe /t /f >nul 2>&1
taskkill /im npm.cmd /t /f >nul 2>&1

echo        Fechando janelas CMD antigas...
taskkill /fi "WINDOWTITLE eq MT5 PLATFORM*" /f >nul 2>&1
taskkill /fi "WINDOWTITLE eq DASHBOARDS*" /f >nul 2>&1
taskkill /fi "WINDOWTITLE eq MCP SERVER*" /f >nul 2>&1
timeout /t 2 >nul

echo        Liberando portas (3000, 5000, 5001)...
for %%p in (3000 5000 5001) do (
    netstat -a -o -n | findstr :%%p >nul 2>&1 && (
        for /f "tokens=5" %%t in ('netstat -a -o -n ^| findstr :%%p') do (
            if %%t neq 4 (
                taskkill /pid %%t /t /f >nul 2>&1
            )
        )
    )
)
timeout /t 2 >nul

echo        Limpando cache...
for /d /r %%i in (__pycache__) do rd /s /q "%%i" 2>nul
for /r %%i in (*.pyc) do del /q "%%i" 2>nul
del /q node_modules\.bin\*.* /s >nul 2>&1
echo                                Sistema limpo

:: Plataforma Principal (Flask)
echo [2/4] Iniciando Plataforma MT5 (5000)...
start "MT5-PLATFORM" cmd /k "cd /d %~pd0 && title MT5 PLATFORM (5000) && echo ========== MT5 PLATFORM ========== && echo. && py -3.8 app.py"
timeout /t 8 >nul
echo                                Plataforma iniciada

:: Dashboards (Django)
echo [3/4] Iniciando Dashboards (5001)...
start "DASHBOARDS" cmd /k "cd /d %~pd0django_server && title DASHBOARDS (5001) && echo ========== DASHBOARDS ========== && echo. && py -3.8 manage.py runserver 5001 --noreload"
timeout /t 5 >nul
echo                                Dashboards iniciadas

:: MCP Server (Node.js)
echo [4/4] Iniciando MCP Server (3000)...
start "MCP-SERVER" cmd /k "cd /d %~pd0mcp-trader && title MCP SERVER (3000) && echo ========== MCP SERVER ========== && echo. && npm start"
timeout /t 5 >nul
echo                                MCP Server iniciado

:: Acessos Diretos
echo.
echo ==================================================
echo        SISTEMA OPERACAO BASICA!
echo ==================================================
echo.
echo PLATAFORMA MT5    │ py -3.8 app.py        │ Port 5000
echo DASHBOARDS       │ py -3.8 manage.py     │ Port 5001
echo MCP SERVER       │ npm start             │ Port 3000
echo.
echo ACESSOS PRINCIPAIS:
echo MLP Health:      http://localhost:5000/mlp/health
echo BTC Stats:       http://localhost:5000/btcusd/stats
echo Dashboard MLP:   http://localhost:5001/quant/mlp/
echo Documentacao API: http://localhost:5001/apidocs/
echo MCP Tools:       http://localhost:3000/tools
echo MCP Frontend:    http://localhost:3000/test-frontend.html
echo.
echo FUNCIONALIDADES ATIVAS:
echo Dados reais MT5   - Market data em tempo real
echo Sinais IA MLP      - Analise inteligente
echo Interface Web      - Dashboard profissional
echo MCP Protocol       - Integracao com LLMs
echo WebSocket          - Comunicacao MetaTrader
echo.
echo SISTEMA COMPLETO OPERACIONAL!
echo    Todos os 3 servidores iniciados com sucesso
echo    Pressione ENTER para continuar...
pause >nul

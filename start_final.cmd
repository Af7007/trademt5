@echo off
REM Sistema MLP Trading - 2 Serviços
REM Plataforma + Dashboards

echo.
echo ==================================================
echo     SISTEMA MLP TRADING
echo ==================================================

:: Limpeza completa do sistema
echo [1/3] Limpando sistema...
echo        Parando processos Python...
taskkill /im python.exe /t /f >nul 2>&1
taskkill /im python3.exe /t /f >nul 2>&1

echo        Fechando janelas CMD antigas...
taskkill /fi "WINDOWTITLE eq MT5 PLATFORM*" /f >nul 2>&1
taskkill /fi "WINDOWTITLE eq DASHBOARDS*" /f >nul 2>&1
timeout /t 2 >nul

echo        Liberando portas (5000, 5001)...
for %%p in (5000 5001) do (
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
echo                                Sistema limpo

:: Plataforma Principal (Flask)
echo [2/3] Iniciando Plataforma MT5 (5000)...
start "MT5-PLATFORM" cmd /k "cd /d %~pd0 && title MT5 PLATFORM (5000) && echo ========== MT5 PLATFORM ========== && echo. && py -3.8 app.py"
timeout /t 8 >nul
echo                                Plataforma iniciada

:: Dashboards (Django)
echo [3/3] Iniciando Dashboards (5001)...
start "DASHBOARDS" cmd /k "cd /d %~pd0django_server && title DASHBOARDS (5001) && echo ========== DASHBOARDS ========== && echo. && py -3.8 manage.py runserver 5001 --noreload"
timeout /t 5 >nul
echo                                Dashboards iniciadas

:: Acessos Diretos
echo.
echo ==================================================
echo        SISTEMA OPERACAO BASICA!
echo ==================================================
echo.
echo PLATAFORMA MT5    │ py -3.8 app.py        │ Port 5000
echo DASHBOARDS       │ py -3.8 manage.py     │ Port 5001
echo.
echo ACESSOS PRINCIPAIS:
echo MLP Health:      http://localhost:5000/mlp/health
echo BTC Stats:       http://localhost:5000/btcusd/stats
echo Dashboard MLP:   http://localhost:5001/quant/mlp/
echo Documentacao API: http://localhost:5001/apidocs/
echo.
echo FUNCIONALIDADES ATIVAS:
echo Dados reais MT5   - Market data em tempo real
echo Sinais IA MLP      - Analise inteligente
echo Interface Web      - Dashboard profissional
echo WebSocket          - Comunicacao MetaTrader
echo.
echo SISTEMA OPERACIONAL!
echo    Ambas as plataformas iniciadas com sucesso
echo    Pressione ENTER para continuar...
pause >nul

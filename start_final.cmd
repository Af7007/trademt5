@echo off
REM Sistema MLP Trading - Plataforma Única
REM Apenas API Flask na porta 5000

echo.
echo ==================================================
echo     SISTEMA MLP TRADING - PLATAFORMA UNICA
echo ==================================================

:: Limpeza completa do sistema
echo [1/2] Limpando sistema...
echo        Parando processos Python...
taskkill /im python.exe /t /f >nul 2>&1
taskkill /im python3.exe /t /f >nul 2>&1

echo        Fechando janelas CMD antigas...
taskkill /fi "WINDOWTITLE eq MT5 PLATFORM*" /f >nul 2>&1
timeout /t 2 >nul

echo        Liberando porta 5000...
netstat -a -o -n | findstr :5000 >nul 2>&1 && (
    for /f "tokens=5" %%t in ('netstat -a -o -n ^| findstr :5000') do (
        if %%t neq 4 (
            taskkill /pid %%t /t /f >nul 2>&1
        )
    )
)
timeout /t 2 >nul

echo        Limpando cache...
for /d /r %%i in (__pycache__) do rd /s /q "%%i" 2>nul
for /r %%i in (*.pyc) do del /q "%%i" 2>nul
echo                                Sistema limpo

:: Plataforma Principal (Flask) - Única fonte
echo [2/2] Iniciando Plataforma MT5 (5000)...
start "MT5-PLATFORM" cmd /k "cd /d %~pd0 && title MT5 PLATFORM (5000) && echo ========== MT5 PLATFORM ========== && echo. && py -3.8 app.py"
timeout /t 8 >nul
echo                                Plataforma iniciada

:: Acessos Diretos
echo.
echo ==================================================
echo        SISTEMA OPERACAO BASICA!
echo ==================================================
echo.
echo PLATAFORMA MT5    │ py -3.8 app.py        │ Port 5000
echo.
echo ACESSOS PRINCIPAIS:
echo MLP Health:      http://localhost:5000/mlp/health
echo BTC Stats:       http://localhost:5000/btcusd/stats
echo Documentacao API: http://localhost:5000/apidocs/
echo.
echo FUNCIONALIDADES ATIVAS:
echo Dados reais MT5   - Market data em tempo real
echo Sinais IA MLP      - Analise inteligente
echo API REST Completa  - Todos os endpoints
echo Bot Trading Auto   - Execucao automatica
echo.
echo SISTEMA OPERACIONAL!
echo    Plataforma unica iniciada com sucesso
echo.
echo DASHBOARDS DJANGO REMOVIDOS
echo APENAS FLASK NA PORTA 5000
echo    Pressione ENTER para continuar...
pause >nul

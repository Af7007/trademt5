@echo off
title Motor de Predicao MT5
color 0A

echo ============================================
echo   MOTOR DE PREDICAO - TRADING MT5
echo ============================================
echo.

:: Verificar se Python esta instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado!
    echo Por favor instale Python 3.8 ou superior
    pause
    exit /b 1
)

echo [OK] Python encontrado
echo.

:: Verificar se MT5 esta rodando
tasklist /FI "IMAGENAME eq terminal64.exe" 2>NUL | find /I /N "terminal64.exe">NUL
if errorlevel 1 (
    echo [AVISO] MetaTrader 5 nao parece estar rodando
    echo Por favor, abra o MT5 e faca login antes de continuar
    echo.
    choice /C SN /M "Continuar mesmo assim? (S/N)"
    if errorlevel 2 exit /b 1
)

echo [OK] Iniciando servidor Flask...
echo.
echo ============================================
echo   Servidor iniciado em http://localhost:5000
echo   Dashboard: http://localhost:5000/prediction/dashboard
echo ============================================
echo.
echo Pressione Ctrl+C para parar o servidor
echo.

:: Iniciar servidor
python app.py

pause

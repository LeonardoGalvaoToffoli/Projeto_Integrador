@echo off
title Maestro do Projeto Integrador
echo ==========================================
echo   INICIANDO O SISTEMA COMPLETO (SCI-BDI)
echo ==========================================

:: 1. Inicia o Java (Spring Boot)
echo [1/3] Ligando o Servidor Java...
start "Servidor Java (Porta 8080)" cmd /k "cd service-busca-java && mvn spring-boot:run"

:: Pausa de 5 segundos
timeout /t 5 >nul

:: 2. Inicia a API Python (Flask)
echo [2/3] Ligando a API Python...
start "API Python (Porta 5000)" cmd /k "cd service-ia-python && .venv\Scripts\activate && python api_server.py"

:: Pausa de 3 segundos
timeout /t 3 >nul

:: 3. Inicia o Frontend (Streamlit)
echo [3/3] Abrindo o Streamlit...
start "Frontend Streamlit" cmd /k "cd service-ia-python && .venv\Scripts\activate && streamlit run app_streamlit.py"

echo.
echo ==========================================
echo   SUCESSO! AS JANELAS DEVEM ESTAR ABERTAS.
echo ==========================================
pause
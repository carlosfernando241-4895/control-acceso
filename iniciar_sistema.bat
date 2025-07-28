@echo off
REM Ir a la carpeta del proyecto
cd C:\Users\carlo\PycharmProjects\control_acceso

REM Activar el entorno virtual (ajusta si tienes otro nombre distinto a .venv)
call .venv\Scripts\activate.bat

REM Iniciar el servidor Flask en una nueva ventana de consola
start "Servidor Flask" cmd /k python main.py

REM Esperar 5 segundos a que Flask se inicie
timeout /t 5 >nul

REM Abrir el navegador
start http://localhost:5000
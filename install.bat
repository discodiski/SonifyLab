@echo off
REM ============================================
REM SonifyLab Pro - Instalador para Windows
REM ============================================
REM Autor: Discaury Salas
REM Compatible con: Windows 10/11
REM ============================================

title SonifyLab Pro - Instalador

echo.
echo ========================================
echo   SonifyLab Pro - Instalador Windows
echo ========================================
echo.

REM Verificar Python
echo [1/4] Verificando Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no esta instalado.
    echo Por favor, descarga Python desde https://python.org
    echo Asegurate de marcar "Add Python to PATH" durante la instalacion.
    pause
    exit /b 1
)
echo   [OK] Python encontrado

REM Verificar FFmpeg
echo.
echo [2/4] Verificando FFmpeg...
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ADVERTENCIA] FFmpeg no esta instalado o no esta en el PATH.
    echo.
    echo Para instalar FFmpeg:
    echo   1. Descarga desde https://ffmpeg.org/download.html
    echo   2. Extrae el archivo ZIP
    echo   3. Anade la carpeta 'bin' al PATH del sistema
    echo.
    echo Puedes continuar, pero la conversion no funcionara sin FFmpeg.
    echo.
    pause
)
if %errorlevel% equ 0 (
    echo   [OK] FFmpeg encontrado
)

REM Crear entorno virtual
echo.
echo [3/4] Configurando entorno virtual...
if exist "venv" (
    echo   Actualizando entorno existente...
) else (
    echo   Creando nuevo entorno virtual...
    python -m venv venv
)

REM Activar e instalar dependencias
echo.
echo [4/4] Instalando dependencias...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
echo   [OK] PyQt5 instalado correctamente

REM Crear acceso directo en el escritorio
echo.
echo Creando acceso directo en el Escritorio...
set SCRIPT_DIR=%~dp0
set DESKTOP=%USERPROFILE%\Desktop

REM Crear archivo .bat para lanzar la app
echo @echo off > "%SCRIPT_DIR%run_sonifylab.bat"
echo cd /d "%SCRIPT_DIR%" >> "%SCRIPT_DIR%run_sonifylab.bat"
echo call venv\Scripts\activate.bat >> "%SCRIPT_DIR%run_sonifylab.bat"
echo python SonifyLab.py >> "%SCRIPT_DIR%run_sonifylab.bat"

REM Crear acceso directo usando PowerShell
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%DESKTOP%\SonifyLab Pro.lnk'); $s.TargetPath = '%SCRIPT_DIR%run_sonifylab.bat'; $s.IconLocation = '%SCRIPT_DIR%icono.ico'; $s.WorkingDirectory = '%SCRIPT_DIR%'; $s.Save()"

echo   [OK] Acceso directo creado en el Escritorio

echo.
echo ========================================
echo   Instalacion completada con exito!
echo ========================================
echo.
echo Para ejecutar SonifyLab Pro:
echo   - Haz doble clic en "SonifyLab Pro" en el Escritorio
echo   - O ejecuta run_sonifylab.bat
echo.
pause

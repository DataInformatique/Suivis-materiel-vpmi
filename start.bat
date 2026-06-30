@echo off
REM ===== Suivi Materiel VPMI — demarrage Windows =====
cd /d "%~dp0"

IF NOT EXIST ".venv" (
    echo Creation de l'environnement Python...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    echo Installation des dependances...
    pip install -r requirements.txt
) ELSE (
    call .venv\Scripts\activate.bat
)

IF NOT EXIST ".env" (
    echo.
    echo ATTENTION : le fichier .env est absent.
    echo Copiez .env.example en .env et remplissez les valeurs ^(voir README.md^).
    copy .env.example .env >nul
    echo Un .env vierge a ete cree. Ouvrez-le, completez-le, puis relancez.
    pause
    exit /b
)

echo.
echo Application accessible sur http://127.0.0.1:8000
echo (Ctrl+C pour arreter)
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
pause

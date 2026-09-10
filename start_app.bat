@echo off
SETLOCAL EnableDelayedExpansion

echo ==============================================
echo       IHIS RAG Assistant - Startup Script      
echo ==============================================
echo.

cd /d "%~dp0"

:: Check if virtual environment exists
IF NOT EXIST "venv\" (
    echo [INFO] First time setup detected! Creating virtual environment...
    
    :: Attempt to use Python 3.11 specifically to avoid the 3.14 alpha wheel issues
    py -3.11 -m venv venv >nul 2>&1
    IF !ERRORLEVEL! NEQ 0 (
        echo [INFO] Python 3.11 not found via 'py', falling back to default Python...
        python -m venv venv
    )
    
    echo [INFO] Activating environment and installing dependencies... (This may take a few minutes)
    call venv\Scripts\activate.bat
    python -m pip install --upgrade pip >nul 2>&1
    pip install -r requirements.txt
    echo [INFO] Installation complete!
) ELSE (
    echo [INFO] Virtual environment found. Activating...
    call venv\Scripts\activate.bat
)

:: Check if .env file exists
IF NOT EXIST ".env" (
    echo.
    echo [WARNING] Security Configuration Required!
    echo No .env file found. To keep your API key secure and off GitHub,
    echo we need to generate it locally.
    set /p API_KEY="Please paste your Google Gemini API Key: "
    echo GEMINI_API_KEY=!API_KEY!> .env
    echo [INFO] .env file generated successfully and securely hidden!
    echo.
)

:: Check if the ChromaDB vector database exists
IF NOT EXIST "chroma_db\" (
    echo [INFO] Vector database not found. Running ingestion script...
    echo [INFO] This will embed the GAHAR handbook. It may take a few minutes.
    python ingest.py
    echo [INFO] Ingestion complete!
    echo.
)

echo [INFO] Starting the IHIS Application Server...
echo.
python app.py

pause

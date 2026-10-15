@echo off
SETLOCAL EnableDelayedExpansion
TITLE Integrated Hospital Information System (IHIS) Launcher

echo =====================================================================
echo           INTEGRATED HOSPITAL INFORMATION SYSTEM (IHIS)              
echo          Multimodal Clinical AI Platform - Automated Launcher        
echo =====================================================================
echo.

cd /d "%~dp0"

:: -----------------------------------------------------------------------
:: STEP 1: Environment & Python Runtime Detection
:: -----------------------------------------------------------------------
echo [STEP 1/6] Checking Python Runtime Environment...
IF NOT EXIST "venv\" (
    echo   - Virtual environment not found. Setting up clean workspace...
    
    :: Attempt to use Python 3.11 launcher (recommended for PyTorch, TF, and ChromaDB stability)
    py -3.11 -m venv venv >nul 2>&1
    IF !ERRORLEVEL! NEQ 0 (
        echo   - Python 3.11 launcher not found. Initializing with system python...
        python -m venv venv
    )
    IF NOT EXIST "venv\Scripts\activate.bat" (
        echo   [ERROR] Failed to create virtual environment. Please ensure Python is installed and added to PATH.
        pause
        exit /b 1
    )
    echo   - Virtual environment created successfully.
    
    :: Upgrade pip & install dependencies on first creation
    echo [STEP 2/6] Installing Dependencies from requirements.txt...
    call venv\Scripts\activate.bat
    python -m pip install --upgrade pip >nul 2>&1
    pip install -r requirements.txt
) ELSE (
    echo   - Existing virtual environment detected.
    echo [STEP 2/6] Activating Virtual Environment...
    call venv\Scripts\activate.bat
)
echo   - Environment active: Python !PYTHON_VERSION!
echo.

:: -----------------------------------------------------------------------
:: STEP 3: Dependency Integrity Check
:: -----------------------------------------------------------------------
echo [STEP 3/6] Verifying core framework packages...
python -c "import flask, sqlalchemy" >nul 2>&1
IF !ERRORLEVEL! NEQ 0 (
    echo   - Re-syncing missing packages from requirements.txt...
    pip install -r requirements.txt
) ELSE (
    echo   - Core framework verified.
)
echo.

:: -----------------------------------------------------------------------
:: STEP 4: Configuration & API Security Guardrail
:: -----------------------------------------------------------------------
echo [STEP 4/6] Checking Environment Variables & Security Guardrails...
IF NOT EXIST ".env" (
    echo.
    echo   ====================== CONFIGURATION NOTICE ======================
    echo   No .env configuration file found.
    echo   For RAG Accreditation Assistant queries, a Google Gemini API Key
    echo   is required. (Offline Vision models like Bone Fracture YOLO and
    echo   Dental U-Net work locally without an API key).
    echo   ==================================================================
    echo.
    set /p USER_API_KEY="Enter your GEMINI_API_KEY (press ENTER to skip/use local models only): "
    
    (
        echo # IHIS Local Environment Configuration
        echo FLASK_ENV=development
        echo SECRET_KEY=ihis-secure-local-dev-key
        IF DEFINED USER_API_KEY (
            echo GEMINI_API_KEY=!USER_API_KEY!
        ) ELSE (
            echo GEMINI_API_KEY=
        )
    ) > .env
    echo   - Generated .env file safely (kept local and excluded from git).
) ELSE (
    echo   - .env configuration file detected.
)
echo.

:: -----------------------------------------------------------------------
:: STEP 5: AI Knowledge Base & Embeddings Check
:: -----------------------------------------------------------------------
echo [STEP 5/6] Checking GAHAR Standards RAG Vector Database...
IF NOT EXIST "chroma_db\" (
    IF EXIST "gahar-handbook-for-hospitals-accreditation-standards-final.pdf" (
        echo   - Vector store not found. Building ChromaDB index from GAHAR Handbook...
        python ingest.py
        echo   - Vector index build complete.
    ) ELSE (
        echo   - Note: GAHAR accreditation PDF not found. Ingestion skipped.
    )
) ELSE (
    echo   - ChromaDB vector store verified.
)
echo.

:: -----------------------------------------------------------------------
:: STEP 6: Clinical Database & Account Seeding
:: -----------------------------------------------------------------------
echo [STEP 6/6] Checking Clinical Database & User Accounts...
IF NOT EXIST "database\ihis.db" (
    echo   - Database not initialized. Running seed script with clinical demo data...
    python seed.py
    echo   - Database created and seeded.
) ELSE (
    echo   - SQLite clinical database verified (database\ihis.db).
)
echo.

:: -----------------------------------------------------------------------
:: LAUNCH APPLICATION
:: -----------------------------------------------------------------------
echo =====================================================================
echo   IHIS SERVER READY!
echo.
echo   Demo Login Accounts (Password for all: password123)
echo     - Doctor Portal:       doctor1
echo     - Dental Portal:       dentist1
echo     - Dermatology Portal:  derm_doctor
echo     - Patient Portal:      patient1  (or patient2)
echo.
echo   Opening: http://127.0.0.1:5000 in your browser...
echo   Press CTRL+C in this console window to gracefully stop the server.
echo =====================================================================
echo.

start "" http://127.0.0.1:5000
python app.py

pause

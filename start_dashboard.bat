@echo off
echo Starting TerraShield Dashboard System...
echo.

echo Starting Flask Backend API...
start "Flask Backend" cmd /k "cd backend && python app.py"

echo Waiting for Flask to start...
timeout /t 3 /nobreak >nul

echo Starting Streamlit Dashboard...
start "Streamlit Dashboard" cmd /k "cd frontend && python -m streamlit run dashboard2.py --server.port=8501"

echo.
echo Both services are starting...
echo Flask Backend API: http://127.0.0.1:5000
echo Streamlit Dashboard: http://localhost:8501
echo.
echo Press any key to exit this window (services will continue running)
pause >nul

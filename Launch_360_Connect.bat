@echo off
title 360 Connect - Alumni Portal
cd /d "%~dp0"

echo =====================================================
echo                Starting 360 Connect                  
echo =====================================================
echo.
echo [1/2] Pre-launching GD Preparation Engine...
start /b cmd /c "cd /d gd_preparation && npm run dev"

echo [2/2] Launching 360 Connect Portal...
start "" "msedge.exe" --app=http://localhost:8501

python -m streamlit run app.py

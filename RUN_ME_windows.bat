@echo off
cd /d "%~dp0"

echo Hello! The pipeline is getting started. Please keep this window open. 
python -m pip install -r requirements.txt --quiet --disable-pip-version-check

python 1_organize.py
python 2_clean.py
python 3_compute.py

echo.
echo Pipeline finished.
pause
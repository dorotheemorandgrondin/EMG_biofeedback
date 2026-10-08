#!/bin/bash
# EMG analysis workflow - double-click this file to run the pipeline (Mac)

cd "$(dirname "$0")"   # go to the folder where this file is

echo "Hello! The pipeline is getting started. Please keep this window open."
python3 -m pip install -r requirements.txt --quiet --disable-pip-version-check

python3 1_organize.py

echo ""
echo "Pipeline finished."
read -n 1 -s -r -p "Press any key to close this window."
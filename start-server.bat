@echo off
REM Change directory to the target folder
cd /d "C:/Users/sandu calin/Documents/work/QkdMessage/flask_socket"

REM Run both Python files
start cmd /k python server.py
start cmd /k python client.py

REM Pause so the window doesn't close immediately
pause
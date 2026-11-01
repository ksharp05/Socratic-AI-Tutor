@echo off
rem Opens the local control panel (tools\panel) in your browser. Works from any folder.
"%~dp0.venv\Scripts\python.exe" "%~dp0tools\panel\server.py" %*

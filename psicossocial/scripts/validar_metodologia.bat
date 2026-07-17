@echo off
cd /d "%~dp0.."
".\.venv\Scripts\python.exe" -m psicossocial.cli validar-metodologia --config config/metodologia_v1.yaml --json

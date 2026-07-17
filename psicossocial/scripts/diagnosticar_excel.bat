@echo off
cd /d "%~dp0.."
set "INPUT=%~1"
if "%INPUT%"=="" set INPUT=dados\entrada_exemplo.xlsx
".\.venv\Scripts\python.exe" -m psicossocial.cli diagnosticar-excel --input "%INPUT%" --config config/metodologia_v1.yaml

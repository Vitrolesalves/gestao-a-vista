@echo off
cd /d "%~dp0.."
set "INPUT=%~1"
set "OUTPUT=%~2"
if "%INPUT%"=="" set INPUT=dados\entrada_exemplo.xlsx
if "%OUTPUT%"=="" set OUTPUT=dados\resultado_exemplo.xlsx
".\.venv\Scripts\python.exe" -m psicossocial.cli exportar-excel --input "%INPUT%" --output "%OUTPUT%" --config config/metodologia_v1.yaml

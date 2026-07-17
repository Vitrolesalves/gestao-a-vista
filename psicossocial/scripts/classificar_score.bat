@echo off
cd /d "%~dp0.."
set SCORE=%1
if "%SCORE%"=="" set SCORE=3.5
".\.venv\Scripts\python.exe" -m psicossocial.cli classificar-score --config config/metodologia_v1.yaml --score %SCORE%

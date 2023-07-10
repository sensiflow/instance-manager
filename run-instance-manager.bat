@echo OFF

if "%1"=="" goto dev

echo "using envinroment %1" 
set ENVIRONMENT=%1

goto install

:dev

echo "using default environment: dev" 
set ENVIRONMENT=DEV

:install

poetry install
poetry run python run.py
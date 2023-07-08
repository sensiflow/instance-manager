#!/bin/bash

if [ -z "$1" ]
then
    echo "using default environment: dev"
    ENVIRONMENT=DEV
else
    echo "using envinroment $1"
    ENVIRONMENT=$1
fi

poetry install
poetry run python scheduler.py

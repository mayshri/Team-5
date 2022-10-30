#!/usr/bin/env bash

exec python3 run_evaluation.py &
exec python3 -m flask run --host=0.0.0.0
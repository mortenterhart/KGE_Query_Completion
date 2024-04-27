#!/usr/bin/env bash

# Script to evaluate a model on Google Cloud Engine
# and shutdown afterwards

python evaluate_model.py

sleep 60

sudo shutdown -h now

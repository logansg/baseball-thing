#!/bin/bash

# Start the worker program in the background
python worker.py &

# Start the main program
python main.py

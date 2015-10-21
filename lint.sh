#!/bin/sh

flake8 .
flake8 --ignore=N,E302 --exclude= analysis/analysis.py

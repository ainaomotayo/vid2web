#!/bin/bash
isort src/ tests/
pyink --config pyproject.toml src/ tests/

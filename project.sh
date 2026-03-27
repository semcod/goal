#!/usr/bin/env bash
clear
pip install -e .
venv/bin/pip install vallm --upgrade
venv/bin/pip install redup --upgrade
venv/bin/pip install glon --upgrade
venv/bin/pip install goal --upgrade
venv/bin/pip install code2logic --upgrade
venv/bin/pip install code2llm --upgrade
#code2llm ./ -f toon,evolution,code2logic,project-yaml -o ./project --no-chunk
venv/bin/code2llm ./ -f all -o ./project --no-chunk
#code2llm report --format all       # → all views
rm project/analysis.json
rm project/analysis.yaml

venv/bin/pip install code2docs --upgrade
venv/bin/code2docs ./ --readme-only
venv/bin/redup scan . --format toon --output ./project
#venv/bin/redup scan . --functions-only -f toon --output ./project
#venv/bin/vallm batch ./src --recursive --semantic --model qwen2.5-coder:7b
#vallm batch --parallel .
venv/bin/vallm batch . --recursive --format toon --output ./project
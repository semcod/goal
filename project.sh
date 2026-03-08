#!/usr/bin/env bash
clear
pip install glon --upgrade
pip install code2llm --upgrade
pip install -e .
code2docs ./code2docs --output ../docs/
#code2llm ./ -f toon,evolution,code2logic,project-yaml -o ./project --no-chunk
code2llm ./ -f all -o ./project --no-chunk
#code2llm report --format all       # → all views
rm project/analysis.json
rm project/analysis.yaml

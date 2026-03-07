#!/usr/bin/env bash
clear
pip install glon --upgrade
pip install code2llm --upgrade
#code2llm ./ -f toon,evolution,code2logic,project-yaml -o ./project --no-chunk
code2llm ./ -f all -o ./project --no-chunk
#code2llm report --format all       # → all views
rm project/analysis.json
rm project/analysis.yaml
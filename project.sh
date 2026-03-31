#!/usr/bin/env bash
clear
pip install -e .
pip install pyqual --upgrade
pip install prefact --upgrade
pip install vallm --upgrade
pip install redup --upgrade
pip install glon --upgrade
pip install goal --upgrade
pip install code2logic --upgrade
pip install code2llm --upgrade
#code2llm ./ -f toon,evolution,code2logic,project-yaml -o ./project --no-chunk
code2llm ./ -f all -o ./project --no-chunk
#code2llm report --format all       # → all views
rm project/analysis.json
rm project/analysis.yaml

pip install code2docs --upgrade
code2docs ./ --readme-only
redup scan . --format toon --output ./project
#redup scan . --functions-only -f toon --output ./project
#vallm batch ./src --recursive --semantic --model qwen2.5-coder:7b
#vallm batch --parallel .
vallm batch . --recursive --format toon --output ./project
prefact -a
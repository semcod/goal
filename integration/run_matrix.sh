#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="/tmp/goal-integration-matrix"
rm -rf "$ROOT_DIR"
mkdir -p "$ROOT_DIR"

pass_count=0
fail_count=0

run_case() {
  local ptype="$1"
  local repo="$ROOT_DIR/$ptype"

  rm -rf "$repo"
  mkdir -p "$repo"
  pushd "$repo" >/dev/null

  git init -q
  git config user.email "ci@example.com"
  git config user.name "CI"

  printf "0.1.0\n" > VERSION

  cat > goal.yaml <<'YAML'
quality:
  enhanced_summary:
    enabled: false
  gates:
    min_capabilities: 0
    min_unique_files_ratio: 0
    max_duplicate_relations: 999
YAML

  local change_file=""

  case "$ptype" in
    python)
      cat > pyproject.toml <<'TOML'
[project]
name = "matrix-python"
version = "0.1.0"
TOML
      cat > app.py <<'PY'
print("hello")
PY
      change_file="app.py"
      ;;
    nodejs)
      cat > package.json <<'JSON'
{
  "name": "matrix-node",
  "version": "0.1.0"
}
JSON
      cat > index.js <<'JS'
console.log('hello')
JS
      change_file="index.js"
      ;;
    rust)
      cat > Cargo.toml <<'TOML'
[package]
name = "matrix_rust"
version = "0.1.0"
edition = "2021"
TOML
      mkdir -p src
      cat > src/lib.rs <<'RS'
pub fn hello() -> &'static str { "hello" }
RS
      change_file="src/lib.rs"
      ;;
    go)
      cat > go.mod <<'MOD'
module example.com/matrix

go 1.22
MOD
      mkdir -p cmd/app
      cat > cmd/app/main.go <<'GO'
package main

import "fmt"

func main() {
	fmt.Println("hello")
}
GO
      change_file="cmd/app/main.go"
      ;;
    ruby)
      cat > Gemfile <<'RB'
source "https://rubygems.org"

gemspec
RB
      cat > matrix.gemspec <<'RBS'
Gem::Specification.new do |s|
  s.name        = "matrix"
  s.version     = "0.1.0"
  s.summary     = "matrix"
  s.authors     = ["ci"]
  s.files       = ["lib/matrix.rb"]
end
RBS
      mkdir -p lib
      cat > lib/matrix.rb <<'RB'
module Matrix
  def self.hello
    "hello"
  end
end
RB
      change_file="lib/matrix.rb"
      ;;
    php)
      cat > composer.json <<'JSON'
{
  "name": "matrix/php",
  "version": "0.1.0",
  "require": {}
}
JSON
      mkdir -p src
      cat > src/App.php <<'PHP'
<?php

class App {
  public static function hello(): string {
    return "hello";
  }
}
PHP
      change_file="src/App.php"
      ;;
    dotnet)
      cat > Matrix.csproj <<'XML'
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net8.0</TargetFramework>
    <Version>0.1.0</Version>
  </PropertyGroup>
</Project>
XML
      cat > Program.cs <<'CS'
Console.WriteLine("hello");
CS
      change_file="Program.cs"
      ;;
    java)
      cat > pom.xml <<'XML'
<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.example</groupId>
  <artifactId>matrix</artifactId>
  <version>0.1.0</version>
</project>
XML
      mkdir -p src/main/java/com/example
      cat > src/main/java/com/example/App.java <<'JAVA'
package com.example;

public class App {
  public static void main(String[] args) {
    System.out.println("hello");
  }
}
JAVA
      change_file="src/main/java/com/example/App.java"
      ;;
    *)
      echo "Unknown project type: $ptype" >&2
      popd >/dev/null
      return 1
      ;;
  esac

  git add -A
  git commit -qm "chore: init"

  echo "" >> "$change_file"
  git add -A

  local info_out
  info_out=$(goal info 2>&1)
  echo "$info_out" | grep -qi "Project types:.*$ptype"

  local out
  out=$(goal push --dry-run --yes --markdown 2>&1)
  echo "$out" | grep -Fq "# Goal Push Result"
  echo "$out" | grep -Fq "**Commit:**"

  popd >/dev/null
}

PTYPES=(python nodejs rust go ruby php dotnet java)

for p in "${PTYPES[@]}"; do
  echo "=== [$p] ==="
  if run_case "$p"; then
    echo "PASS: $p"
    pass_count=$((pass_count + 1))
  else
    echo "FAIL: $p"
    fail_count=$((fail_count + 1))
  fi
done

echo "\nPassed: $pass_count, Failed: $fail_count"

if [[ "$fail_count" -gt 0 ]]; then
  exit 1
fi

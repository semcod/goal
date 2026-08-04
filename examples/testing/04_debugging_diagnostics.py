"""
Testy diagnostyczne i debugowanie.

Przykłady narzędzi do diagnozowania problemów z Goal.
"""

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
import subprocess
import traceback

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def test_debug_output_capture():
    """
    Przechwytywanie i analiza outputu debugowego.

    Użyteczne do wykrywania duplikatów w logach.
    """
    from goal.project_bootstrap import bootstrap_project

    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        (project_dir / "pyproject.toml").write_text('[project]\nname="debug-test"\n')
        subprocess.run(["git", "init"], cwd=project_dir, capture_output=True)

        # Przechwytujemy wszystkie wyjścia click
        captured_output = []

        def capture_echo(message, *args, **kwargs):
            captured_output.append(str(message))

        with patch("click.echo", side_effect=capture_echo):
            with patch(
                "goal.project_bootstrap._ensure_costs_installed", return_value=True
            ):
                with patch(
                    "goal.project_bootstrap.ensure_project_environment",
                    return_value=True,
                ):
                    bootstrap_project(project_dir, "python", yes=True)

        # Analiza przechwyconych danych
        print(f"Przechwycono {len(captured_output)} linii outputu")

        # Szukaj duplikatów
        from collections import Counter

        duplicates = {
            line: count for line, count in Counter(captured_output).items() if count > 1
        }

        if duplicates:
            print("\n⚠ Znaleziono duplikaty:")
            for line, count in duplicates.items():
                print(f"  ({count}x) {line[:80]}")
        else:
            print("\n✓ Brak duplikatów w outputcie")

        # Szukaj konkretnych wzorców
        debug_lines = [l for l in captured_output if "DEBUG:" in l]
        print(f"\nLinie DEBUG: {len(debug_lines)}")
        for line in debug_lines:
            print(f"  {line}")


def test_stack_trace_analysis():
    """
    Analiza stack trace dla zrozumienia przepływu wywołań.
    """

    call_origins = []

    def traced_costs_install(project_dir, python_bin):
        # Zapisz stack trace
        stack = traceback.extract_stack()
        # Usuń ostatnią ramkę (bieżące wywołanie)
        stack = stack[:-1]

        # Znajdź wywołującego w project_bootstrap
        relevant_frames = [f for f in stack if "project_bootstrap.py" in f.filename]

        call_origins.append(
            {
                "function": relevant_frames[-1].name if relevant_frames else "unknown",
                "line": relevant_frames[-1].lineno if relevant_frames else 0,
                "file": relevant_frames[-1].filename if relevant_frames else "unknown",
            }
        )

        return True

    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        (project_dir / "pyproject.toml").write_text('[project]\nname="trace-test"\n')
        subprocess.run(["git", "init"], cwd=project_dir, capture_output=True)

        with patch("click.echo"):
            with patch(
                "goal.project_bootstrap._ensure_costs_installed",
                side_effect=traced_costs_install,
            ):
                from goal.project_bootstrap import bootstrap_project

                bootstrap_project(project_dir, "python", yes=True)

        print("\nŚledzenie wywołań _ensure_costs_installed:")
        for i, origin in enumerate(call_origins, 1):
            print(f"  {i}. Wywołane z: {origin['function']}() (linia {origin['line']})")

        if len(call_origins) > 1:
            print(f"\n⚠ Funkcja wywołana {len(call_origins)} razy!")
        else:
            print("\n✓ Funkcja wywołana tylko raz")


def test_performance_timing():
    """
    Pomiar czasu wykonania funkcji.

    Użyteczne do wykrywania spowolnienia spowodowanego duplikatami.
    """
    import time
    from goal.project_bootstrap import bootstrap_project

    timings = {}

    def timed_costs_install(project_dir, python_bin):
        start = time.time()
        # Symulacja pracy
        time.sleep(0.01)  # 10ms
        elapsed = time.time() - start

        if "costs_install" not in timings:
            timings["costs_install"] = []
        timings["costs_install"].append(elapsed)

        return True

    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        (project_dir / "pyproject.toml").write_text('[project]\nname="perf-test"\n')
        subprocess.run(["git", "init"], cwd=project_dir, capture_output=True)

        with patch("click.echo"):
            with patch(
                "goal.project_bootstrap._ensure_costs_installed",
                side_effect=timed_costs_install,
            ):
                with patch(
                    "goal.project_bootstrap.ensure_project_environment",
                    return_value=True,
                ):
                    start_total = time.time()
                    bootstrap_project(project_dir, "python", yes=True)
                    total_time = time.time() - start_total

        print("\nCzasy wykonania:")
        print(f"  Całkowity czas: {total_time:.3f}s")

        if "costs_install" in timings:
            times = timings["costs_install"]
            print(f"  _ensure_costs_installed: {len(times)} wywołań")
            print(f"    Suma: {sum(times):.3f}s")
            print(f"    Średnia: {sum(times) / len(times):.3f}s")

            if len(times) > 1:
                print(f"\n  ⚠ Nadmiarowe wywołania kosztowały {sum(times[1:]):.3f}s")


def test_import_tracing():
    """
    Śledzenie importów dla wykrywania cykli i duplikatów.
    """
    import sys

    # Zapisz stan przed
    before_modules = set(sys.modules.keys())

    # Importuj goal

    # Sprawdź co zostało zaimportowane
    after_modules = set(sys.modules.keys())
    new_modules = after_modules - before_modules

    goal_modules = [m for m in new_modules if "goal" in m]

    print(f"\nZaimportowano {len(goal_modules)} modułów goal:")
    for m in sorted(goal_modules)[:20]:  # Limit do 20
        print(f"  - {m}")
    if len(goal_modules) > 20:
        print(f"  ... i {len(goal_modules) - 20} więcej")

    # Sprawdź duplikaty importów
    print("\n✓ Import tracing zakończony")


def test_config_diagnostics():
    """
    Diagnostyka konfiguracji.
    """
    from goal.user_config import get_user_config

    print("\nDiagnostyka konfiguracji:")

    try:
        config = get_user_config()
        if config:
            print("  Załadowano konfigurację użytkownika")
            print(f"  Klucze: {list(config.keys())}")
        else:
            print("  Brak konfiguracji użytkownika")
    except Exception as e:
        print(f"  Błąd ładowania konfiguracji: {e}")

    # Sprawdź lokalną konfigurację
    local_config = Path.cwd() / "goal.yaml"
    if local_config.exists():
        print(f"  Znaleziono lokalną konfigurację: {local_config}")
    else:
        print("  Brak lokalnej konfiguracji (goal.yaml)")


def create_debug_report():
    """
    Tworzenie pełnego raportu debugowego.
    """
    print("=" * 60)
    print("RAPORT DIAGNOSTYCZNY GOAL")
    print("=" * 60)

    # Wersja
    try:
        from goal import __version__

        print(f"\nWersja goal: {__version__}")
    except:
        print("\nWersja goal: nieznana")

    # Python
    import platform

    print(f"Python: {platform.python_version()}")
    print(f"System: {platform.system()} {platform.release()}")

    # Git
    try:
        result = subprocess.run(["git", "--version"], capture_output=True, text=True)
        print(f"Git: {result.stdout.strip()}")
    except:
        print("Git: niedostępny")

    # Zależności
    print("\nKluczowe zależności:")
    deps = ["click", "yaml", "git"]
    for dep in deps:
        try:
            if dep == "yaml":
                import yaml as y

                print(f"  PyYAML: {y.__version__}")
            elif dep == "git":
                import git

                print(f"  GitPython: {git.__version__}")
            else:
                mod = __import__(dep)
                ver = getattr(mod, "__version__", "unknown")
                print(f"  {dep}: {ver}")
        except ImportError:
            print(f"  {dep}: nie zainstalowano")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    create_debug_report()

    print("\n--- Testy diagnostyczne ---")

    print("\n1. Przechwytywanie outputu debug:")
    test_debug_output_capture()

    print("\n2. Analiza stack trace:")
    test_stack_trace_analysis()

    print("\n3. Pomiar wydajności:")
    test_performance_timing()

    print("\n4. Śledzenie importów:")
    test_import_tracing()

    print("\n5. Diagnostyka konfiguracji:")
    test_config_diagnostics()

    print("\n" + "=" * 60)
    print("Diagnostyka zakończona")
    print("=" * 60)

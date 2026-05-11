"""
cleanup_workspace.py — Sniper v6.2 · Limpieza Segura del Workspace
Pide confirmacion antes de borrar. Ejecutar con:
    python -X utf8 cleanup_workspace.py
"""
import sys, os
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).parent

# ═══════════════════════════════════════════════════════════════════════════════
# INVENTARIO DE ARCHIVOS OBSOLETOS
# ═══════════════════════════════════════════════════════════════════════════════
#
# Criterio de seleccion:
#   SCRIPTS RAIZ HUERFANOS
#     train_phase1.py           -> wrapper 1 linea, sustituido por orquestador_fases.py
#     entrenador_fase2_terminal.py -> lanzador terminal Fase 2, idem
#     run_fase3.py              -> lanzador terminal Fase 3, idem
#     nvidia_quickstart.py      -> demo NVIDIA, integrado en nvidia_acceleration.py
#     constructor.py            -> bootstrap inicial, proyecto ya configurado
#
#   TESTS POR FASE -> sustituidos por test_pipeline_completo.py
#     test_fase1.py, test_fase2.py, test_fase3.py, test_nvidia_dashboard.py
#
#   DOCUMENTACION FRAGMENTADA -> absorbida por nuevo README.md
#     FASE_1_COMPLETADA.md, FASE_1_RESUMEN.txt, FASE_2_DOCUMENTACION.md,
#     FASE_3_ENSEMBLE.md, MANIFEST.md, PROYECTO_COMPLETADO.md,
#     QUICKSTART.md, QUICKSTART_FASE1.md, QUICKSTART_FASE2.md,
#     DASHBOARD_ORQUESTADOR*.md, NVIDIA_INTEGRATION_*.md/txt,
#     ARQUITECTURA_DIAGRAM.txt
#
#   LOGS TEMPORALES
#     fase3_full.log, fase3_output.log, test_output.log

ARCHIVOS_OBSOLETOS = [
    # Scripts raiz huerfanos
    (ROOT / "train_phase1.py",               "Wrapper de 1 linea -> orquestador_fases.py"),
    (ROOT / "entrenador_fase2_terminal.py",   "Lanzador terminal Fase 2 -> orquestador_fases.py"),
    (ROOT / "run_fase3.py",                   "Lanzador terminal Fase 3 -> orquestador_fases.py"),
    (ROOT / "nvidia_quickstart.py",           "Demo NVIDIA -> integrado en nvidia_acceleration.py"),
    (ROOT / "constructor.py",                 "Bootstrap inicial, proyecto ya configurado"),
    # Tests individuales por fase
    (ROOT / "test_fase1.py",                  "Sustituido por test_pipeline_completo.py"),
    (ROOT / "test_fase2.py",                  "Sustituido por test_pipeline_completo.py"),
    (ROOT / "test_fase3.py",                  "Sustituido por test_pipeline_completo.py"),
    (ROOT / "test_nvidia_dashboard.py",       "Demo visual aislada, no refleja stack actual"),
    # Documentacion fragmentada
    (ROOT / "FASE_1_COMPLETADA.md",           "Absorbida por nuevo README.md"),
    (ROOT / "FASE_1_RESUMEN.txt",             "Absorbida por nuevo README.md"),
    (ROOT / "FASE_2_DOCUMENTACION.md",        "Absorbida por nuevo README.md"),
    (ROOT / "FASE_3_ENSEMBLE.md",             "Absorbida por nuevo README.md"),
    (ROOT / "MANIFEST.md",                    "Manifiesto de sesion anterior"),
    (ROOT / "PROYECTO_COMPLETADO.md",         "Snapshot pre-Fase 4, obsoleto"),
    (ROOT / "QUICKSTART.md",                  "Sustituido por seccion Ejecucion del README"),
    (ROOT / "QUICKSTART_FASE1.md",            "Sustituido por seccion Ejecucion del README"),
    (ROOT / "QUICKSTART_FASE2.md",            "Sustituido por seccion Ejecucion del README"),
    (ROOT / "DASHBOARD_ORQUESTADOR.md",       "Borrador arquitectura -> README.md"),
    (ROOT / "DASHBOARD_ORQUESTADOR_SUMMARY.md",    "Borrador arquitectura -> README.md"),
    (ROOT / "DASHBOARD_ORQUESTADOR_VALIDACION.md", "Borrador arquitectura -> README.md"),
    (ROOT / "NVIDIA_INTEGRATION_GUIDE.md",    "Integrado en seccion Hardware del README"),
    (ROOT / "NVIDIA_INTEGRATION_SUMMARY.txt", "Integrado en seccion Hardware del README"),
    (ROOT / "ARQUITECTURA_DIAGRAM.txt",       "Sustituido por diagrama ASCII del README"),
    # Logs temporales
    (ROOT / "fase3_full.log",                 "Log de depuracion temporal (124 KB)"),
    (ROOT / "fase3_output.log",               "Log de ejecucion anterior"),
    (ROOT / "test_output.log",                "Salida de test anterior"),
]


def main():
    SEP = "-" * 65
    print()
    print("=" * 65)
    print("  Sniper v6.2 -- Limpieza Segura del Workspace")
    print("=" * 65)

    existentes   = [(p, r) for p, r in ARCHIVOS_OBSOLETOS if p.exists()]
    no_existen   = [(p, r) for p, r in ARCHIVOS_OBSOLETOS if not p.exists()]

    if no_existen:
        print(f"\n  INFO: {len(no_existen)} archivo(s) ya no estan en disco (omitidos):")
        for p, _ in no_existen:
            print(f"        - {p.name}")

    if not existentes:
        print("\n  El workspace ya esta limpio. Nada que eliminar.")
        print("=" * 65 + "\n")
        return

    total_kb = sum(p.stat().st_size for p, _ in existentes) / 1024
    print(f"\n  Archivos a eliminar: {len(existentes)}  |  Espacio estimado: {total_kb:.1f} KB\n")
    print(f"  {'N':>3}  {'Archivo':<44}  Razon")
    print(f"  {SEP}")

    for i, (p, razon) in enumerate(existentes, 1):
        kb = p.stat().st_size / 1024
        print(f"  {i:>3}  {p.name:<44}  {razon}")
        print(f"       {'':44}  [{kb:.1f} KB]")

    print(f"\n  {SEP}")

    try:
        resp = input("\n  Eliminar estos archivos? (Y/N): ").strip().upper()
    except KeyboardInterrupt:
        print("\n\n  Operacion cancelada.")
        sys.exit(0)

    if resp != "Y":
        print("\n  Cancelado. No se elimino nada.")
        print("=" * 65 + "\n")
        sys.exit(0)

    print()
    ok, err = 0, 0
    for p, _ in existentes:
        try:
            p.unlink()
            print(f"  [BORRADO]  {p.name}")
            ok += 1
        except Exception as e:
            print(f"  [ERROR]    {p.name}: {e}")
            err += 1

    print()
    print("=" * 65)
    print(f"  Eliminados : {ok}")
    if err:
        print(f"  Errores    : {err}")
    print(f"  Espacio liberado: {total_kb:.1f} KB")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()

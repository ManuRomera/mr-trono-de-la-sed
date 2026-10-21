"""Compatibilidad: exportación artística unificada v3."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).with_name("art-v3.py")),run_name="__main__")

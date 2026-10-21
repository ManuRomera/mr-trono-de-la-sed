"""Entrada compatible: la edición editorial se construye desde el manuscrito Markdown."""
from pathlib import Path
import runpy,sys
if '--manual-only' in sys.argv:sys.argv[sys.argv.index('--manual-only')]='--manual'
runpy.run_path(str(Path(__file__).with_name('manual.py')),run_name='__main__')

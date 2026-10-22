#!/usr/bin/env python3
"""Genera arte nuevo delegando en Codex CLI (image_gen). Uso: python3 tools/gen_codex.py [--only id,id] [--jobs 3]
Lee docs/arte-v14.json y escribe art/new/<id>.png (reanudable). Copia siempre la imagen devuelta por la herramienta de esta sesión."""
import argparse, json, os, subprocess, time
from concurrent.futures import ThreadPoolExecutor
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL = "gpt-6.1-sol"

def valida(path, size):
    from PIL import Image
    try: w, h = Image.open(path).size
    except Exception: return False
    rw, rh = map(int, size.split("x")); return min(w, h) >= 900 and abs(w / h - rw / rh) < 0.2

def one(it, estilo):
    out = os.path.join("art", "new", it["id"] + ".png")
    extra = " The background MUST be transparent (alpha channel)." if it["tipo"] == "token" else ""
    prompt = ("Usa tu herramienta de generación de imágenes para crear UNA sola imagen, tamaño %s. Descripción: %s Estilo: %s%s\n"
              "Después copia EL PNG QUE TU HERRAMIENTA ACABA DE DEVOLVER EN ESTA SESIÓN (ruta exacta; nunca busques el archivo más reciente de la carpeta) a %s (crea la carpeta si falta) y responde solo con esa ruta. "
              "No generes más de una imagen ni modifiques otros archivos.") % (it["size"], it["prompt"], estilo, extra, out)
    t0 = time.time(); r = None
    for _ in range(2):
        r = subprocess.run(["codex", "exec", "-m", MODEL, "-c", 'model_reasoning_effort="low"', "--skip-git-repo-check", "-s", "workspace-write", prompt],
                           cwd=ROOT, capture_output=True, text=True, timeout=900, stdin=subprocess.DEVNULL)
        p = os.path.join(ROOT, out)
        if os.path.exists(p) and not valida(p, it["size"]): os.remove(p)
        if os.path.exists(p): return "OK  %-16s %4.0fs" % (it["id"], time.time() - t0)
    return "ERR %-16s %s" % (it["id"], (r.stdout + r.stderr)[-300:].replace("\n", " "))

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--only"); ap.add_argument("--file", default="arte-v14.json"); ap.add_argument("--jobs", type=int, default=1); a = ap.parse_args()
    cfg = json.load(open(os.path.join(ROOT, "docs", a.file))); os.makedirs(os.path.join(ROOT, "art", "new"), exist_ok=True)
    only = set(a.only.split(",")) if a.only else None
    todo = [i for i in cfg["imagenes"] if (not only or i["id"] in only) and not os.path.exists(os.path.join(ROOT, "art", "new", i["id"] + ".png"))]
    print("pendientes:", len(todo), flush=True)
    with ThreadPoolExecutor(a.jobs) as ex:
        for res in ex.map(lambda it: one(it, cfg["estilo"]), todo): print(res, flush=True)
    print("Hecho")

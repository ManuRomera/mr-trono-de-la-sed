"""Comprueba que el audio distribuido se decodifica, tiene señal y empalma sin clic."""
from pathlib import Path
import subprocess,json,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1];rows=[]
for a in json.loads((ROOT/'content/audio.json').read_text()):
 p=ROOT/a['path'];raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(p),'-f','f32le','-ac','2','-ar','48000','pipe:1']);x=np.frombuffer(raw,dtype='<f4').reshape(-1,2)
 peak=float(np.max(np.abs(x)));rms=float(np.sqrt(np.mean(x*x)));jump=float(np.max(np.abs(x[0]-x[-1])));deriv=float(np.quantile(np.abs(np.diff(x,axis=0)),.999))
 check={'file':a['path'],'seconds':len(x)/48000,'peak':peak,'rms':rms,'boundary_jump':jump,'ordinary_delta_p999':deriv,'loop':a['repeat'],'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'pass':peak<.99 and rms>.0001 and (not a['repeat'] or jump<max(.03,3*deriv))};rows.append(check)
print(json.dumps({'files':len(rows),'all_pass':all(r['pass'] for r in rows),'failed':[r for r in rows if not r['pass']]}));(ROOT/'docs/audio-validation.json').write_text(json.dumps(rows,indent=2));raise SystemExit(not all(r['pass'] for r in rows))

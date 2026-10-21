"""Prepara nueve bucles instrumentales acreditados y efectos originales sin voces."""
from pathlib import Path
import subprocess,json,wave,hashlib,math
import numpy as np
ROOT=Path(__file__).resolve().parents[1];SR=48000
MUSIC=[('muhar','Muhar al atardecer','Desert City','USUAN1100564'),('tumbas','Viento entre las tumbas','Echoes of Time v2','USUAN1300030'),('procesion','Procesión funeraria','Oppressive Gloom','USUAN1100885'),('laberinto','El Laberinto','Night of Chaos','USUAN1300042'),('banquete','El banquete','Ritual','USUAN1100466'),('merit','La negativa de Merit','Evening Fall (Harp)','USUAN1100236'),('pesaje','La Cámara del Pesaje','Dark Fog','USUAN1300031'),('coronacion','La coronación','Lightless Dawn','USUAN1100655'),('amanecer','El último amanecer','Evening Fall (Piano)','USUAN1100235')]
OUT=ROOT/'assets/audio';TMP=ROOT/'tmp/audio';TMP.mkdir(parents=True,exist_ok=True)
for d in ['music','sfx']:(OUT/d).mkdir(parents=True,exist_ok=True)
def probe(p):
 return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(p)]))
def stamp(p,**kw):
 d=probe(p);return dict(path=str(p.relative_to(ROOT)),seconds=float(d['format']['duration']),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),**kw)
records=[]
for slug,label,title,isrc in MUSIC:
 src=ROOT/'research/audio-sources'/(title+'.mp3');dest=OUT/'music'/(slug+'.ogg');duration=float(probe(src)['format']['duration'])
 # Recorte de introducción/cierre y solapamiento circular de seis segundos.
 end=duration-8;d=end-8;n=6
 f=f'[0:a]atrim=start=8:end={end},asetpts=PTS-STARTPTS,asplit=3[m][h][t];[m]atrim=start={n}:end={d-n},asetpts=PTS-STARTPTS[b];[h]atrim=end={n},asetpts=PTS-STARTPTS[head];[t]atrim=start={d-n},asetpts=PTS-STARTPTS[tail];[tail][head]acrossfade=d={n}:c1=qsin:c2=qsin[s];[b][s]concat=n=2:v=0:a=1,loudnorm=I=-26:TP=-4:LRA=6,aresample=48000[a]'
 subprocess.run(['ffmpeg','-y','-v','error','-i',str(src),'-filter_complex',f,'-map','[a]','-c:a','libopus','-b:a','96k',str(dest)],check=True)
 records.append(stamp(dest,slug=slug,name=label,kind='music',repeat=True,instrumental=True,title=title,author='Kevin MacLeod',source=f'https://incompetech.com/music/royalty-free/index.html?isrc={isrc}',license='CC BY 4.0',licenseUrl='https://creativecommons.org/licenses/by/4.0/',changes='Recorte de introducción/cierre, solapamiento circular de 6 s, normalización a -26 LUFS y codificación Ogg Opus.'))
 print(slug,flush=True)
rng=np.random.default_rng(370143)
def filtered_noise(sec,low=80,high=2000):
 n=round(sec*SR);x=rng.normal(size=n);spec=np.fft.rfft(x);freq=np.fft.rfftfreq(n,1/SR);mask=np.minimum(1,(freq/max(low,1))**2)/np.sqrt(1+(freq/high)**6);v=np.fft.irfft(spec*mask,n);return v/(np.std(v)+1e-9)
def env(x,attack=.15,release=.7):
 a=min(len(x),int(attack*SR));z=min(len(x),int(release*SR));x=x.copy();x[:a]*=np.linspace(0,1,a);x[-z:]*=np.linspace(1,0,z);return x
def ring(freq,sec,decay=2):
 t=np.arange(round(sec*SR))/SR;return sum(np.sin(2*np.pi*freq*p*t)*np.exp(-t*(i+1)/decay)/(i+1) for i,p in enumerate([1,2.756,5.404,8.93]))
def echo(x,delays=(.18,.37,.61),gains=(.23,.13,.07)):
 y=x.copy()
 for delay,g in zip(delays,gains):n=int(delay*SR);y[n:]+=x[:-n]*g
 return y
sfx={}
t=np.arange(SR*32)/SR
sfx['viento']=(env(filtered_noise(32,35,900)*(1+.3*np.sin(2*np.pi*t/11))),'Viento sobre la arena',True)
sfx['antorchas']=(env(filtered_noise(32,250,6200)*np.maximum(0,np.sin(2*np.pi*t*.71))*.16),'Antorchas',True)
sfx['piedra']=(env(echo(filtered_noise(5,45,1200)*np.exp(-np.arange(SR*5)/SR/2)),.2,1),'Puerta de piedra',False)
sfx['campana']=(env(echo(ring(147,7,3)),.005,1),'Campana funeraria',False)
sfx['vasija']=(env(echo(ring(425,3,.65)*.5+ring(697,3,.55)*.25),.004,.6),'Vasija de alabastro',False)
sfx['corazon']=(env(echo(ring(74,6,2)+ring(139,6,1.3)*.4),.02,1.4),'Latido del corazón cautivo',False)
sfx['sello']=(env(echo(filtered_noise(5,250,7000)*np.exp(-np.arange(SR*5)/SR/1.3)),.006,1.3),'Ruptura del sello',False)
sfx['pluma']=(env(echo(filtered_noise(4,1000,8500)*.13+ring(784,4,1)*.13),.6,1.4),'El testimonio permanece',False)
x=np.zeros(SR*6)
for i in range(7):
 n=int((.2+i*.67)*SR);q=env(filtered_noise(.18,55,1600)*np.exp(-np.arange(int(.18*SR))/SR/.055),.004,.08);x[n:n+len(q)]+=q
sfx['pasos']=(echo(x),'Pasos en la tumba',False)
x=np.zeros(SR*24)
for i in range(16):
 n=int(rng.uniform(.3,22)*SR);q=ring(rng.uniform(800,1600),1.5,.2)*.08;x[n:n+len(q)]+=q
sfx['agua']=(env(echo(x)),'Agua en la cámara',True)
for slug,(x,label,loop) in sfx.items():
 if loop:
  n=SR*2;x=np.concatenate((x[n:-n],x[-n:]*np.linspace(1,0,n)+x[:n]*np.linspace(0,1,n)))
 # Techo prudente; los efectos se disparan a volumen moderado en Foundry.
 x=x/(np.max(np.abs(x))+1e-9)*.35;stereo=np.stack((x,np.roll(x,37)*.96),axis=1);wav=TMP/(slug+'.wav')
 with wave.open(str(wav),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR);w.writeframes((stereo*32767).astype('<i2').tobytes())
 dest=OUT/'sfx'/(slug+'.ogg');subprocess.run(['ffmpeg','-y','-v','error','-i',str(wav),'-c:a','libopus','-b:a','96k',str(dest)],check=True)
 records.append(stamp(dest,slug=slug,name=label,kind='sfx',repeat=loop,author='Proyecto MR · Manuel Romera',license='CC BY-NC-SA 4.0',method='Diseño sonoro sintetizado, sin voces ni muestras externas.'))
(ROOT/'content/audio.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
text='# Créditos de audio\n\nLas nueve piezas instrumentales son de Kevin MacLeod (incompetech.com), bajo Creative Commons Attribution 4.0: https://creativecommons.org/licenses/by/4.0/. Se han recortado, adaptado para repetición y normalizado; sus nombres originales se conservan a continuación. No son composiciones originales del Proyecto MR.\n\n'
for d in records:
 if d['kind']=='music':text+=f'- **{d["name"]}**: «{d["title"]}» — Kevin MacLeod. [Ficha y licencia]({d["source"]}). {d["changes"]}\n'
text+='\nLos diez efectos son síntesis originales del Proyecto MR, sin voces ni muestras externas. Licencia CC BY-NC-SA 4.0.\n'
(ROOT/'AUDIO-CREDITS.md').write_text(text);print('19 audios reales terminados',flush=True)

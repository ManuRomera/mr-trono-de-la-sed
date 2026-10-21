"""Cartografía vectorial original con geometría compartida por los muros Foundry."""
from pathlib import Path
import json,html
root=Path(__file__).resolve().parents[1]
# Las interrupciones entre segmentos son accesos reales; no hay puertas dibujadas sobre muros cerrados.
rooms=[('Vestíbulo',300,700,400,250),('Banquete',800,650,700,350),('Galería',250,200,500,300),('Dormitorio',900,150,450,300),('Vasijas',1550,200,450,300),('Inscripción',1600,650,400,300),('Pesaje',800,1150,700,350)]
segments=[];parts=[]
for i,(name,x,y,w,h) in enumerate(rooms,1):
 # Dos accesos centrados en lados norte y sur, corredores sin obstáculos.
 gap=100;mid=x+w/2
 for c in [[x,y,mid-gap/2,y],[mid+gap/2,y,x+w,y],[x,y,x,y+h],[x+w,y,x+w,y+h],[x,y+h,mid-gap/2,y+h],[mid+gap/2,y+h,x+w,y+h]]:segments.append(c)
 parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#d7c8a6"/><text x="{mid}" y="{y+h/2}" text-anchor="middle">{i}</text>')
svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="2300" height="1700" viewBox="0 0 2300 1700"><rect width="2300" height="1700" fill="#1f202a"/><style>text{{font:36px Georgia;fill:#24212a}}.title{{font:42px Georgia;fill:#d9c08a}}</style><text x="1150" y="80" text-anchor="middle" class="title">LA CORTE DE LAS SIETE LENGUAS</text><path d="M500 200V1100H1800V200M1150 150V1500" stroke="#d7c8a6" stroke-width="110" fill="none"/>{''.join(parts)}<g stroke="#504332" stroke-width="12" stroke-linecap="square">{''.join(f'<path d="M{a} {b}L{c} {d}"/>' for a,b,c,d in segments)}</g><text x="90" y="1620" class="title">N ↑ · Plano de orientación · Sin escala métrica</text></svg>'''
(root/'assets/maps/corte.svg').write_text(svg)
(root/'content').mkdir(exist_ok=True)
(root/'content/maps.json').write_text(json.dumps({'corte':{'width':2300,'height':1700,'walls':segments,'rooms':[{'number':i,'name':r[0],'center':[r[1]+r[3]/2,r[2]+r[4]/2]} for i,r in enumerate(rooms,1)]}},ensure_ascii=False,indent=2))
# Plano urbano original de las localizaciones de la aventura; no pretende ser mapa canónico.
points=[('Plaza del funeral',350,350),('Archivo de Panehsy',1050,250),('Taller de Tia',400,850),('Casa de Nefru',1200,800),('Camino al pozo',1700,550)]
parts=['<rect width="2000" height="1200" fill="#e9ddc1"/>','<path d="M350 350L1050 250L1700 550L1200 800L400 850L350 350M350 350L1200 800M1050 250L1200 800" fill="none" stroke="#ae9670" stroke-width="55"/>']
for name,x,y in points:parts += [f'<rect x="{x-95}" y="{y-65}" width="190" height="130" rx="10" fill="#393341" stroke="#9c7c46" stroke-width="8"/>',f'<text x="{x}" y="{y+115}" text-anchor="middle">{name}</text>']
(root/'assets/maps/muhar.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" width="2000" height="1200"><style>text{font:30px Georgia;fill:#2a2330}</style>'+''.join(parts)+'<text x="70" y="80">MUHAR · Rutas de investigación · Plano original sin escala</text><text x="70" y="1140">N ↑ · Calles transitables; el peligro depende de la situación y las decisiones</text></svg>')
import math
parts=['<rect width="1400" height="1400" fill="#282936"/>','<circle cx="700" cy="700" r="480" fill="#d3c3a0" stroke="#a88a50" stroke-width="20"/>','<circle cx="700" cy="700" r="300" fill="#252632" stroke="#927c52" stroke-width="16"/>']
for i in range(7):
 angle=-math.pi/2+i*math.tau/7;x=700+385*math.cos(angle);y=700+385*math.sin(angle)
 parts.append(f'<rect x="{x-38}" y="{y-64}" width="76" height="128" rx="28" fill="'+('#8b2b3b' if i<6 else '#eee4cf')+'" stroke="#564735" stroke-width="8"/>')
parts += ['<path d="M640 1190V1410H760V1190" fill="#d3c3a0" stroke="#927c52" stroke-width="10"/>','<text x="700" y="690" text-anchor="middle">Descenso al Laberinto</text>','<text x="700" y="140" text-anchor="middle">EL POZO · Seis marcas y un hueco limpio</text>']
(root/'assets/maps/pozo.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="1400"><style>text{font:30px Georgia;fill:#e9dfc8}</style>'+''.join(parts)+'</svg>')

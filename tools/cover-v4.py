"""Portada tipográfica vectorial, sin modificar la ilustración aprobada."""
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor,Color
from pathlib import Path
from PIL import Image
from reportlab.lib.utils import ImageReader
ROOT=Path(__file__).resolve().parents[1]
for weight in ['Regular','Bold','Black']:
 pdfmetrics.registerFont(TTFont('Cinzel'+weight,str(ROOT/f'editorial/fonts/cinzel/CinzelDecorative-{weight}.ttf')))
def tracked(c,text,y,font,size,tracking,color,width):
 length=pdfmetrics.stringWidth(text,font,size)+tracking*(len(text)-1)
 t=c.beginText((width-length)/2,y);t.setFont(font,size);t.setCharSpace(tracking);t.setFillColor(color);t.textOut(text);c.drawText(t)
def cover(c,W,H,kind):
 # Oscurecimiento progresivo en el pie para dar contraste sin ocultar el rostro.
 gradient=Image.new('RGBA',(2,1024))
 gradient.putdata([(5,6,10,round(237*(i/1023)**.55)) for i in range(1024) for _ in range(2)])
 c.drawImage(ImageReader(gradient),0,0,W,420,mask='auto')
 gold=HexColor('#c8a46d');bone=HexColor('#f5ecd7');red=HexColor('#742731')
 tracked(c,'UNA AVENTURA DE HORROR GÓTICO',H-31,'BodyBold',9.5,2,gold,W)
 tracked(c,'EL',335,'CinzelRegular',17,5,gold,W)
 # Sombra mínima de registro y tinta clara; el título mantiene contornos nítidos.
 tracked(c,'TRONO',267,'CinzelBlack',66,3,red,W)
 tracked(c,'TRONO',270,'CinzelBlack',66,3,bone,W)
 tracked(c,'DE LA',235,'CinzelRegular',16,6,gold,W)
 tracked(c,'SED',157,'CinzelBlack',82,7,red,W)
 tracked(c,'SED',160,'CinzelBlack',82,7,bone,W)
 # Filetes funerarios y un sello romboidal vectorial, sin ilustraciones añadidas.
 cx=W/2;c.setStrokeColor(gold);c.setLineWidth(.65)
 for xa,xb in [(85,cx-11),(cx+11,W-85)]:c.line(xa,137,xb,137)
 p=c.beginPath();p.moveTo(cx,142);p.lineTo(cx+5,137);p.lineTo(cx,132);p.lineTo(cx-5,137);p.close();c.setFillColor(red);c.drawPath(p,fill=1,stroke=1)
 tracked(c,'LA CORTE DEL REY SIN NOMBRE',112,'CinzelBold',11.3,.8,gold,W)
 tracked(c,'MANUEL ROMERA',70,'CinzelBold',12,2.2,bone,W)
 tracked(c,kind.upper()+' · LEGEND IN THE MIST',45,'Body',9.3,1,gold,W)

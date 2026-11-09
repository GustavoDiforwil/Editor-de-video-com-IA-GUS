"""Recorta as folhas de assets do usuário (assets/assets do narrando jogos) em peças soltas com fundo transparente, em assets/jogos-narrado/imagens/colagem."""
import os
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
from collections import deque
RAIZ=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # pasta do projeto (acima de ferramentas/)
D=os.path.join(RAIZ,"assets","assets do narrando jogos")
OUT=os.path.join(RAIZ,"assets","jogos-narrado","imagens","colagem"); os.makedirs(OUT,exist_ok=True)
for f in os.listdir(OUT): os.remove(os.path.join(OUT,f))
def fundo(arr,cor,tol):
    """Fundo = o que encosta na borda e tem a cor do fundo; branco fechado dentro da peça fica."""
    d=np.abs(arr[...,:3].astype(int)-cor).max(2)<=tol
    h,w=d.shape; v=np.zeros((h,w),bool); q=deque()
    for x in range(w):
        for y in(0,h-1):
            if d[y,x] and not v[y,x]: v[y,x]=True;q.append((y,x))
    for y in range(h):
        for x in(0,w-1):
            if d[y,x] and not v[y,x]: v[y,x]=True;q.append((y,x))
    while q:
        y,x=q.popleft()
        for a,b in((y+1,x),(y-1,x),(y,x+1),(y,x-1)):
            if 0<=a<h and 0<=b<w and d[a,b] and not v[a,b]: v[a,b]=True;q.append((a,b))
    return v
def componentes(m,area_min):
    k=3;h,w=m.shape; p=m[:h//k*k,:w//k*k].reshape(h//k,k,w//k,k).max((1,3)); H,W=p.shape; lab=np.zeros((H,W),int);c=0;res=[]
    for y,x in zip(*np.nonzero(p)):
        if lab[y,x]: continue
        c+=1;q=deque([(y,x)]);lab[y,x]=c;n=0;x0=x1=x;y0=y1=y
        while q:
            u,v=q.popleft();n+=1;x0=min(x0,v);x1=max(x1,v);y0=min(y0,u);y1=max(y1,u)
            for a,b in((u+1,v),(u-1,v),(u,v+1),(u,v-1)):
                if 0<=a<H and 0<=b<W and p[a,b] and not lab[a,b]: lab[a,b]=c;q.append((a,b))
        if n*k*k>=area_min: res.append((c,x0,y0,x1,y1))
    return lab,k,res
def salvar(arr,alfa,nome):
    al=Image.fromarray(np.uint8(alfa*255)).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.7))
    im=Image.fromarray(arr[...,:3]).convert("RGBA"); im.putalpha(al); im=im.crop(al.getbbox()); im.save(os.path.join(OUT,nome)); return nome
todos=[]
for arq,pre,cor,tol,amin in (("download.png","a",(255,255,255),6,1500),("download (1).png","b",(255,255,255),6,1500),
                             ("assets 1.png","c",(228,228,228),10,1500),("assets 2.png","d",(255,255,255),8,1500)):  # c, d: folhas de 02/11 (Death Stranding)
    arr=np.asarray(Image.open(os.path.join(D,arq)).convert("RGBA")); m=~fundo(arr,cor,tol)
    lab,k,res=componentes(m,amin); big=np.kron(lab,np.ones((k,k),int)); h,w=big.shape
    for i,(c,x0,y0,x1,y1) in enumerate(res):
        Y0,Y1,X0,X1=y0*k,(y1+1)*k,x0*k,(x1+1)*k
        todos.append(salvar(arr[Y0:Y1,X0:X1],(big[Y0:Y1,X0:X1]==c)&m[:h,:w][Y0:Y1,X0:X1],f"{pre}{i:02d}.png"))
for arq,nome,cor,tol in (("download (4).png","ovni.png",(128,128,128),6),("e45df6ce024aa66be07a2f351d22e9fa.jpg","interrogacao.png",(255,255,255),18),("e657d7603b899cfe4a8c409d4fc5ed55.jpg","dont-panic.png",(255,255,255),18),
                     ("assets 3.jpg","olho.png",(255,255,255),18),("assets 4.jpg","tv-cabeca.png",(255,255,255),18),("assets 5.jpg","celular-maos.png",(255,255,255),18)):
    arr=np.asarray(Image.open(os.path.join(D,arq)).convert("RGBA")); m=~fundo(arr,cor,tol); todos.append(salvar(arr,m,nome))
# alfabeto: caixa de cada letra (coordenadas da folha 1152x2048)
LET={"A":(55,15,320,310),"B":(355,18,525,345),"C":(575,55,812,310),"D":(838,55,1104,316),"E":(30,328,272,610),"F":(318,376,520,602),"G":(545,365,828,650),"H":(852,335,1076,606),
"I":(70,632,234,884),"J":(326,636,512,928),"K":(586,660,808,892),"L":(860,644,1094,886),"M":(45,946,280,1182),"N":(330,948,622,1150),"O":(656,944,866,1152),"P":(916,926,1102,1184),
"Q":(50,1212,290,1450),"R":(368,1176,574,1446),"S":(612,1174,846,1446),"T":(882,1212,1125,1456),"U":(56,1458,300,1698),"V":(350,1478,586,1712),"W":(646,1474,836,1696),"X":(884,1478,1096,1720),
"Y":(86,1730,284,1994),"Z":(346,1732,602,1984)}
al=Image.open(os.path.join(D,"download (2).png")).convert("RGB"); e=1152/1125
for L,(x0,y0,x1,y1) in LET.items():
    pc=np.asarray(al.crop((int(x0*e),int(y0*e),int(x1*e),int(y1*e))).convert("RGBA"))
    if L in "UV":  # papel claro demais para separar do fundo pela cor: fica o recorte reto (mal cortado de propósito)
        Image.fromarray(pc).save(os.path.join(OUT,f"letra_{L}.png"))
    else:
        m=~fundo(pc,(248,239,231),30)
        ma=Image.fromarray(np.uint8(m*255)).filter(ImageFilter.MinFilter(7)).filter(ImageFilter.MaxFilter(7))  # some com as linhas finas do quadriculado
        salvar(pc,np.asarray(ma)>127,f"letra_{L}.png")
    todos.append(f"letra_{L}.png")
cw,ch=200,200;cols=9;rows=(len(todos)+cols-1)//cols
S=Image.new("RGB",(cw*cols,ch*rows),(90,150,110));dr=ImageDraw.Draw(S)
for i,f in enumerate(todos):
    p=Image.open(os.path.join(OUT,f)).convert("RGBA");p.thumbnail((cw-10,ch-26));x,y=i%cols*cw+5,i//cols*ch+20;S.paste(p,(x,y),p);dr.text((x,y-16),f,fill=(255,255,255))
S.save(os.path.join(OUT,"_conferir.jpg"),quality=88);print(len(todos))

from PIL import Image,ImageDraw
files=list(__import__('pathlib').Path('video/out/qa-style').glob('old-*.png'))
files=sorted(files,key=lambda p:int(p.stem.split('-')[1]))
s=Image.new('RGB',(1920,1200),'white');d=ImageDraw.Draw(s)
for i,p in enumerate(files):
 x=(i%4)*480;y=(i//4)*300;s.paste(Image.open(p).resize((480,270)),(x,y));d.text((x+6,y+276),p.stem,fill='black')
s.save('video/out/qa-style/old-contact.png')


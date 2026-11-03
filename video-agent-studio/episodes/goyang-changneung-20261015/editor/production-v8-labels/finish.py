from pathlib import Path
import psutil,subprocess,json
E=Path(__file__).resolve().parent;R=E.parents[4]
for p in psutil.process_iter(['name']):
 try:
  if p.info['name']=='node.exe' and any('production-v8-labels/render.cjs' in x for x in p.cmdline()):p.wait(timeout=1200)
 except psutil.Error:pass
subprocess.run([str(R/'tools/python311/python.exe'),'-X','utf8',str(E/'assemble.py')],check=True)

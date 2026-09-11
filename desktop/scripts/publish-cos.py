"""Publish built artifacts with short-lived PUT URLs; publish latest.yml last.
CINE_LAB_CONNECTION_DIR points to an external module providing connect() and run().
The connection module owns SSH authentication; no credential is stored in this repo.
"""
import os,sys,json,hashlib,base64,shlex,urllib.request
from pathlib import Path
sys.path.insert(0,os.environ['CINE_LAB_CONNECTION_DIR'])
from lab_connection import connect,run
root=Path(__file__).resolve().parents[1]
version=json.loads((root/'package.json').read_text(encoding='utf-8'))['version']
names=[f'Avatar-Forge-{version}-Windows-x64-Setup.exe',f'Avatar-Forge-{version}-Windows-x64-Setup.exe.blockmap','latest.yml']
release=root/'release'/version
files=[{'name':n,'size':(release/n).stat().st_size} for n in names]
manifest=(release/'latest.yml').read_text(encoding='utf-8')
expected=base64.b64encode(hashlib.sha512((release/names[0]).read_bytes()).digest()).decode()
assert f'version: {version}' in manifest and expected in manifest and names[0] in manifest
origin='https://prod-lab-1321001571.cos.ap-guangzhou.myqcloud.com/releases/avatar-forge/windows/x64/'
c=connect()
def rpc(mode,items):
 value=json.dumps({'mode':mode,'files':items},separators=(',',':'))
 return json.loads(run(c,'docker exec lycheeailab-api-1 node /tmp/cine-cos-release.cjs '+shlex.quote(value)))
try:
 with c.open_sftp() as s:s.put(str(root/'scripts/cos-release.cjs'),'/tmp/cine-cos-release.cjs')
 run(c,'docker cp /tmp/cine-cos-release.cjs lycheeailab-api-1:/tmp/cine-cos-release.cjs')
 urls=rpc('prepare',files)
 for item in files:
  name=item['name']
  if name=='latest.yml':
   # Verify the public executable before moving the stable channel pointer.
   digest=hashlib.sha512()
   with urllib.request.urlopen(origin+names[0],timeout=90) as response:
    while chunk:=response.read(4*1024*1024):digest.update(chunk)
   assert base64.b64encode(digest.digest()).decode()==expected
  request=urllib.request.Request(urls[name],data=(release/name).read_bytes(),method='PUT',headers={'Content-Type':'text/yaml' if name.endswith('.yml') else 'application/octet-stream','Cache-Control':'no-cache, max-age=0, must-revalidate' if name.endswith('.yml') else 'public, max-age=31536000, immutable'})
  with urllib.request.urlopen(request,timeout=600) as response:assert response.status==200
  rpc('expose',[item]);print('Published '+name,flush=True)
 with urllib.request.urlopen(origin+'latest.yml',timeout=30) as response:assert response.read().decode('utf-8')==manifest
 print('Stable channel verified: '+origin+'latest.yml',flush=True)
finally:c.close()

const {app,BrowserWindow}=require('electron');
const fs=require('node:fs');const path=require('node:path');
app.setPath('userData',path.join(app.getPath('temp'),'avatar-forge-preview-qa'));
app.whenReady().then(async()=>{try{
 const w=new BrowserWindow({show:false,webPreferences:{sandbox:true,contextIsolation:true,nodeIntegration:false}});
 await w.loadFile(path.join(__dirname,'src/index.html'));
 const out=path.join(app.getPath('temp'),'avatar-forge-ui-qa');fs.mkdirSync(out,{recursive:true});
 for(const [width,height] of [[1280,880],[980,680],[390,844]]){
  w.setContentSize(width,height);await new Promise(r=>setTimeout(r,150));
  const ok=await w.webContents.executeJavaScript('document.documentElement.scrollWidth <= innerWidth');if(!ok)throw Error('Overflow '+width);
  fs.writeFileSync(path.join(out,`${width}.png`),(await w.webContents.capturePage()).toPNG());
  console.log(await w.webContents.executeJavaScript(`(()=>{const bar=document.querySelector('.af-topbar');const before=bar.getBoundingClientRect().toJSON();document.querySelector('[data-page="history"]').click();const after=bar.getBoundingClientRect().toJSON();for(const key of ['x','y','width','height'])if(Math.abs(before[key]-after[key])>1)throw Error('Navigation layout shift: '+key);return 'PASS stable topbar '+innerWidth;})()`));
  fs.writeFileSync(path.join(out,`${width}-history.png`),(await w.webContents.capturePage()).toPNG());
  await w.webContents.executeJavaScript("document.getElementById('back-studio').click()");
 }
 const result=await w.webContents.executeJavaScript(`(async()=>{
 document.querySelector('[data-person="video"]').click();
 if(!document.getElementById('person-route').textContent.includes('无需'))throw Error('Video branch');
 document.querySelector('[data-voice="audio"]').click();
 if(!document.getElementById('script-section').hidden)throw Error('Script not hidden');
 document.getElementById('simulate').click();
 if(document.getElementById('toast').hidden)throw Error('Missing validation');
 document.getElementById('login').click();if(!document.getElementById('notice').open)throw Error('Dialog');
 document.getElementById('acknowledge').click();if(document.getElementById('notice').open)throw Error('Close');
 document.querySelector('[data-page="history"]').click();if(document.getElementById('history').hidden)throw Error('History');
 document.getElementById('back-studio').click();
 document.querySelector('[data-person="image"]').click();document.querySelector('[data-voice="clone"]').click();
 return 'PASS branches, input validation, dialog, history, three viewport overflow';})()`);
 console.log(result);console.log(out);app.exit(0);
 }catch(e){console.error(e);app.exit(1)}});

const {app,BrowserWindow,ipcMain}=require('electron'),path=require('node:path'),fs=require('node:fs');
app.setPath('userData',path.join(app.getPath('temp'),'avatar-library-qa'));
app.whenReady().then(async()=>{try{
 ipcMain.handle('avatar:status',()=>({ok:true,data:{user:{id:'test',displayName:'测试账户'}}}));
 ipcMain.handle('avatar:updates',()=>({ok:true,data:{status:'disabled',currentVersion:'dev'}}));
 ipcMain.handle('avatar:library',()=>({ok:true,data:{models:[{id:'m',name:'示例模特',status:'ready',ready:true},{id:'pending',name:'制作中',status:'template_queued',ready:false}],voices:[{id:'v',name:'我的音色',status:'completed',ready:true}]}}));
 ipcMain.handle('avatar:renameAsset',(_,x)=>({ok:true,data:{ok:true}}));
 const source=process.env.AVATAR_QA_SOURCE||path.join(__dirname,'src');
 const w=new BrowserWindow({show:false,webPreferences:{preload:path.join(source,'preload.cjs'),sandbox:true,contextIsolation:true}});await w.loadFile(path.join(source,'index.html'));
 const out=path.join(app.getPath('temp'),'avatar-library-qa-images');fs.mkdirSync(out,{recursive:true});
 for(const width of [1280,980,390]){w.setContentSize(width,880);await new Promise(r=>setTimeout(r,100));
 const before=await w.webContents.executeJavaScript("document.querySelector('.af-topbar').getBoundingClientRect().height");
 await w.webContents.executeJavaScript("document.querySelector('[data-page=models]').click()");await new Promise(r=>setTimeout(r,150));
 if(!await w.webContents.executeJavaScript(`document.documentElement.scrollWidth<=innerWidth&&document.querySelector('.af-topbar').getBoundingClientRect().height===${before}&&document.querySelectorAll('.af-library-card').length===2&&document.querySelectorAll('.af-library-actions button')[2].disabled`))throw Error('Library geometry/status '+width);
 fs.writeFileSync(path.join(out,width+'.png'),(await w.webContents.capturePage()).toPNG());
 await w.webContents.executeJavaScript("document.querySelector('.af-library-actions button').click()");await new Promise(r=>setTimeout(r,150));
 if(!await w.webContents.executeJavaScript("document.getElementById('library').hidden&&document.getElementById('person-drop').hidden&&window.avatarLibrary.selection().modelId==='m'"))throw Error('Selection lost');
 await w.webContents.executeJavaScript("document.querySelector('[data-page=voices]').click()");await new Promise(r=>setTimeout(r,150));await w.webContents.executeJavaScript("document.querySelector('.af-library-actions button').click()");await new Promise(r=>setTimeout(r,150));
 if(!await w.webContents.executeJavaScript("!document.getElementById('script-section').hidden&&window.avatarLibrary.selection().voiceId==='v'"))throw Error('Voice selection');
 }
 w.webContents.send('avatar:auth',{user:null});await new Promise(r=>setTimeout(r,100));if(!await w.webContents.executeJavaScript("window.avatarLibrary.selection().modelId===''&&document.querySelectorAll('.af-library-card').length===0"))throw Error('Logout data retained');
 console.log('PASS library navigation, selection, disabled states, logout and three sizes; simulated data only');console.log(out);app.exit(0)
 }catch(e){console.error(e);app.exit(1)}});

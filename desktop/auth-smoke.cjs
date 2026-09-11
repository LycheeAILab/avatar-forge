const {app,BrowserWindow,ipcMain}=require('electron');
const path=require('node:path');
app.setPath('userData',path.join(app.getPath('temp'),'avatar-auth-smoke'));
app.whenReady().then(async()=>{try{
 ipcMain.handle('avatar:status',()=>({ok:true,data:{user:{id:'test',displayName:'测试账户'}}}));
 ipcMain.handle('avatar:updates',()=>({ok:true,data:{status:'disabled',currentVersion:'test'}}));
 ipcMain.handle('avatar:history',()=>({ok:true,data:{items:[{id:'example',title:'测试口播',status:'paused',stage:2,createdAt:new Date().toISOString()}],cloud:[]}}));
 const win=new BrowserWindow({show:false,webPreferences:{preload:path.join(__dirname,'src/preload.cjs'),sandbox:true,contextIsolation:true,nodeIntegration:false}});
 await win.loadFile(path.join(__dirname,'src/index.html'));
 await new Promise(r=>setTimeout(r,150));
 const ok=await win.webContents.executeJavaScript("typeof require==='undefined' && !!window.avatarAuth && document.getElementById('login').textContent.includes('测试账户') && !('tokens' in window.avatarAuth)");
 if(!ok)throw Error('Preload/auth UI failed');
 await win.webContents.executeJavaScript("document.querySelector('[data-page=history]').click()");await new Promise(r=>setTimeout(r,100));
 if(!await win.webContents.executeJavaScript("document.querySelector('.af-history-row').textContent.includes('测试口播')"))throw Error('History UI failed');
 win.webContents.send('avatar:auth',{user:null});await new Promise(r=>setTimeout(r,100));
 if(!await win.webContents.executeJavaScript("document.getElementById('login').textContent.includes('登录 LycheeAILab')"))throw Error('Logout UI failed');
 console.log('PASS native sandbox/preload/account/history/anonymous state; mock identity only');app.exit(0);
 }catch(e){console.error(e);app.exit(1)}});

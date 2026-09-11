const {app,BrowserWindow,nativeTheme,ipcMain,safeStorage,shell,dialog,protocol,net}=require('electron');
const {randomUUID}=require('node:crypto');
const {Pipeline,mime}=require('./pipeline.cjs');
const {Updates}=require('./updates.cjs');
const {autoUpdater}=require('electron-updater');
protocol.registerSchemesAsPrivileged([{scheme:'avatar-media',privileges:{standard:true,secure:true,supportFetchAPI:true,stream:true}}]);
const path=require('node:path'),fs=require('node:fs/promises'),os=require('node:os');
const {pathToFileURL}=require('node:url');
const {LabClient}=require('./lab-client.cjs');
const {SCHEME,CLIENT,labOrigin,beginLogin,acceptCallback}=require('./auth.cjs');
app.setName('Avatar Forge');
app.setPath('userData',path.join(app.getPath('appData'),'avatar-forge-preview'));
const base=labOrigin(process.env.AVATAR_FORGE_LAB_URL,app.isPackaged);
const page=pathToFileURL(path.join(__dirname,'index.html')).href;
let win,client,engine,user=null,pending=null,busy=false;
const files=new Map();
const notify=event=>{if(win&&!win.isDestroyed())win.webContents.send('avatar:auth',event)};
async function callback(value){
 if(!client||busy||engine?.running)return;
 try{const input=acceptCallback(value,pending);pending=null;busy=true;await client.exchange(input);user=(await client.api('/api/desktop-auth/me')).user;notify({user});if(win.isMinimized())win.restore();win.show();win.focus();}
 catch(error){notify({error:error.message})}finally{busy=false}
}
if(!app.requestSingleInstanceLock())app.quit();
else{
 app.on('second-instance',(_,args)=>{const value=args.find(a=>a.startsWith(`${SCHEME}:`));if(value)void callback(value);if(win){if(win.isMinimized())win.restore();win.show();win.focus()}});
 app.whenReady().then(async()=>{
  nativeTheme.themeSource='light';
  const root=app.getPath('userData');await fs.mkdir(root,{recursive:true});const file=path.join(root,'desktop-session.enc');
  const storage={
   async read(){try{if(!safeStorage.isEncryptionAvailable())return null;const saved=JSON.parse(safeStorage.decryptString(await fs.readFile(file)));return saved.origin===base&&saved.clientId===CLIENT?saved.tokens:null}catch{return null}},
   async write(tokens){if(!safeStorage.isEncryptionAvailable())throw Error('Windows安全存储不可用，无法保存登录');await fs.writeFile(file+'.tmp',safeStorage.encryptString(JSON.stringify({origin:base,clientId:CLIENT,tokens})));await fs.rename(file+'.tmp',file)},
   async clear(){await fs.rm(file,{force:true})}
  };
  client=new LabClient(base,storage);await client.initialize();
  if(app.isPackaged)app.setAsDefaultProtocolClient(SCHEME);else app.setAsDefaultProtocolClient(SCHEME,process.execPath,[path.resolve(__dirname,'..')]);
  engine=new Pipeline({client,root:path.join(root,'tasks'),driver:app.isPackaged?path.join(process.resourcesPath,'template-driver.wav'):path.resolve(__dirname,'../../plugins/avatar-forge/skills/avatar-forge-pipeline/assets/template-driver.wav'),notify:value=>win?.webContents.send('avatar:task',value)});
  const identity=async()=>{user=(await client.api('/api/desktop-auth/me')).user;return user.id};
  const idle=()=>{if(engine.running||busy)throw Error('请先暂停当前制作')};
  const updates=new Updates({updater:autoUpdater,version:app.getVersion(),enabled:app.isPackaged&&Number(app.getVersion().split('.')[0])>=1,busy:()=>busy||engine.running||Boolean(pending&&pending.expiresAt>Date.now())});
  updates.on('state',state=>win?.webContents.send('avatar:update',state));
  app.on('before-quit',()=>updates.stop());
  protocol.handle('avatar-media',async request=>{try{const url=new URL(request.url);if(!user||url.host!=='result'||url.search||url.hash)return new Response('',{status:403});const id=url.pathname.slice(1);const file=path.join(engine.dir(user.id,id),'final.mp4');const s=JSON.parse(await fs.readFile(path.join(engine.dir(user.id,id),'state.json'),'utf8'));if(s.status!=='completed')return new Response('',{status:404});return net.fetch(pathToFileURL(file).href,{headers:request.headers})}catch{return new Response('',{status:404})}});
  function handle(name,fn){ipcMain.handle('avatar:'+name,async(event,...args)=>{
   if(event.sender!==win.webContents||event.senderFrame!==win.webContents.mainFrame||event.senderFrame.url!==page)throw Error('请求来源无效');
   try{return {ok:true,data:await fn(...args)}}catch(error){return {ok:false,error:error.message}}
  })}
  handle('status',async()=>{if(!client.tokens)return {user:null};try{user=(await client.api('/api/desktop-auth/me')).user;return {user}}catch(error){user=null;if(error.status===401)return {user:null};throw error}});
  handle('updates',async()=>updates.state);
  handle('checkUpdates',async()=>{void updates.check();return updates.state});
  handle('installUpdate',async()=>{updates.install();return {ok:true}});
  handle('login',async()=>{idle();if(pending&&pending.expiresAt>Date.now())throw Error('请在已打开的浏览器完成授权，或稍后重新登录');pending=beginLogin(base,os.hostname());try{await shell.openExternal(pending.url)}catch(error){pending=null;throw error}return {message:'请在系统浏览器完成 Lab 登录与授权'}});
  handle('logout',async()=>{idle();busy=true;pending=null;try{await client.logout();user=null;files.clear();notify({user:null});return {user:null}}finally{busy=false}});
  handle('register',async file=>{if(typeof file!=='string'||!path.isAbsolute(file)||!mime(file))throw Error('素材格式不支持');const stat=await fs.stat(file);if(!stat.isFile()||!stat.size||stat.size>600*1024*1024)throw Error('素材大小无效');const token=randomUUID();files.set(token,{path:file,size:stat.size});return {token}});
  handle('library',async()=>{await identity();return client.api('/api/avatar-forge/library')});
  handle('renameAsset',async({kind,id,name,mediaToken})=>{await identity();if(!['model','voice'].includes(kind)||typeof id!=='string')throw Error('资产无效');const file=mediaToken?files.get(mediaToken):null;if(mediaToken&&(!file||file.size>15*1024*1024))throw Error('素材无效');const body=await engine.form({name},file?{media:file.path}:{});return client.api('/api/avatar-forge/library/'+kind+'/'+encodeURIComponent(id),{method:'POST',body})});
  handle('create',async input=>{idle();busy=true;try{
   const uid=await identity(),p=files.get(input.personToken),v=files.get(input.voiceToken);
   if(input.person!=='saved'&&(!p||!mime(p.path).startsWith(input.person==='image'?'image/':'video/')||p.size>(input.person==='image'?15:600)*1024*1024))throw Error('请重新选择有效人物素材');
   if(input.voice!=='saved'&&(!v||!mime(v.path).startsWith('audio/')||v.size>(input.voice==='clone'?15:100)*1024*1024))throw Error('请重新选择有效声音素材');
   let coverPath;
   if(input.person==='video'&&typeof input.cover==='string'&&/^data:image\/png;base64,[A-Za-z0-9+/=]+$/.test(input.cover)&&input.cover.length<3*1024*1024){coverPath=path.join(root,'cover-'+randomUUID()+'.png');await fs.writeFile(coverPath,Buffer.from(input.cover.split(',')[1],'base64'))}
   let state;try{state=await engine.create(uid,{person:input.person,voice:input.voice,script:input.script,consent:input.consent,modelId:input.modelId,voiceId:input.voiceId,personPath:p?.path,voicePath:v?.path,coverPath})}finally{if(coverPath)await fs.rm(coverPath,{force:true})}
   void engine.resume(uid,state.id).catch(()=>{});return engine.public(state)
  }finally{busy=false}});
  handle('resume',async id=>{idle();busy=true;try{const uid=await identity();void engine.resume(uid,id).catch(e=>win?.webContents.send('avatar:task',{error:e.message,status:'paused'}));return {ok:true}}finally{busy=false}});
  handle('pause',async()=>{engine.stopped=true;return {message:'将在当前提交完成后暂停；云端任务不会取消'}});
  handle('history',async()=>{const uid=await identity();return {items:await engine.list(uid),cloud:(await client.api('/api/avatar-forge/desktop-history')).items}});
  handle('export',async id=>{const uid=await identity();const state=JSON.parse(await fs.readFile(path.join(engine.dir(uid,id),'state.json'),'utf8'));if(state.status!=='completed')throw Error('视频尚未完成');const result=await dialog.showSaveDialog(win,{defaultPath:'Avatar-Forge-'+id+'.mp4',filters:[{name:'视频',extensions:['mp4']}]});if(!result.canceled){await fs.copyFile(path.join(engine.dir(uid,id),'final.mp4'),result.filePath);return {saved:true}}return {saved:false}});
  win=new BrowserWindow({width:1280,height:880,minWidth:980,minHeight:680,backgroundColor:'#f5f7fb',autoHideMenuBar:true,webPreferences:{preload:path.join(__dirname,'preload.cjs'),sandbox:true,contextIsolation:true,nodeIntegration:false}});
  win.webContents.setWindowOpenHandler(()=>({action:'deny'}));win.webContents.on('will-navigate',e=>e.preventDefault());win.webContents.session.setPermissionRequestHandler((_,__,done)=>done(false));
  await win.loadURL(page);
  updates.start();
  win.on('close',event=>{if(engine.running){event.preventDefault();dialog.showMessageBox(win,{type:'info',message:'请先暂停制作，等待当前提交结束后再关闭。'})}});
 });
 app.on('window-all-closed',()=>app.quit());
}

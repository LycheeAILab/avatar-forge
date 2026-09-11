const {contextBridge,ipcRenderer,webUtils}=require('electron');
contextBridge.exposeInMainWorld('avatarStudio',{
 library:()=>ipcRenderer.invoke('avatar:library'),
 renameAsset:input=>ipcRenderer.invoke('avatar:renameAsset',input),
 updates:()=>ipcRenderer.invoke('avatar:updates'),
 checkUpdates:()=>ipcRenderer.invoke('avatar:checkUpdates'),
 installUpdate:()=>ipcRenderer.invoke('avatar:installUpdate'),
 onUpdate:fn=>{const listener=(_,value)=>fn(value);ipcRenderer.on('avatar:update',listener);return()=>ipcRenderer.removeListener('avatar:update',listener)},
 register:(file)=>ipcRenderer.invoke('avatar:register',webUtils.getPathForFile(file)),
 create:input=>ipcRenderer.invoke('avatar:create',input),
 history:()=>ipcRenderer.invoke('avatar:history'),
 resume:id=>ipcRenderer.invoke('avatar:resume',id),
 export:id=>ipcRenderer.invoke('avatar:export',id),
 pause:()=>ipcRenderer.invoke('avatar:pause'),
 onChange:fn=>{const listener=(_,value)=>fn(value);ipcRenderer.on('avatar:task',listener);return()=>ipcRenderer.removeListener('avatar:task',listener)}
});
contextBridge.exposeInMainWorld('avatarAuth',{
 status:()=>ipcRenderer.invoke('avatar:status'),
 login:()=>ipcRenderer.invoke('avatar:login'),
 logout:()=>ipcRenderer.invoke('avatar:logout'),
 onChange:fn=>{const listener=(_,value)=>fn(value);ipcRenderer.on('avatar:auth',listener);return()=>ipcRenderer.removeListener('avatar:auth',listener)}
});

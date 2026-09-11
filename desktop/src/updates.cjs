const {EventEmitter}=require('node:events');
class Updates extends EventEmitter {
  constructor({updater,version,enabled,busy}){super();this.updater=updater;this.enabled=enabled;this.busy=busy;this.state={status:enabled?'idle':'disabled',currentVersion:version};this.checking=false;updater.autoDownload=true;updater.autoInstallOnAppQuit=false;updater.allowDowngrade=false;updater.logger=null;
    updater.on('checking-for-update',()=>this.set({status:'checking',error:null}));
    updater.on('update-available',info=>this.set({status:'downloading',version:info.version,percent:0}));
    updater.on('download-progress',info=>this.set({status:'downloading',percent:Math.round(info.percent)}));
    updater.on('update-not-available',()=>this.set({status:'current'}));
    updater.on('update-downloaded',info=>this.set({status:'ready',version:info.version,percent:100}));
    updater.on('error',()=>this.set({status:'error',error:'更新检查或下载失败，请稍后重试'}));
  }
  set(value){this.state={...this.state,...value};this.emit('state',this.state);}
  async check(){if(!this.enabled)return this.state;if(this.checking||['downloading','ready'].includes(this.state.status))return this.state;this.checking=true;try{const result=await this.updater.checkForUpdates();if(result?.downloadPromise)await result.downloadPromise;}catch{this.set({status:'error',error:'更新检查或下载失败，请稍后重试'});}finally{this.checking=false;}return this.state;}
  install(){if(this.state.status!=='ready')throw Error('更新尚未下载完成');if(this.busy())throw Error('请等待制作结束，或暂停制作后再安装更新');this.updater.quitAndInstall(false,true);}
  start(){if(!this.enabled)return;this.timer=setTimeout(()=>void this.check(),10000);this.timer.unref();this.interval=setInterval(()=>void this.check(),4*60*60*1000);this.interval.unref();}
  stop(){clearTimeout(this.timer);clearInterval(this.interval);}
}
module.exports={Updates};

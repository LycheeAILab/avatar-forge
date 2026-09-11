const fs=require('node:fs/promises'),path=require('node:path');
class HiddenModels {
 constructor(root){this.file=path.join(root,'hidden-models.json');this.queue=Promise.resolve()}
 async read(){try{return JSON.parse(await fs.readFile(this.file,'utf8'))}catch(e){if(e.code==='ENOENT')return {};throw Error('无法读取已删除模特记录，请重试')}}
 async ids(user){const data=await this.read();return new Set(data[user]||[])}
 async hide(user,id){const action=this.queue.then(async()=>{const data=await this.read();data[user]=[...new Set([...(data[user]||[]),id])];await fs.writeFile(this.file+'.tmp',JSON.stringify(data));await fs.rename(this.file+'.tmp',this.file)});this.queue=action.catch(()=>{});return action}
}
module.exports={HiddenModels};

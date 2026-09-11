const { CLIENT } = require('./auth.cjs');
class LabError extends Error { constructor(status,message) {super(message);this.status=status;} }
class LabClient {
  constructor(base, storage, request=fetch) {this.base=base;this.storage=storage;this.request=request;this.tokens=null;this.refreshing=null;}
  async initialize() {this.tokens=await this.storage.read();}
  async raw(path, options={}) {
    const deadline=AbortSignal.timeout(path==='/api/cine-sleuth/analyze'?660000:60000);
    const signal=options.signal?AbortSignal.any([options.signal,deadline]):deadline;
    let response,text;
    try{response=await this.request(this.base+path,{...options,redirect:'error',signal});text=await response.text();}
    catch(error){
      if(error.name==='TimeoutError'||signal.reason?.name==='TimeoutError'||['UND_ERR_HEADERS_TIMEOUT','UND_ERR_BODY_TIMEOUT'].includes(error.cause?.code))throw Object.assign(new LabError(504,'等待 Lab 响应超时。已提交的云端任务可能仍在处理，请稍后继续原任务；不会自动重复提交分析。'),{code:'LAB_TIMEOUT'});
      throw error;
    }
    let body;try{body=JSON.parse(text);}catch{body=null;}
    if (!response.ok) throw new LabError(response.status,response.status===404&&path.startsWith('/api/desktop-auth/')?'Lab 尚未部署桌面登录接口，请先更新服务端':typeof body?.message==='string'?body.message:`Lab 请求失败（${response.status}）`);
    if (!body) throw Error('Lab 返回格式无效，请确认服务端已更新');
    return body;
  }
  async save(tokens) {await this.storage.write({...tokens,expiresAt:Date.now()+tokens.expiresIn*1000});this.tokens={...tokens,expiresAt:Date.now()+tokens.expiresIn*1000};}
  async exchange(input) {await this.save(await this.raw('/api/desktop-auth/token',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(input)}));}
  async refresh() {
    if (!this.tokens) throw new LabError(401,'请先登录 LycheeAILab');
    if (!this.refreshing) this.refreshing=this.exchange({clientId:CLIENT,grantType:'refresh_token',refreshToken:this.tokens.refreshToken}).catch(async error=>{
      if (error.status===401) {this.tokens=null;await this.storage.clear();}throw error;
    }).finally(()=>{this.refreshing=null;});
    await this.refreshing;
  }
  async api(path, options={}) {
    if (!path.startsWith('/api/')) throw Error('接口路径无效');
    if (!this.tokens) throw new LabError(401,'请先登录 LycheeAILab');
    if (Date.now()>this.tokens.expiresAt-60000) await this.refresh();
    const used=this.tokens.accessToken;
    const run=()=>this.raw(path,{...options,headers:{...options.headers,Authorization:`Bearer ${this.tokens.accessToken}`}});
    try{return await run();}catch(error){
      if(error.status!==401)throw error;
      if(this.tokens?.accessToken===used)await this.refresh();
      return run();
    }
  }
  json(path,body) {return this.api(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body||{})});}
  async logout() {
    try { if(this.tokens) await this.json('/api/desktop-auth/logout'); }
    catch(error) { if(error.status!==401) throw error; }
    this.tokens=null;await this.storage.clear();
  }
}
module.exports={LabClient,LabError};

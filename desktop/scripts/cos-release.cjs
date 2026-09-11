// Run inside the Lab API container; credentials remain in its existing environment.
const {createRequire}=require('node:module');const COS=createRequire('/app/dist/audio/cos-storage.service.js')('cos-nodejs-sdk-v5');
const cos=new COS({SecretId:process.env.COS_SECRET_ID,SecretKey:process.env.COS_SECRET_KEY,SecurityToken:process.env.COS_TOKEN||undefined,Protocol:'https:'});
const Bucket=process.env.COS_BUCKET,Region=process.env.COS_REGION,prefix='releases/avatar-forge/windows/x64/';
const input=JSON.parse(process.argv[2]);
function object(name){if(!/^(Avatar-Forge-\d+\.\d+\.\d+-Windows-x64-Setup\.exe(?:\.blockmap)?|latest\.yml)$/.test(name))throw Error('Invalid release filename');return {Bucket,Region,Key:prefix+name};}
(async()=>{
 if(input.mode==='prepare'){const urls={};for(const f of input.files){const params=object(f.name);if(f.name!=='latest.yml'){try{await cos.headObject(params);throw Error('Release artifact already exists: '+f.name);}catch(e){if(e.statusCode!==404)throw e;}}urls[f.name]=await cos.getObjectUrl({...params,Sign:true,Method:'PUT',Expires:3600,Protocol:'https:'});}console.log(JSON.stringify(urls));}
 else if(input.mode==='expose'){for(const f of input.files){const params=object(f.name);const head=await cos.headObject(params);if(Number(head.headers['content-length'])!==f.size)throw Error('Size mismatch');await cos.putObjectAcl({...params,ACL:'public-read'});}console.log(JSON.stringify({ok:true}));}
 else throw Error('Invalid mode');
})().catch(e=>{console.error(e.code||e.message);process.exitCode=1;});

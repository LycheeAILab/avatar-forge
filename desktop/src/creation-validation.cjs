function validateCreation(input){
 if(!['image','saved'].includes(input.person))throw Error('请选择上传图片或已有模特');
 if(input.person==='saved'&&(typeof input.modelId!=='string'||!input.modelId.trim()))throw Error('请选择已有模特');
 if(input.voice!=='saved'||typeof input.voiceId!=='string'||!input.voiceId.trim())throw Error('请选择已有音色');
 if(typeof input.script!=='string'||!input.script.trim())throw Error('请填写口播文案');
 if(input.script.length>20000)throw Error('口播文案不能超过20000字');
 if(input.consent!==true)throw Error('请确认素材使用授权');
}
module.exports={validateCreation};

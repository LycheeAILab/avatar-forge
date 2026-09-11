const { randomBytes, createHash } = require('node:crypto');
const CLIENT = 'avatar-forge-desktop';
const SCHEME = 'cn.com.lycheeai.avatarforge';
const REDIRECT = `${SCHEME}:/oauth/callback`;
const PRODUCTION = 'https://lab.lycheeai.com.cn';
function labOrigin(value, packaged) {
  const url = new URL(value || PRODUCTION);
  if (url.origin === PRODUCTION && url.href === `${PRODUCTION}/`) return PRODUCTION;
  if (!packaged && url.protocol === 'http:' && ['127.0.0.1','localhost'].includes(url.hostname) && !url.username && !url.password && url.pathname === '/' && !url.search && !url.hash) return url.origin;
  throw Error('Lab 地址无效');
}
function beginLogin(base, deviceName) {
  const state = randomBytes(32).toString('base64url'), verifier = randomBytes(48).toString('base64url');
  const url = new URL('/desktop-authorize', base);
  url.search = new URLSearchParams({clientId:CLIENT,redirectUri:REDIRECT,state,codeChallenge:createHash('sha256').update(verifier).digest('base64url'),codeChallengeMethod:'S256',deviceName});
  return { url:url.toString(), state, verifier, expiresAt:Date.now()+5*60*1000 };
}
function acceptCallback(value, pending) {
  const url = new URL(value);
  if (!pending || Date.now()>pending.expiresAt || url.protocol!==`${SCHEME}:` || url.host || url.pathname!=='/oauth/callback' || url.hash ||
      url.searchParams.getAll('state').length!==1 || url.searchParams.getAll('code').length!==1 || url.searchParams.get('state')!==pending.state ||
      !/^[A-Za-z0-9_-]{43}$/.test(url.searchParams.get('code')||'')) throw Error('登录回调无效或已过期，请重新登录');
  return {clientId:CLIENT,grantType:'authorization_code',redirectUri:REDIRECT,code:url.searchParams.get('code'),codeVerifier:pending.verifier};
}
module.exports = {CLIENT,SCHEME,REDIRECT,PRODUCTION,labOrigin,beginLogin,acceptCallback};

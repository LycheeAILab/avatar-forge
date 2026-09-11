const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const files = {'/':'index.html','/style.css':'style.css','/studio.css':'studio.css','/renderer.js':'renderer.js','/studio.js':'studio.js','/library.js':'library.js','/library.css':'library.css'};
http.createServer((req,res) => {
  const file = files[new URL(req.url,'http://localhost').pathname];
  if (!file) { res.writeHead(404); return res.end(); }
  res.setHeader('Cache-Control','no-store');
  res.setHeader('Content-Type', file.endsWith('.css')?'text/css':file.endsWith('.js')?'text/javascript':'text/html; charset=utf-8');
  fs.createReadStream(path.join(__dirname,'src',file)).pipe(res);
}).listen(3291,'127.0.0.1',()=>console.log('Avatar Forge preview: http://127.0.0.1:3291'));

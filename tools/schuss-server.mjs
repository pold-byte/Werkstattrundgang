// tools/schuss-server.mjs
// Nimmt PNG-Data-URLs aus dem Browser entgegen und schreibt sie nach blender/renders/.
// Start: node tools/schuss-server.mjs   (im Repo-Wurzelverzeichnis)
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

const ZIEL = path.join(process.cwd(), 'blender', 'renders');
fs.mkdirSync(ZIEL, { recursive: true });

http.createServer((req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Headers', '*');
  if (req.method === 'OPTIONS') { res.end(); return; }
  let rumpf = '';
  req.on('data', (teil) => { rumpf += teil; });
  req.on('end', () => {
    try {
      const { name, data } = JSON.parse(rumpf);
      if (!/^[\w-]+$/.test(name)) throw new Error('unerlaubter Name');
      fs.writeFileSync(path.join(ZIEL, name + '.png'), Buffer.from(data.split(',')[1], 'base64'));
      console.log('OK ' + name);
    } catch (fehler) {
      console.log('FEHLER ' + fehler.message);
    }
    res.end('ok');
  });
}).listen(5198, () => console.log('Schuss-Server auf http://localhost:5198'));

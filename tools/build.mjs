// Compila únicamente documentos propios a un Adventure LevelDB y un ZIP local.
import fs from 'node:fs/promises';
import {createWriteStream} from 'node:fs';
import {ClassicLevel} from 'classic-level';
import archiver from 'archiver';
const manifest=JSON.parse(await fs.readFile('module.json'));
const docs=JSON.parse(await fs.readFile('_data/aventura.json'));
await fs.mkdir('packs',{recursive:true});
await fs.rm('packs/aventura',{recursive:true,force:true});
const db=new ClassicLevel('packs/aventura',{valueEncoding:'json'});
for(const d of docs) await db.put(`!adventures!${d._id}`,d);
await db.close();
await fs.mkdir('dist',{recursive:true});
const out=createWriteStream('dist/mr-trono-de-la-sed.zip');
const zip=archiver('zip',{zlib:{level:9}});
const done=new Promise((resolve,reject)=>{out.on('close',resolve);out.on('error',reject);zip.on('error',reject)});
zip.pipe(out);
for(const p of ['module.json','js','styles','lang','templates','tours','packs','assets','brand','content/upgrade-v1.json','content/stage.json','README.md','NOTICE.md','LICENSE','AUDIO-CREDITS.md','CHANGELOG.md']) {
 try {const st=await fs.stat(p);if(st.isDirectory())zip.directory(p,p);else zip.file(p,{name:p});}
 catch(e){if(e.code!=='ENOENT')throw e;}
}
await zip.finalize();await done;
await fs.copyFile('module.json','dist/module.json');
console.log(`Compendio ${docs.length}; ZIP ${manifest.version} listo para distribución.`);

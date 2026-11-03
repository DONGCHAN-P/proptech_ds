import { createApp } from '../src/server.ts';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
const dir=mkdtempSync(join(tmpdir(),'ik-browser-'));
const app=createApp(dir);app.listen(3211,'127.0.0.1');
process.on('SIGTERM',()=>{app.close(()=>{rmSync(dir,{recursive:true,force:true});process.exit(0);});});

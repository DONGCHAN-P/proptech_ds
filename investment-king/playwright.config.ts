import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir:'./browser-tests',workers:1,timeout:60000,reporter:'list',
  use:{baseURL:'http://127.0.0.1:3211',headless:true,channel:'chrome'},
  webServer:{command:'node scripts/qa-server.ts',url:'http://127.0.0.1:3211/health',reuseExistingServer:false},
  projects:[{name:'desktop',use:{viewport:{width:1440,height:1000}}},{name:'mobile',use:{viewport:{width:390,height:844},isMobile:true,hasTouch:true}}]
});

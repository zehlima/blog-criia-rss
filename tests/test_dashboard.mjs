import test from 'node:test';
import assert from 'node:assert/strict';
import {createSnapshotAPI} from '../frontend/src/snapshot.mjs';
const snapshot={schema_version:1,generated_at:'2026-09-14',articles:[{id:1,title:'Ciência no Brasil',country:'Brasil'},{id:2,title:'Energy',country:'USA'}],trends:[{scope:'country',place:'Brasil',payload:{ranking:[{label:'Ciência',articles:3,publishers:2}]}},{scope:'globe',place:'Globo',payload:{ranking:[{label:'Energy',articles:8,publishers:4}]}}]};
const read=createSnapshotAPI({url:'http://local/data',fetcher:async()=>({ok:true,json:async()=>snapshot})});
test('accent-insensitive search and geography',async()=>assert.equal((await read('articles',{q:'ciencia',place:'brasil'})).data.items.length,1));
test('scopes do not mix',async()=>assert.equal((await read('trends',{scope:'globe'})).data.items[0].label,'Energy'));
test('unknown article fails',async()=>assert.rejects(read('articles/99')));
test('HTTP errors are not reported as empty data',async()=>{const r=createSnapshotAPI({url:'http://local',fetcher:async()=>({ok:false,status:503})});await assert.rejects(r('articles'));});

test('pagination retains total and reveals additional articles',async()=>{const first=await read('articles',{limit:1});assert.equal(first.data.items.length,1);assert.equal(first.data.total,2);assert.equal((await read('articles',{limit:30})).data.items.length,2);});

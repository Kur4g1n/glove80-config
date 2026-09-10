// Exercise the shipped event handlers with a small DOM test double. Layout and
// raster rendering are separately checked in the browser and exported PDF.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
class Node {
  constructor(tag='div'){this.tag=tag;this.attrs={};this.dataset={};this.children=[];this.events={};this.style={setProperty:(k,v)=>this.style[k]=v};this.textContent='';}
  setAttribute(k,v){this.attrs[k]=String(v);if(k.startsWith('data-'))this.dataset[k.slice(5)]=String(v);}
  getAttribute(k){return this.attrs[k]??null;}
  removeAttribute(k){delete this.attrs[k];}
  append(...children){this.children.push(...children);}
  replaceChildren(...children){this.children=children;}
  addEventListener(type,fn){(this.events[type]??=[]).push(fn);}
  fire(type,props={}){return Promise.all((this.events[type]??[]).map(fn=>fn({currentTarget:this,pointerType:'mouse',detail:1,preventDefault(){},...props})));}
}
function app(userAgent='Macintosh'){
  const nodes=new Map();
  const document=new Node();document.documentElement=new Node();
  document.querySelector=selector=>{if(!nodes.has(selector))nodes.set(selector,new Node());return nodes.get(selector);};
  document.createElement=tag=>new Node(tag);document.createElementNS=(_,tag)=>new Node(tag);
  const window=new Node(),context={window,document,console,navigator:{userAgent},matchMedia:()=>({matches:false}),localStorage:{getItem(){return null;},setItem(){}}};
  vm.createContext(context);
  vm.runInContext(fs.readFileSync('docs/layout-data.js','utf8'),context);
  vm.runInContext(fs.readFileSync('docs/layout.js','utf8'),context);
  return {nodes,document,window,key:pos=>nodes.get('#keyboard').children.find(k=>k.dataset.position===String(pos)),title:()=>nodes.get('#layer-title').textContent.replace(/ layer$/,'')};
}
{
  const a=app();assert.equal(a.title(),'Base');
  assert.equal(a.nodes.get('#layer-title').textContent,'Base layer');
  assert.equal(a.nodes.get('.base-identity').hidden,false);
  assert.ok(a.nodes.get('.layer-overview').textContent.includes('Enthium'));
  a.key(68).fire('pointerenter');assert.equal(a.title(),'Number');
  assert.equal(a.nodes.get('#layer-title').textContent,'Number layer');
  assert.equal(a.nodes.get('.layer-state').textContent,'');
  assert.equal(a.nodes.get('.base-identity').hidden,true);
  a.key(68).fire('pointerleave');assert.equal(a.title(),'Base');
  a.key(68).fire('click');assert.equal(a.title(),'Number');assert.equal(a.key(68).dataset.locked,'true');assert.equal(a.key(68).style['--key-bg'],'#ed8796');
  a.key(75).fire('click');assert.equal(a.title(),'Number'); // Restored '(' is not a layer switch.
  a.key(68).fire('click');assert.equal(a.title(),'Base');
  a.key(51).fire('keydown',{key:'Enter'});assert.equal(a.title(),'Cursor');assert.equal(a.key(51).dataset.locked,'true');
  a.document.fire('keydown',{key:'Escape'});assert.equal(a.title(),'Base');
  a.key(64).fire('click');assert.equal(a.title(),'Magic');assert.equal(a.key(64).dataset.locked,'false');
  a.key(75).fire('click');assert.equal(a.title(),'Symbol');assert.equal(a.key(75).dataset.locked,'true');
  a.key(51).fire('pointerenter');assert.equal(a.title(),'Symbol'); // Restored slash has no preview.
}
{
  const a=app();
  a.key(68).fire('pointerenter');a.key(68).fire('click');
  assert.equal(a.key(68).dataset.locked,'true');
  a.key(68).fire('click');assert.equal(a.title(),'Number');
  assert.equal(a.key(68).dataset.locked,'false');
  a.key(68).fire('pointerleave');assert.equal(a.title(),'Base');
  a.key(68).fire('pointerenter');a.key(68).fire('click');
  a.key(68).fire('pointerleave');assert.equal(a.title(),'Number');
  a.document.fire('keydown',{key:'Escape'});
  assert.equal(a.key(24).style['--key-bg'],'#8bd5ca');
}
{
  const a=app(),tap=(pos,detail=1)=>a.key(pos).fire('click',{pointerType:'touch',detail});
  a.key(68).fire('pointerenter',{pointerType:'touch'});assert.equal(a.title(),'Base');
  tap(68);assert.equal(a.title(),'Number');assert.equal(a.key(68).dataset.locked,'false');
  tap(68,2);assert.equal(a.key(68).dataset.locked,'true');assert.equal(a.key(68).style['--key-bg'],'#ed8796');
  tap(68,3);assert.equal(a.title(),'Base');
  tap(64);tap(75);assert.equal(a.title(),'Symbol');assert.equal(a.key(75).dataset.locked,'false');
  tap(75);assert.equal(a.key(75).dataset.locked,'true');
}
{
  const a=app(),letter=()=>a.key(24).children.find(n=>n.attrs.class?.startsWith('legend')).textContent;
  assert.equal(letter(),'y');a.document.fire('keydown',{key:'Shift'});assert.equal(letter(),'Y');
  a.document.fire('keyup',{key:'Shift'});assert.equal(letter(),'y');
  a.nodes.get('.shift-toggle').fire('click');assert.equal(letter(),'Y');
  a.document.fire('keydown',{key:'Shift'});a.document.fire('keyup',{key:'Shift'});assert.equal(letter(),'Y');
  a.nodes.get('.shift-toggle').fire('click');assert.equal(letter(),'y');
  a.nodes.get('.theme-toggle').fire('click');assert.equal(a.document.documentElement.dataset.theme,'light');
}
{
  const a=app(),letter=pos=>a.key(pos).children.find(n=>n.attrs.class?.startsWith('legend')).textContent;
  a.nodes.get('.language-toggle').fire('click');
  assert.equal(letter(24),'у');assert.equal(letter(74),'в');assert.equal(letter(22),'ё');
  assert.equal(letter(34),'ф');assert.equal(letter(45),'щ');
  assert.equal(letter(46),'');assert.equal(letter(33),'');
  assert.equal(letter(66),',');assert.equal(letter(67),'.');
  assert.equal(a.nodes.get('.layout-name').textContent,'Statica · thumb');
  a.nodes.get('.shift-toggle').fire('click');assert.equal(letter(24),'У');assert.equal(letter(22),'Ё');
  a.key(75).fire('click');const symbols=a.nodes.get('#keyboard').children.filter(n=>Number(n.dataset.position)<55).map(n=>n.attrs['aria-label']);
  a.nodes.get('.language-toggle').fire('click');
  assert.equal(a.title(),'Symbol');assert.equal(a.key(75).dataset.locked,'true');
  assert.deepEqual(a.nodes.get('#keyboard').children.filter(n=>Number(n.dataset.position)<55).map(n=>n.attrs['aria-label']),symbols);
  a.document.fire('keydown',{key:'Escape'});assert.equal(letter(24),'Y');assert.equal(letter(22),'');
}
{
  const a=app();a.key(51).fire('click');
  assert.equal(a.key(58).getAttribute('role'),'button');
  a.key(58).fire('click');assert.equal(a.nodes.get('.language-toggle').textContent,'RU');
  assert.equal(a.title(),'Cursor');assert.equal(a.key(51).dataset.locked,'true');
  a.key(58).fire('keydown',{key:'Enter'});assert.equal(a.nodes.get('.language-toggle').textContent,'EN');
}
{
  const a=app();
  const legend=()=>a.nodes.get('.color-legend').children.map(section=>section.children[1].children.map(button=>button.dataset.category));
  for(const position of [null,51,68,64,75]){
    a.document.fire('keydown',{key:'Escape'});
    if(position!==null)a.key(position).fire('click');
    const english=legend();
    a.nodes.get('.language-toggle').fire('click');assert.deepEqual(legend(),english);
    a.nodes.get('.language-toggle').fire('click');assert.deepEqual(legend(),english);
  }
}
{
  const a=app('Windows NT 10.0'),label=pos=>a.key(pos).children.find(n=>n.attrs.class?.startsWith('legend')).textContent;
  assert.equal(label(53),'Ctrl');assert.equal(label(54),'Win');assert.equal(label(56),'Ctrl');
  a.nodes.get('.language-toggle').fire('click');
  assert.equal(label(53),'Ctrl');assert.equal(label(54),'Win');assert.equal(label(56),'Ctrl');
}
{
  const {pdfBytes}=require('../docs/pdf.js');
  // Binary image data must not corrupt xref offsets or stream lengths.
  const pdf=Buffer.from(pdfBytes(Array.from({length:5},()=>Uint8Array.from([0xff,0xd8,0x80,0,0xff,0xd9]))));
  const text=pdf.toString('latin1'),xref=Number(text.match(/startxref\n(\d+)/)[1]);assert.equal(text.slice(xref,xref+4),'xref');
  assert.equal((text.match(/\/Type \/Page /g)||[]).length,5);
  const offsets=text.slice(xref).split('\n').slice(3,20);
  offsets.forEach((line,index)=>assert.ok(text.slice(Number(line.slice(0,10))).startsWith(`${index+1} 0 obj`)));
}
async function testExport(){
  const a=app();
  a.key(68).fire('click');a.nodes.get('.shift-toggle').fire('click');a.nodes.get('.language-toggle').fire('click');
  let captured;
  a.window.captureLayoutPage=()=>({title:a.title(),shift:a.nodes.get('.shift-toggle').getAttribute('aria-pressed')});
  a.window.downloadLayoutPDF=async(pages,theme,language)=>{captured={pages,theme,language};return {url:'blob:test',filename:'layers.pdf'};};
  await a.nodes.get('.pdf-download').fire('click');
  assert.deepEqual(Array.from(captured.pages,p=>p.title),['Base','Cursor','Number','Magic','Symbol']);
  assert.ok(captured.pages.every(p=>p.shift==='true'));assert.equal(captured.theme,'macchiato');
  assert.equal(captured.language,'ru');assert.equal(a.nodes.get('.language-toggle').textContent,'RU');
  assert.equal(a.title(),'Number');assert.equal(a.key(68).dataset.locked,'true');
  assert.equal(a.nodes.get('.pdf-download').disabled,false);
  a.window.captureLayoutPage=()=>{throw Error('Expected test failure');};
  // An export error must also restore the selected/locked map and button.
  const oldError=console.error;console.error=()=>{};
  try{await a.nodes.get('.pdf-download').fire('click');}finally{console.error=oldError;}
  assert.equal(a.title(),'Number');assert.equal(a.key(68).dataset.locked,'true');
  assert.equal(a.nodes.get('.pdf-download').disabled,false);
}
testExport().then(()=>console.log('Diagram: desktop/touch locks, Shift, fixed Macchiato theme, PDF capture/restoration and structure passed')).catch(error=>{console.error(error);process.exitCode=1;});

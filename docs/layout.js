(() => {
  'use strict';
  const data=window.GLOVE80, svg=document.querySelector('#keyboard');
  const panel=document.querySelector('#keyboard-panel');
  const shiftButton=document.querySelector('.shift-toggle'), themeButton=document.querySelector('.theme-toggle');
  const languageButton=document.querySelector('.language-toggle');
  let language='en';
  const platformButton=document.querySelector('.platform-toggle');
  const platforms=['macos','windows','linux'],platformNames={macos:'macOS',windows:'Windows',linux:'Linux'};
  const userAgent=typeof navigator!=='undefined'?navigator.userAgent:'';
  let platform=/Windows/.test(userAgent)?'windows':/Linux/.test(userAgent)&&!/Android/.test(userAgent)?'linux':'macos';
  try{const saved=localStorage.getItem('glove80-platform');if(['macos','windows','linux'].includes(saved))platform=saved;}catch{}
  function updatePlatformButton(){
    const next=platforms[(platforms.indexOf(platform)+1)%platforms.length];
    platformButton.dataset.platform=platform;
    platformButton.setAttribute('aria-label',`Platform: ${platformNames[platform]}. Show ${platformNames[next]} thumb keys`);
    platformButton.setAttribute('title',`${platformNames[platform]} · Click for ${platformNames[next]}`);
  }
  updatePlatformButton();
  const layers=()=>data.languages[language].layers;
  const categoryLabel=label=>platform==='windows'?({'Command':'Control','Control':'Windows','Alt · Option':'Alt'}[label]??label):platform==='linux'?({'Command':'Super','Alt · Option':'Alt'}[label]??label):label;
  const legendPanel=document.querySelector('.color-legend');
  const overviews=[
    'Enthium typing with dedicated modifiers, numbers, and function keys.',
    'Navigation, editing, media playback, brightness, and language switching.',
    'Numbers, arithmetic, and text navigation on the right half.',
    'Bluetooth, USB, lighting, and keyboard reset controls.',
    'Punctuation, brackets, and programming symbols on the left half.'
  ];
  const ns='http://www.w3.org/2000/svg';
  let selected=0, preview=null, shiftLatched=false, shiftHeld=false, locked=null;
  let legendLayer=-1, highlighted=null, hoveredGroup=null, legendButtons=[];
  const keyTheme=data.defaultTheme;
  document.documentElement.style.setProperty('--active-key',data.roles['layer.active'].background);
  document.documentElement.style.setProperty('--locked-key',data.roles['layer.locked'].background);
  const active=()=>preview ?? selected;
  const element=(tag,attrs={})=>{
    const node=document.createElementNS(ns,tag);
    for(const [name,value] of Object.entries(attrs))node.setAttribute(name,value);
    return node;
  };
  const view=[data.viewBox[0]-.55,data.viewBox[1]-.35,data.viewBox[2]+1.1,data.viewBox[3]+.85];
  svg.setAttribute('viewBox',view.join(' '));
  svg.style.aspectRatio=`${view[2]} / ${view[3]}`;
  // Coordinates are fixed to the diagram, never inserted into document flow on hover.
  const coordinates=element('g',{class:'coordinates','aria-hidden':'true'});
  for(const side of ['L','R']){
    const finger=data.geometry.filter(g=>g.label.startsWith(side+'_C'));
    for(let col=1;col<=6;col++){
      const top=finger.filter(g=>g.label.startsWith(`${side}_C${col}R`)).sort((a,b)=>a.y-b.y)[0];
      const text=element('text',{x:top.x+.5,y:top.y-.22});text.textContent=`C${col}`;coordinates.append(text);
    }
    for(let row=1;row<=6;row++){
      const outer=finger.find(g=>g.label===`${side}_C6R${row}`);
      const text=element('text',{x:side==='L'?-.43:19.68,y:outer.y+.53});text.textContent=`R${row}`;coordinates.append(text);
    }
    for(const g of data.geometry.filter(g=>g.label.startsWith(side+'_T'))){
      const offset=Number(g.label.split('_T')[1])<=3?-.80:.83, angle=g.r*Math.PI/180;
      const text=element('text',{x:g.x+.5-Math.sin(angle)*offset,y:g.y+.5+Math.cos(angle)*offset});
      text.textContent=g.label.split('_')[1];text.setAttribute('class','thumb-coordinate');coordinates.append(text);
    }
  }
  function select(layer){selected=layer;preview=null;locked=null;highlighted=null;hoveredGroup=null;render();}
  function choose(target,touch=false,hovered=false){
    if(target===null)return;
    if(locked===target || (target===3 && selected===3)){
      select(0);
      // Desktop unlock returns to a hover preview until the pointer leaves.
      if(!touch && hovered){preview=target;render();}
      return;
    }
    const shouldLock=target!==3 && (!touch || selected===target);
    select(target);
    if(shouldLock){locked=target;render();}
  }

  const keyIcons={
    '⇧':{name:'Shift',path:'m12 3 9 9h-5v9H8v-9H3Z'},
    '⌫':{name:'Backspace',path:'M9 5H22V19H9L2 12ZM12 9l6 6m0-6-6 6'}
  };
  const keys=data.geometry.map((g,pos)=>{
    const x=g.x,y=g.y,group=element('g',{class:'key','data-position':pos});
    if(g.r)group.setAttribute('transform',`rotate(${g.r} ${g.rx} ${g.ry})`);
    const shell=element('rect',{class:'key-shell',x:x+.035,y:y+.05,width:.93,height:.94,rx:.11});
    const face=element('rect',{class:'key-face',x:x+.07,y:y+.035,width:.86,height:.86,rx:.085});
    const rim=element('path',{class:'key-rim',d:`M${x+.14} ${y+.075}h.72M${x+.10} ${y+.12}v.65`});
    const pulse=element('circle',{class:'layer-pulse',cx:x+.5,cy:y+.46,r:.33});
    const legend=element('text',{class:'legend',x:x+.5,y:y+.5});
    const icon=element('path',{class:'key-icon',transform:`translate(${x+.308} ${y+.288}) scale(.016)`,'aria-hidden':'true'});
    const upper=element('text',{class:'shifted',x:x+.5,y:y+.18});
    const mark=element('path',{class:'lock-mark',d:`M${x+.73} ${y+.66}v-.08a.06.06 0 0 1 .12 0v.08m-.14 0h.16v.13h-.16z`});
    const title=element('title');
    group.append(title,shell,face,rim,pulse,legend,icon,upper,mark);
    if(pos===38 || pos===41)group.append(element('path',{class:'home-mark',d:`M${x+.40} ${y+.79}h.20`}));
    let pointerInside=false;
    const target=()=>layers()[selected][pos].target;
    const languageKey=()=>layers()[selected][pos].binding==='&kp LC(SPACE)';
    const start=()=>{if(target()!==null){preview=target();hoveredGroup=null;render();}};
    const end=()=>{if(preview!==null){preview=null;render();}};
    group.addEventListener('pointerenter',event=>{if(event.pointerType!=='touch'){pointerInside=true;start();}});
    group.addEventListener('pointerleave',()=>{pointerInside=false;end();});
    group.addEventListener('focus',start);group.addEventListener('blur',end);
    group.addEventListener('click',event=>{if(languageKey())toggleLanguage();else choose(target(),event.pointerType==='touch',pointerInside);});
    group.addEventListener('keydown',event=>{
      if((target()!==null || languageKey()) && (event.key==='Enter'||event.key===' ')){
        event.preventDefault();if(languageKey())toggleLanguage();else choose(target());
      }
    });
    svg.append(group);return {group,legend,icon,upper,title,pos};
  });
  svg.append(coordinates);
  function updateHighlights(){
    const match=hoveredGroup ?? highlighted;
    for(const {group} of keys)group.dataset.match=String(match!==null && group.dataset.category===match);
    for(const button of legendButtons)button.setAttribute('aria-pressed',String(button.dataset.category===highlighted));
  }
  function renderLegend(layer){
    if(legendLayer===layer)return;
    legendLayer=layer;highlighted=null;hoveredGroup=null;
    const roles=layers()[layer].map(key=>data.roles[key.role]);
    roles.push(data.roles['layer.active'],data.roles['layer.locked']);
    const unique=new Map(roles.map(role=>[role.label,role]));
    // Use the canonical layer's order, independent of which translated key
    // happens to introduce a category first (e.g. ё replacing a blank).
    const categoryOrder=[...new Set([
      ...data.layers[layer].map(key=>data.roles[key.role].label),
      data.roles['layer.active'].label,data.roles['layer.locked'].label,
      ...Object.values(data.roles).map(role=>role.label)
    ])];
    const mainLabels=new Set(layers()[layer].filter((key,pos)=>!data.geometry[pos].label.includes('_T')).map(key=>data.roles[key.role].label));
    mainLabels.add(data.roles['layer.active'].label);mainLabels.add(data.roles['layer.locked'].label);
    const buttons=[...unique.values()].sort((a,b)=>categoryOrder.indexOf(a.label)-categoryOrder.indexOf(b.label)).map(role=>{
      const button=document.createElement('button');button.type='button';button.className='swatch-button';
      button.dataset.category=role.label;button.dataset.disabled=String(role.rgb==='#000000');button.setAttribute('aria-label',`Highlight ${categoryLabel(role.label)} keys`);
      const swatch=document.createElement('span');swatch.className='swatch';swatch.style.setProperty('--swatch',role.background);swatch.setAttribute('aria-hidden','true');
      const label=document.createElement('span');label.className='swatch-label';label.textContent=categoryLabel(role.label);
      button.append(swatch,label);
      const enter=()=>{hoveredGroup=role.label;updateHighlights();},leave=()=>{hoveredGroup=null;updateHighlights();};
      button.addEventListener('pointerenter',enter);button.addEventListener('pointerleave',leave);
      button.addEventListener('focus',enter);button.addEventListener('blur',leave);
      button.addEventListener('click',()=>{highlighted=highlighted===role.label?null:role.label;updateHighlights();});
      return button;
    });
    legendButtons=buttons;
    const mainGroup=document.createElement('div');mainGroup.className='legend-group';
    const mainSection=document.createElement('div');mainSection.className='main-legend';
    mainSection.setAttribute('role','group');mainSection.setAttribute('aria-label','Main keys');
    const mainHeading=document.createElement('span');mainHeading.className='legend-group-title';mainHeading.textContent='Main keys';
    mainSection.append(mainHeading,mainGroup);
    const thumbGroup=document.createElement('div');thumbGroup.className='thumb-legend';
    thumbGroup.setAttribute('role','group');thumbGroup.setAttribute('aria-label','Thumb keys');
    const heading=document.createElement('span');heading.className='legend-group-title';heading.textContent='Thumb keys';
    const thumbItems=document.createElement('div');thumbItems.className='legend-group';
    for(const button of buttons)(mainLabels.has(button.dataset.category)?mainGroup:thumbItems).append(button);
    thumbGroup.append(heading,thumbItems);
    legendPanel.replaceChildren(mainSection,...(thumbItems.children.length?[thumbGroup]:[]));
  }
  function render(){
    const layer=active(), shifted=shiftLatched || shiftHeld;
    document.querySelector('#layer-title').textContent=`${data.names[layer]} layer`;
    document.querySelector('.base-identity').hidden=layer!==0;
    document.querySelector('.layout-name').textContent=data.languages[language].name;
    document.querySelector('.layer-heading').dataset.base=String(layer===0);
    document.querySelector('.layer-overview').textContent=language==='ru' && layer===0
      ? 'Statica with a right-thumb в, dedicated modifiers, and the shared symbol layer.' : overviews[layer];
    document.querySelector('.shift-hint').hidden=layer!==0;
    document.querySelector('.layer-state').textContent=locked===layer?'Locked':'';
    svg.setAttribute('aria-label',`Glove80, ${data.names[layer]} layer`);
    for(const {group,legend,icon,upper,title,pos} of keys){
      const key=layers()[layer][pos],target=key.target;
      let label=shifted && key.shifted?key.shifted:key.label;
      if(platform==='windows'){
        if(['&kp LGUI','&kp RGUI'].includes(key.binding))label='Ctrl';
        if(key.binding==='&kp LCTRL')label='Win';
      }
      if(platform==='linux' && ['&kp LGUI','&kp RGUI'].includes(key.binding))label='Super';
      if(platform!=='macos' && key.binding==='&kp LALT')label='Alt';
      const isLocked=target!==null && locked===target, colors=isLocked?data.roles['layer.locked']:key;
      group.style.setProperty('--key-bg',colors.background);group.style.setProperty('--key-fg',colors.foreground);
      group.dataset.category=data.roles[isLocked?'layer.locked':key.role].label;
      group.dataset.disabled=String(key.binding==='&none');group.dataset.active=String(target===layer);
      const languageKey=key.binding==='&kp LC(SPACE)';
      group.dataset.locked=String(isLocked);group.dataset.interactive=String(target!==null || languageKey);
      const symbol=keyIcons[label];
      legend.textContent=symbol?'':label;legend.setAttribute('class',`legend${label.length>7?' long':label.length>5?' medium':''}`);
      icon.setAttribute('d',symbol?symbol.path:'');
      upper.textContent=/^\p{L}$/u.test(key.label)||['&kp LGUI','&kp RGUI','&kp LCTRL','&kp LALT'].includes(key.binding)?'':shifted?(key.label===label?'':key.label):key.shifted;
      const hint=languageKey?' — Switch diagram language':target===null?'':target===3?' — RGB status on an unused tap':locked===target?' — Press to unlock':selected===3?' — Lock layer':' — Click to lock; on touch, tap again';
      const accessible=`${data.geometry[pos].label}: ${symbol?symbol.name:label || 'unassigned'}${hint}`;
      group.setAttribute('aria-label',accessible);title.textContent=accessible;
      // Focusability follows the selected map: previews cannot remove their own focus target.
      const interactive=layers()[selected][pos].target!==null || layers()[selected][pos].binding==='&kp LC(SPACE)';
      if(interactive){group.setAttribute('role','button');group.setAttribute('tabindex','0');group.setAttribute('aria-pressed',String(languageKey?language==='ru':target===layer));}
      else {group.removeAttribute('role');group.removeAttribute('tabindex');group.removeAttribute('aria-pressed');}
    }
    shiftButton.setAttribute('aria-pressed',String(shifted));
    renderLegend(layer);updateHighlights();
  }
  shiftButton.addEventListener('click',()=>{shiftLatched=!shiftLatched;render();});
  function toggleLanguage(){
    language=language==='en'?'ru':'en';legendLayer=-1;
    languageButton.textContent=language.toUpperCase();
    languageButton.setAttribute('aria-pressed',String(language==='ru'));
    languageButton.setAttribute('aria-label',`Show ${language==='en'?'Russian':'English'} layout`);
    render();
  }
  languageButton.addEventListener('click',toggleLanguage);
  platformButton.addEventListener('click',()=>{
    platform=platforms[(platforms.indexOf(platform)+1)%platforms.length];
    updatePlatformButton();
    legendLayer=-1;
    try{localStorage.setItem('glove80-platform',platform);}catch{}
    render();
  });
  document.addEventListener('keydown',event=>{
    if(event.key==='Escape'){select(0);document.activeElement?.blur();}
    if(event.key==='Shift'&&!shiftHeld){shiftHeld=true;render();}
  });
  document.addEventListener('keyup',event=>{if(event.key==='Shift'){shiftHeld=false;render();}});
  window.addEventListener('blur',()=>{shiftHeld=false;preview=null;render();});
  function setTheme(theme){
    document.documentElement.dataset.theme=theme;
    themeButton.setAttribute('aria-label',`Switch to ${theme==='dark'?'light':'dark'} theme`);
    document.querySelector('meta[name="theme-color"]').content=theme==='dark'?'#24273a':'#eff1f5';
  }
  const systemTheme=matchMedia('(prefers-color-scheme: light)');
  // The old key also stored automatic defaults, so it cannot identify a user choice.
  const themePreferenceKey='glove80-theme-preference';
  let preferredTheme=null;
  try{const saved=localStorage.getItem(themePreferenceKey);if(['light','dark'].includes(saved))preferredTheme=saved;}catch{}
  const applyTheme=()=>setTheme(preferredTheme??(systemTheme.matches?'light':'dark'));
  applyTheme();
  systemTheme.addEventListener('change',applyTheme);
  themeButton.addEventListener('click',()=>{
    preferredTheme=document.documentElement.dataset.theme==='dark'?'light':'dark';
    applyTheme();
    try{localStorage.setItem(themePreferenceKey,preferredTheme);}catch{/* Switching still works without storage. */}
  });
  document.querySelector('.pdf-download').addEventListener('click',async event=>{
    const button=event.currentTarget,status=document.querySelector('.download-status');button.disabled=true;status.textContent='Preparing PDF…';
    try{
      // Capture all layers synchronously, then restore the interaction before encoding.
      const saved={selected,preview,locked,highlighted,hoveredGroup};
      const pages=[];
      try{
        for(let layer=0;layer<data.names.length;layer++){
          selected=layer;preview=null;locked=null;render();
          pages.push(window.captureLayoutPage());
        }
      }finally{
        ({selected,preview,locked,highlighted,hoveredGroup}=saved);
        legendLayer=-1;render();highlighted=saved.highlighted;hoveredGroup=saved.hoveredGroup;updateHighlights();
      }
      const file=await window.downloadLayoutPDF(pages,keyTheme,language);
      const link=document.createElement('a');link.href=file.url;link.download=file.filename;link.textContent='Download PDF';
      status.replaceChildren('Five-layer PDF ready · ',link);
    }
    catch(error){status.textContent='PDF export failed. Please try again.';console.error(error);}
    finally{button.disabled=false;}
  });
  render();
})();

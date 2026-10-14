/* Local, dependency-free PDF export. Each A4 landscape page embeds a 300 dpi
 * snapshot of the current UI renderer, including its key and page themes.
 * No server, external fonts, or network requests are required. */
(() => {
  'use strict';
  const esc=text=>String(text).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&apos;'}[c]));
  // Snapshot the actual renderer at a stable desktop width. SVG key geometry,
  // computed colors and HTML text positions all come from the current UI.
  function captureLayoutPage(){
    const stage=document.querySelector('main').cloneNode(true);
    stage.setAttribute('aria-hidden','true');stage.inert=true;
    Object.assign(stage.style,{position:'fixed',left:'-10000px',top:'0',width:'1440px',maxWidth:'none',padding:'24px 44px 32px',margin:'0',pointerEvents:'none'});
    stage.querySelector('.masthead').remove();stage.querySelector('.download-status').remove();
    document.body.append(stage);
    try{
      const box=stage.getBoundingClientRect();
      const base=getComputedStyle(document.documentElement).getPropertyValue('--base').trim();
      const parts=[`<rect width="1440" height="${box.height}" fill="${esc(base)}"/>`];
      const svg=stage.querySelector('#keyboard'),clone=svg.cloneNode(true),rect=svg.getBoundingClientRect();
      const props=['fill','fill-opacity','stroke','stroke-width','stroke-opacity','stroke-dasharray','stroke-linecap','stroke-linejoin','opacity','display','visibility','font-family','font-size','font-weight','font-style','text-anchor','dominant-baseline','letter-spacing'];
      const originals=[svg,...svg.querySelectorAll('*')],copies=[clone,...clone.querySelectorAll('*')];
      originals.forEach((node,i)=>{
        const style=getComputedStyle(node);
        copies[i].removeAttribute('style');
        for(const prop of props)copies[i].style.setProperty(prop,style.getPropertyValue(prop));
        // Export a static pulse, unaffected by animation timing.
        if(node.classList.contains('layer-pulse'))copies[i].style.opacity='.16';
      });
      clone.setAttribute('x',rect.left-box.left);clone.setAttribute('y',rect.top-box.top);
      clone.setAttribute('width',rect.width);clone.setAttribute('height',rect.height);
      parts.push(new XMLSerializer().serializeToString(clone));
      const footer=stage.querySelector('.legend-panel'),line=footer.getBoundingClientRect();
      parts.push(`<path d="M${line.left-box.left} ${line.top-box.top}h${line.width}" stroke="${esc(getComputedStyle(footer).borderTopColor)}"/>`);
      for(const swatch of stage.querySelectorAll('.swatch')){
        const r=swatch.getBoundingClientRect();
        parts.push(`<circle cx="${r.left-box.left+r.width/2}" cy="${r.top-box.top+r.height/2}" r="${r.width/2}" fill="${esc(getComputedStyle(swatch).backgroundColor)}"/>`);
      }
      // Use browser line wrapping and font metrics for headings, hints and legend.
      for(const root of stage.querySelectorAll('.layer-heading,.key-hints,.color-legend')){
        const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);
        while(walker.nextNode()){
          const node=walker.currentNode,parent=node.parentElement,style=getComputedStyle(parent);
          if(!parent.getClientRects().length || style.visibility==='hidden')continue;
          for(const match of node.textContent.matchAll(/\S+/g)){
            const range=document.createRange();range.setStart(node,match.index);range.setEnd(node,match.index+match[0].length);
            const r=range.getBoundingClientRect();if(!r.width || !r.height)continue;
            parts.push(`<text x="${r.left-box.left}" y="${r.top-box.top+r.height/2}" dominant-baseline="central" fill="${esc(style.color)}" font-family="${esc(style.fontFamily)}" font-size="${esc(style.fontSize)}" font-weight="${esc(style.fontWeight)}" letter-spacing="${esc(style.letterSpacing)}">${esc(match[0])}</text>`);
          }
        }
      }
      const width=1480,height=width*2480/3508,scale=Math.min(1,(height-40)/box.height);
      return `<svg xmlns="http://www.w3.org/2000/svg" width="3508" height="2480" viewBox="0 0 ${width} ${height}"><rect width="${width}" height="${height}" fill="${esc(base)}"/><g transform="translate(${(width-1440*scale)/2} ${(height-box.height*scale)/2}) scale(${scale})">${parts.join('')}</g></svg>`;
    }finally{stage.remove();}
  }
  function pdfBytes(images){
    const encoder=new TextEncoder(),chunks=[],offsets=[0];let length=0;
    const append=value=>{const bytes=typeof value==='string'?encoder.encode(value):value;chunks.push(bytes);length+=bytes.length;};
    const object=(id,body)=>{offsets[id]=length;append(`${id} 0 obj\n`);append(body);append('\nendobj\n');};
    append('%PDF-1.4\n%Glove80\n');
    object(1,'<< /Type /Catalog /Pages 2 0 R >>');
    object(2,`<< /Type /Pages /Count ${images.length} /Kids [${images.map((_,i)=>`${3+i*3} 0 R`).join(' ')}] >>`);
    images.forEach((jpeg,i)=>{
      const id=3+i*3;
      object(id,`<< /Type /Page /Parent 2 0 R /MediaBox [0 0 841.89 595.28] /Resources << /XObject << /Image ${id+1} 0 R >> >> /Contents ${id+2} 0 R >>`);
      offsets[id+1]=length;append(`${id+1} 0 obj\n<< /Type /XObject /Subtype /Image /Width 3508 /Height 2480 /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length ${jpeg.length} >>\nstream\n`);append(jpeg);append('\nendstream\nendobj\n');
      const content='q 841.89 0 0 595.28 0 0 cm /Image Do Q\n';
      object(id+2,`<< /Length ${encoder.encode(content).length} >>\nstream\n${content}endstream`);
    });
    const xref=length;append(`xref\n0 ${offsets.length}\n0000000000 65535 f \n`);
    for(const offset of offsets.slice(1))append(`${String(offset).padStart(10,'0')} 00000 n \n`);
    append(`trailer\n<< /Size ${offsets.length} /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF\n`);
    const result=new Uint8Array(length);let pos=0;for(const chunk of chunks){result.set(chunk,pos);pos+=chunk.length;}return result;
  }
  let previousURL;
  async function downloadLayoutPDF(pages,theme,language='en'){
    const images=[];
    for(const page of pages){
      const url=URL.createObjectURL(new Blob([page],{type:'image/svg+xml;charset=utf-8'}));
      try{
        const image=new Image();image.src=url;await image.decode();
        const canvas=document.createElement('canvas');canvas.width=3508;canvas.height=2480;
        canvas.getContext('2d').drawImage(image,0,0,canvas.width,canvas.height);
        const jpeg=await new Promise((resolve,reject)=>canvas.toBlob(blob=>blob?resolve(blob):reject(new Error('Image encoding failed')),'image/jpeg',.97));
        images.push(new Uint8Array(await jpeg.arrayBuffer()));
        canvas.width=canvas.height=0;
      }finally{URL.revokeObjectURL(url);}
    }
    const url=URL.createObjectURL(new Blob([pdfBytes(images)],{type:'application/pdf'}));
    const link=document.createElement('a');link.href=url;link.download=`glove80-layers-${language}-${theme}.pdf`;document.body.append(link);link.click();link.remove();
    if(previousURL)URL.revokeObjectURL(previousURL);previousURL=url;
    return {url,filename:link.download};
  }
  if(typeof window!=='undefined'){window.downloadLayoutPDF=downloadLayoutPDF;window.captureLayoutPage=captureLayoutPage;}
  if(typeof module!=='undefined')module.exports={pdfBytes};
})();

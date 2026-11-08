/* ToucHigh language menu: open/close, keyboard support, GA4 language_switch event */
(function(){
  function q(s,r){return (r||document).querySelector(s)}
  function qa(s,r){return Array.prototype.slice.call((r||document).querySelectorAll(s))}
  qa('[data-lmenu]').forEach(function(m){
    var b=q('.lm-btn',m), l=q('.lm-list',m);
    function open(o){b.setAttribute('aria-expanded',o?'true':'false'); if(o){l.removeAttribute('hidden'); var c=q('a[aria-current="page"]',l)||q('a',l); if(c) c.focus();} else l.setAttribute('hidden','');}
    b.addEventListener('click',function(e){e.stopPropagation();open(b.getAttribute('aria-expanded')!=='true');});
    m.addEventListener('keydown',function(e){
      if(e.key==='Escape'){open(false);b.focus();}
      if(e.key==='ArrowDown'||e.key==='ArrowUp'){var a=qa('a',l),i=a.indexOf(document.activeElement);if(i<0)return;e.preventDefault();a[(i+(e.key==='ArrowDown'?1:a.length-1))%a.length].focus();}
    });
    document.addEventListener('click',function(e){if(!m.contains(e.target))open(false);});
    qa('a',l).forEach(function(a){a.addEventListener('click',function(e){
      var hl=a.getAttribute('hreflang')||'', sl=a.getAttribute('data-setlang');
      try{localStorage.setItem('tl', hl==='zh-Hans'?'zh':(hl==='en'?'en':hl.toLowerCase()));}catch(_){}
      try{gtag('event','language_switch',{language:hl,location:'menu'});}catch(_){}
      if(sl && typeof window.setLang==='function'){e.preventDefault();window.setLang(sl);try{history.replaceState(null,'',a.getAttribute('href'));}catch(_){} open(false);}
    });});
  });
  // keep the label in sync on the bilingual (client-side zh/en) pages
  function sync(x){qa('[data-lmenu]').forEach(function(m){
    var hl=x==='en'?'en':'zh-Hans';
    qa('.lm-list a',m).forEach(function(a){if(a.getAttribute('data-setlang')){if(a.getAttribute('hreflang')===hl){a.setAttribute('aria-current','page');var t=q('.lm-txt',m);if(t)t.textContent=a.getAttribute('data-short');}else a.removeAttribute('aria-current');}});
  });}
  var f=window.setLang;
  if(typeof f==='function' && q('[data-setlang]')){
    window.setLang=function(x){f(x);sync(x);};
    sync((document.documentElement.lang||'').indexOf('en')===0?'en':'zh');
  }
})();

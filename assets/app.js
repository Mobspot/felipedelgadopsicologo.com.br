(function(){
  var open=document.getElementById('open'), close=document.getElementById('close'),
      panel=document.getElementById('panel'), fab=document.getElementById('fab');

  function setPanel(on){
    if(on){
      panel.removeAttribute('inert');
      panel.setAttribute('aria-hidden','false');
      panel.setAttribute('data-open','');
      document.body.style.overflow='hidden';
      close.focus();
    }
    else{
      panel.removeAttribute('data-open');
      panel.setAttribute('aria-hidden','true');
      panel.setAttribute('inert','');
      document.body.style.overflow='';
      open.focus();
    }
    open.setAttribute('aria-expanded', on ? 'true':'false');
  }
  open.addEventListener('click',function(){ setPanel(true); });
  close.addEventListener('click',function(){ setPanel(false); });
  panel.addEventListener('click',function(e){ if(e.target.tagName==='A') setPanel(false); });
  document.addEventListener('keydown',function(e){
    if(!panel.hasAttribute('data-open')) return;
    if(e.key==='Escape'){ setPanel(false); return; }
    if(e.key==='Tab'){
      var focusable=panel.querySelectorAll('a[href],button:not([disabled])');
      if(!focusable.length) return;
      var first=focusable[0], last=focusable[focusable.length-1];
      if(e.shiftKey && document.activeElement===first){ e.preventDefault(); last.focus(); }
      else if(!e.shiftKey && document.activeElement===last){ e.preventDefault(); first.focus(); }
    }
  });

  function onScroll(){
    if(window.scrollY > window.innerHeight*0.25) fab.setAttribute('data-show','');
    else fab.removeAttribute('data-show');
  }
  window.addEventListener('scroll', onScroll, {passive:true}); onScroll();
})();

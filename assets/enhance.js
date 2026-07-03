/* Tabserve blog enhance: okuma çubuğu + otomatik İçindekiler + mobil indir çubuğu */
(function(){
"use strict";
var TR = (document.documentElement.lang||"en").indexOf("tr")===0;
var APPS = {
 "6761003117":{n:"Routevia",p:"com.yunusgunes.routevia"},
 "6761047805":{n:"OneBag",p:"com.onebag.travel"},
 "6767179451":{n:"RentFlow",p:null}
};
document.addEventListener("DOMContentLoaded",function(){
  var art = document.querySelector("article.post");

  /* 1) Okuma ilerleme çubuğu (yalnız yazı sayfaları) */
  if(art){
    var bar=document.createElement("div"); bar.id="rprog"; document.body.appendChild(bar);
    addEventListener("scroll",function(){
      var h=document.documentElement;
      bar.style.width=(h.scrollTop/(h.scrollHeight-h.clientHeight)*100)+"%";
    },{passive:true});
  }

  /* 2) Otomatik İçindekiler (4+ H2 olan yazılarda) */
  if(art){
    var hs=[].slice.call(art.querySelectorAll("h2")).filter(function(h){
      return !h.closest(".related,.quickfacts") && h.textContent.trim().length>2;
    });
    if(hs.length>=4){
      var box=document.createElement("details"); box.className="toc";
      var list=hs.map(function(h,i){
        if(!h.id) h.id="b"+(i+1);
        return '<li><a href="#'+h.id+'">'+h.textContent.replace(/</g,"&lt;")+"</a></li>";
      }).join("");
      box.innerHTML="<summary>"+(TR?"📑 İçindekiler":"📑 Contents")+"</summary><ol>"+list+"</ol>";
      hs[0].parentNode.insertBefore(box,hs[0]);
    }
  }

  /* 3) Mobil yapışkan indir çubuğu — %35 kaydırınca, kapatılabilir (7 gün hatırlar) */
  var meta=document.querySelector('meta[name="apple-itunes-app"]');
  if(meta && matchMedia("(max-width:820px)").matches){
    var id=(meta.content.match(/app-id=(\d+)/)||[])[1], app=APPS[id];
    try{ var mut=+localStorage.getItem("appbar_off")||0; }catch(e){ var mut=0; }
    if(app && Date.now()-mut > 6048e5){
      var el=document.createElement("div"); el.id="stickyapp"; el.style.display="none";
      el.innerHTML='<span class="t">📲 '+(TR?app.n+" — ücretsiz indir":"Get "+app.n+" — free")+'</span>'
        +'<a href="https://apps.apple.com/app/id'+id+'" rel="noopener">App Store</a>'
        +(app.p?'<a href="https://play.google.com/store/apps/details?id='+app.p+'" rel="noopener">Google Play</a>':"")
        +'<button aria-label="Kapat">&times;</button>';
      document.body.appendChild(el);
      el.querySelector("button").onclick=function(){
        el.remove(); try{localStorage.setItem("appbar_off",Date.now())}catch(e){}
      };
      var shown=false;
      addEventListener("scroll",function(){
        if(shown) return;
        var h=document.documentElement;
        if(h.scrollTop/(h.scrollHeight-h.clientHeight)>.35){
          var cb=document.getElementById("cookie-banner");
          if(cb && cb.style.display!=="none" && cb.offsetParent) return; /* banner kapanana kadar bekle */
          shown=true; el.style.display="flex";
        }
      },{passive:true});
    }
  }
});
})();

/* GA4 — performans dostu geç yükleme: sayfa load+800ms veya ilk etkileşim.
   Eventler dataLayer'da kuyruklanır, gtag gelince işlenir (veri kaybı yok). */
window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}
gtag("js",new Date());gtag("config","G-EDZWXP6EEG",{transport_type:"beacon"});
(function(){var d=false;function load(){if(d)return;d=true;
var s=document.createElement("script");s.async=true;
s.src="https://www.googletagmanager.com/gtag/js?id=G-EDZWXP6EEG";document.head.appendChild(s);}
if(document.readyState==="complete"){setTimeout(load,800)}
else{addEventListener("load",function(){setTimeout(load,800)})}
["scroll","click","touchstart","keydown"].forEach(function(e){addEventListener(e,load,{once:true,passive:true})});})();

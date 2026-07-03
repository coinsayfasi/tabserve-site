/* GA4 + Google Consent Mode v2 — varsayılan RED, kullanıcı kabul edince granted.
   Yükleme: load+3sn veya ilk etkileşim (performans). Eventler dataLayer'da kuyruklanır. */
window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}
var __cc=null;try{__cc=localStorage.getItem("cookie_consent");}catch(e){}
var __g=__cc==="accepted"?"granted":"denied";
gtag("consent","default",{analytics_storage:__g,ad_storage:__g,ad_user_data:__g,ad_personalization:__g,wait_for_update:500});
gtag("js",new Date());gtag("config","G-EDZWXP6EEG",{transport_type:"beacon"});
window.__grantConsent=function(ok){var v=ok?"granted":"denied";
gtag("consent","update",{analytics_storage:v,ad_storage:v,ad_user_data:v,ad_personalization:v});};
(function(){var d=false;function load(){if(d)return;d=true;
var s=document.createElement("script");s.async=true;
s.src="https://www.googletagmanager.com/gtag/js?id=G-EDZWXP6EEG";document.head.appendChild(s);}
if(document.readyState==="complete"){setTimeout(load,3000)}
else{addEventListener("load",function(){setTimeout(load,3000)})}
["scroll","click","touchstart","keydown"].forEach(function(e){addEventListener(e,load,{once:true,passive:true})});})();

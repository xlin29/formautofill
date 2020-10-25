"use strict";

var mode = "";

function getData() {
  return new Promise(function(resolve, reject) {
    chrome.storage.local.get(['mode'], function(result) {
      if (chrome.runtime.lastError) {
        console.error(chrome.runtime.lastError.message);
        reject(chrome.runtime.lastError.message);
      } else {
        resolve(result.mode);
      }
    });
  });
}

window.addEventListener('load', () => {
  var ele = document.getElementById('mymodeswitch');
  getData().then(function(item) {
    mode = item;
    if(mode === 'strict'){
      ele.checked = false;
    }
  });
  ele.addEventListener('click', () => {
    if(ele.checked){
      setMode('lax');
    }else{
      setMode('strict');
    }
  });
});

function setMode(mode){
  console.log('set mode', mode);
  chrome.storage.local.set({'mode': mode});
  chrome.runtime.sendMessage({command: mode});
}


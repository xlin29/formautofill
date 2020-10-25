"use strict";
var mode = "";
document.addEventListener('DOMContentLoaded', function() {
	chrome.storage.local.get(['mode'], function(result) {
        mode = result.mode;
		console.log('Value AAA currently is ' + mode);
	});
});


//popup
chrome.browserAction.onClicked.addListener(() => { chrome.tabs.create({url: chrome.extension.getURL('popup.html'), "active": true}) });

//check message
chrome.runtime.onMessage.addListener( (request, sender, sendResponse) => {
    if (request.hasOwnProperty('command')) {
        switch (request.command){
            case 'lax':
            	console.log(request.command);
                chrome.storage.local.set({"mode": "lax"});
                break;
            case "strict":
            	console.log(request.command);
                chrome.storage.local.set({"mode": "strict"});
                break;
        }
    }

    chrome.storage.local.get(['mode'], function(result) {
    	console.log('Value currently is ' + result.mode);
    });
    chrome.tabs.reload();

});




chrome.tabs.onUpdated.addListener(function (tabId, changeInfo, tab) {
    if (changeInfo.status === 'complete') {
        chrome.tabs.query({active: true, currentWindow: true}, function(tabs){
            chrome.storage.local.get(['mode'], function(result) {
                chrome.tabs.sendMessage(tabs[0].id, {mode: result.mode}, function(response) {});
            });
        });
    }
});




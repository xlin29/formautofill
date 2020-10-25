var debugMode = 0;
chrome.runtime.onMessage.addListener(
  function(message, sender, sendResponse) {
	sendResponse({backmessage: 'true'});
  	startProcess(message['mode']);
  });

function startProcess(mode){
	if(debugMode) console.log(mode, 'mode');
	var elGroups = getForms();
	if (elGroups) {
		performChecks(elGroups, mode);
	}
}
var detected = [];
var unautofillableDetected = [];

/////////////////////////////////////////////////////////////////////////////
//chromium regex for identifying autofill type.
//reference: https://source.chromium.org/chromium/chromium/src/+/master:components/autofill/core/common/autofill_regex_constants.cc
/////////////////////////////////////////////////////////////////////////////
var phone = new RegExp(["phone|mobile|contact.?number",
	"|telefonnummer",                                // de-DE
	"|telefono|teléfono",                            // es
	"|telfixe",                                      // fr-FR
	"|電話",                                         // ja-JP
	"|telefone|telovel",                           // pt-BR, pt-PT
	"|телефон",                                      // ru
	"|मोबाइल",                                       // hi for mobile
	"|(\\b|_|\\*)telefon(\\b|_|\\*)",                // tr
	"|电话",                                         // zh-CN
	"|മൊബൈല്‍",                        // ml for mobile
	"|(?:전화|핸드폰|휴대폰|휴대전화)(?:.?번호)?"].join(''), 'i');
var company = new RegExp(["company|business|organization|organisation",
	"|(?<!con)firma|firmenname",  // de-DE
	"|empresa",                   // es
	"|societe|société",           // fr-FR
	"|ragione.?sociale",          // it-IT
	"|会社",                      // ja-JP
	"|название.?компании",        // ru
	"|单位|公司",                 // zh-CN
	"|شرکت",                      // fa
	"|회사|직장"], 'i');
var addrLine1 = new RegExp(["^address$|address[_-]?line(one)?|address1|addr1|street",
	"|(?:shipping|billing)address$",
	"|strasse|straße|hausnummer|housenumber",           // de-DE
	"|house.?name",                                     // en-GB
	"|direccion|dirección",                             // es
	"|adresse",                                         // fr-FR
	"|indirizzo",                                       // it-IT
	"|^住所$|住所1",                                    // ja-JP
	"|morada|((?<!identificação do )endereço)",         // pt-BR, pt-PT
	"|Адрес",                                           // ru
	"|地址",                                            // zh-CN
	"|(\\b|_)adres(?! (başlığı(nız)?|tarifi))(\\b|_)",  // tr
	"|^주소.?$|주소.?1"].join(''), 'i');                               // ko-KR
var addrLine2 = new RegExp(["address[_-]?line(2|two)|address2|addr2|street|suite|unit",
	"|adresszusatz|ergänzende.?angaben",        // de-DE
	"|direccion2|colonia|adicional",            // es
	"|addresssuppl|complementnom|appartement",  // fr-FR
	"|indirizzo2",                              // it-IT
	"|住所2",                                   // ja-JP
	"|complemento|addrcomplement",              // pt-BR, pt-PT
	"|Улица",                                   // ru
	"|地址2",                                   // zh-CN
	"|주소.?2"].join(''), 'i');                                // ko-KR
var addrLine3 = new RegExp(["address.*line[3-9]|address[3-9]|addr[3-9]|street|line[3-9]",
	"|municipio",           // es
	"|batiment|residence",  // fr-FR
	"|indirizzo[3-9]"].join(''), 'i');     // it-IT
var country = new RegExp(["country|countries",
	"|país|pais",                         // es
	"|(\\b|_)land(\\b|_)(?!.*(mark.*))",  // de-DE landmark is a type in india.
	"|(?<!(入|出))国",                    // ja-JP
	"|国家",                              // zh-CN
	"|국가|나라",                         // ko-KR
	"|(\\b|_)(ülke|ulce|ulke)(\\b|_)",    // tr
	"|کشور"].join(''), 'i');                             // fa
var zipCode =  new RegExp(["zip|postal|post.*code|pcode",
	"|pin.?code",                   // en-IN
	"|postleitzahl",                 // de-DE
	"|\\bcp\\b",                     // es
	"|\\bcdp\\b",                    // fr-FR
	"|\\bcap\\b",                    // it-IT
	"|郵便番号",                     // ja-JP
	"|codigo|codpos|\\bcep\\b",      // pt-BR, pt-PT
	"|Почтовый.?Индекс",             // ru
	"|पिन.?कोड",                     // hi
	"|പിന്‍കോഡ്",  // ml
	"|邮政编码|邮编",                // zh-CN
	"|郵遞區號",                     // zh-TW
	"|(\\b|_)posta kodu(\\b|_)",     // tr
	"|우편.?번호"].join(''), 'i');                  // ko-KR
var city = new RegExp(["city|town",
	"|\\bort\\b|stadt",                                  // de-DE
	"|suburb",                                           // en-AU
	"|ciudad|provincia|localidad|poblacion",             // es
	"|ville|commune",                                    // fr-FR
	"|localita",                                         // it-IT
	"|市区町村",                                         // ja-JP
	"|cidade",                                           // pt-BR, pt-PT
	"|Город",                                            // ru
	"|市",                                               // zh-CN
	"|分區",                                             // zh-TW
	"|شهر",                                              // fa
	"|शहर",                                             // hi for city
	"|ग्राम|गाँव",                                        // hi for village
	"|നഗരം|ഗ്രാമം",                                       // ml for town|village
	"|((\\b|_|\\*)([İii̇]l[cç]e(miz|niz)?)(\\b|_|\\*))",  // tr
	"|^시[^도·・]|시[·・]?군[·・]?구"], 'i');                  // ko-KR
var state = new RegExp(["(?<!(united|hist|history).?)state|county|region|province",
	"|county|principality",  // en-UK
	"|都道府県",             // ja-JP
	"|estado|provincia",     // pt-BR, pt-PT
	"|область",              // ru
	"|省",                   // zh-CN
	"|地區",                 // zh-TW
	"|സംസ്ഥാനം",              // ml
	"|استان",                // fa
	"|राज्य",                 // hi
	"|((\\b|_|\\*)(eyalet|[şs]ehir|[İii̇]l(imiz)?|kent)(\\b|_|\\*))",  // tr
	"|^시[·・]?도"].join(''), 'i');                                                  // ko-KR
var email = new RegExp(["e.?mail",
	"|courriel",                 // fr
	"|correo.*electr(o|ó)nico",  // es-ES
	"|メールアドレス",           // ja-JP
	"|Электронной.?Почты",       // ru
	"|邮|邮箱",                // zh-CN
	"|用户名",
	"|電郵地址",                 // zh-TW
	"|ഇ-മെയില്‍|ഇലക്ട്രോണിക്.?",
	"മെയിൽ",                                        // ml
	"|ایمیل|پست.*الکترونیک",                        // fa
	"|ईमेल|इलॅक्ट्रॉनिक.?मेल",                           // hi
	"|(\\b|_)eposta(\\b|_)",                        // tr
	"|(?:이메일|전자.?우편|[Ee]-?mail)(.?주소)?"].join(), 'i');  // ko-KR
var fullName = new RegExp(["^name|full.?name|your.?name|customer.?name|bill.?name|ship.?name",
	"|name.*first.*last|firstandlastname",
	"|nombre.*y.*apellidos",                    // es
	"|^nom(?!bre)",                             // fr-FR
	"|お名前|氏名",                             // ja-JP
	"|^nome",                                   // pt-BR, pt-PT
	"|نام.*نام.*خانوادگی",                      // fa
	"|姓名",                                    // zh-CN
	"|(\\b|_|\\*)ad[ı]? soyad[ı]?(\\b|_|\\*)",  // tr
	"|성명"].join(''), 'i');                                   // ko-KR
var firstName = new RegExp(["first.*name|initials|fname|first$|given.*name",
	"|vorname",                                             // de-DE
	"|nombre",                                              // es
	"|forename|prénom|prenom",                              // fr-FR
	"|名",                                                  // ja-JP
	"|nome",                                                // pt-BR, pt-PT
	"|Имя",                                                 // ru
	"|نام",                                                 // fa
	"|이름",                                                // ko-KR
	"|പേര്",                                                 // ml
	"|(\\b|_|\\*)(isim|ad|ad(i|ı|iniz|ınız)?)(\\b|_|\\*)",  // tr
	"|नाम"].join(''), 'i');                                                // hi
var middleName = new RegExp(["middle.*name|mname|middle$",
	"|apellido.?materno|lastlastname"].join(''), 'i');  // es
var lastName = new RegExp(["last.*name|lname|surname(?!\\d)|last$|secondname|family.*name",
	"|nachname",                                               // de-DE
	"|apellidos?",                                             // es
	"|famille|^nom(?!bre)",                                    // fr-FR
	"|cognome",                                                // it-IT
	"|姓",                                                     // ja-JP
	"|apelidos|surename|sobrenome",                            // pt-BR, pt-PT
	"|Фамилия",                                                // ru
	"|نام.*خانوادگی",                                          // fa
	"|उपनाम",                                                  // hi
	"|മറുപേര്",                                                  // ml
	"|(\\b|_|\\*)(soyisim|soyad(i|ı|iniz|ınız)?)(\\b|_|\\*)",  // tr
	"|\\b성(?:[^명]|\\b)"].join(''), 'i');                                    // ko-KR
var countryCode = new RegExp(["country.*code|ccode|_cc|phone.*code|user.*phone.*code"].join(''), 'i');
var areaCode = new RegExp(["area.*code|acode|area",
    "|지역.?번호"].join(''), 'i')  // ko-KR
var phonePrefix = new RegExp(["prefix|exchange",
    "|preselection",  // fr-FR
    "|ddd"].join(''), 'i');          // pt-BR, pt-PTff
var phoneSuffix = new RegExp(["suffix"].join(''), 'i');
// credit_card form
var nameOnCard = new RegExp(["card.?(?:holder|owner)|name.*(\\b)?on(\\b)?.*card",
    "|(?:card|cc).?name|cc.?full.?name",
    "|karteninhaber",                   // de-DE
    "|nombre.*tarjeta",                 // es
    "|nom.*carte",                      // fr-FR
    "|nome.*cart",                      // it-IT
    "|名前",                            // ja-JP
    "|Имя.*карты",                      // ru
    "|信用卡开户名|开户名|持卡人姓名",  // zh-CN
    "|持卡人姓名"].join(''), 'i');                     // zh-TW
var cardNumber = new RegExp(["(add)?(?:card|cc|acct).?(?:number|#|no|num|field)",
    "|(?<!telefon|haus|person|fødsels)nummer",  // de-DE, sv-SE, no
    "|カード番号",                              // ja-JP
    "|Номер.*карты",                            // ru
    "|信用卡号|信用卡号码",                    // zh-CN
    "|信用卡卡號",                              // zh-TW
    "|카드"].join(''), 'i')                     // ko-KR
    "|(numero|número|numéro)(?!.*(document|fono|phone|réservation))";  // es/pt/fr
var expirationMonth = new RegExp(["expir|exp.*mo|exp.*date|ccmonth|cardmonth|addmonth",
    "|gueltig|gültig|monat",  // de-DE
    "|fecha",                 // es
    "|date.*exp",             // fr-FR
    "|scadenza",              // it-IT
    "|有効期限",              // ja-JP
    "|validade",              // pt-BR, pt-PT
    "|Срок действия карты",   // ru
    "|月"].join(''), 'i');                   // zh-CN
var expirationYear = new RegExp(["exp|^/|(add)?year",
    "|ablaufdatum|gueltig|gültig|jahr",  // de-DE
    "|fecha",                            // es
    "|scadenza",                         // it-IT
    "|有効期限",                         // ja-JP
    "|validade",                         // pt-BR, pt-PT
    "|Срок действия карты",              // ru
	"|年|有效期"].join(''), 'i');                       // zh-CN
var expirationDate = new RegExp(["expir|exp.*date|^expfield$",
    "|gueltig|gültig",        // de-DE
    "|fecha",                 // es
    "|date.*exp",             // fr-FR
    "|scadenza",              // it-IT
    "|有効期限",              // ja-JP
    "|validade",              // pt-BR, pt-PT
    "|Срок действия карты"].join(''), 'i');  // ru

var typePatts = {"Email": email, "Phone": phone, "Address Line1": addrLine1, "Address Line2": addrLine2, "Address Line3": addrLine3, "Country Code": countryCode, "Area Code": areaCode, "Phone Prefix": phonePrefix, "Phone Suffix": phoneSuffix, "Country": country, "State": state, "City": city, "Company": company,"Zipcode": zipCode, "Full Name": fullName, "First Name": firstName, "Middle Name": middleName, "Last Name": lastName, "Card Name": nameOnCard,  "Card Number": cardNumber, "Card Expiration Date": expirationDate, "Card Expiration Month": expirationMonth, "Card Expiration Year": expirationYear}
var addressTypes = Object.keys(typePatts).slice(0, 18), ccTypes = Object.keys(typePatts).slice(18, 23);
//chrome autofillable types
var inputTypes = ["text", "email", "tel", "number", "month", "password", "search", "textarea"];
var selectTypes = ["select-one"];

/////////////////////////////////////////////////////////////////////////////
//identify autofill type based on autocomplete attribute
//extracted from chromium source code https://source.chromium.org/chromium/chromium/src/+/master:components/autofill/core/browser/form_structure.cc
/////////////////////////////////////////////////////////////////////////////
function TypeFromAutocompleteAttributeValue(el){
	var autocompleteValue = el.getAttribute('autocomplete');

	if (autocompleteValue == "")
	return false;

  if (autocompleteValue == "name")
    return "Full Name";

  if (autocompleteValue == "given-name" ||
      autocompleteValue == "given_name" ||
      autocompleteValue == "first-name" ||
      autocompleteValue == "first_name")
    return "First Name";

  if (autocompleteValue == "additional-name" ||
      autocompleteValue == "additional_name") {
    if (el.maxLength == 1)
      return "Middle Name Initial";
    return "Middle Name";
  }

  if (autocompleteValue == "family-name" ||
      autocompleteValue == "family_name")
    return "Familiy Name";

  if (autocompleteValue == "organization" ||
      autocompleteValue == "company")
    return "Organization";

  if (autocompleteValue == "street-address" ||
      autocompleteValue == "street_address" ||
      autocompleteValue == "address")
    return "Street Address";

  if (autocompleteValue == "address-line1" ||
      autocompleteValue == "address_line1")
    return "Address Line1";

  if (autocompleteValue == "address-line2" ||
      autocompleteValue == "address_line2")
    return "Address Line2";

  if (autocompleteValue == "address-line3" ||
      autocompleteValue == "address_line3")
    return "Address Line3";

  if (autocompleteValue == "locality")
    return "Address Level2";

  if (autocompleteValue == "region")
    return "Address Level1";

  if (autocompleteValue == "address-level1" ||
      autocompleteValue == "address_level1")
    return "Address Level1";

  if (autocompleteValue == "address-level2" ||
      autocompleteValue == "address_level2")
    return "Address Level2";

  if (autocompleteValue == "address-level3" ||
      autocompleteValue == "address_level3")
    return "Address Level3";

  if (autocompleteValue == "country")
    return "Country Code";

  if (autocompleteValue == "country-name" ||
      autocompleteValue == "country_name")
    return "Country";

  if (autocompleteValue == "postal-code" ||
      autocompleteValue == "postal_code")
    return "Zipcode";

  if (autocompleteValue == "cc-name" ||
      autocompleteValue == "cc_name")
    return "Card Name";

  if (autocompleteValue == "cc-given-name" ||
      autocompleteValue == "cc_given_name")
    return "First Name";

  if (autocompleteValue == "cc-family-name" ||
      autocompleteValue == "cc_family_name")
    return "Last Name";

  if (autocompleteValue == "cc-number" ||
      autocompleteValue == "cc_number")
    return "Card Number";

  if (autocompleteValue == "cc-exp" ||
      autocompleteValue == "cc_exp") {
    if (el.maxLength == 5)
	  return "Card Expiration Year";
    if (el.maxLength == 7)
      return "Card Expiration Year";
    return "Card Expiration Date";
  }

  if (autocompleteValue == "cc-exp-month" ||
      autocompleteValue == "cc_exp_month")
    return "Card Expiration Month";

  if (autocompleteValue == "cc-exp-year" ||
      autocompleteValue == "cc_exp_year") {
    if (field.max_length == 2)
      return "Card Expiration Year";
    if (field.max_length == 4)
      return "Card Expiration Year";
    return "Card Expiration Year";
  }

  if (autocompleteValue == "tel" ||
      autocompleteValue == "phone")
    return "Phone";

  if (autocompleteValue == "tel-country-code" ||
      autocompleteValue == "phone-country-code" ||
      autocompleteValue == "tel_country_code" ||
      autocompleteValue == "phone_country_code")
    return "Country Code";

  if (autocompleteValue == "tel-national" ||
      autocompleteValue == "phone-national" ||
      autocompleteValue == "tel_national" ||
      autocompleteValue == "phone_national")
    return "Phone National";

  if (autocompleteValue == "tel-area-code" ||
      autocompleteValue == "phone-area-code" ||
      autocompleteValue == "tel_area_code" ||
      autocompleteValue == "phone_area_code")
    return "Area Code";

  if (autocompleteValue == "tel-local" ||
      autocompleteValue == "phone-local" ||
      autocompleteValue == "tel_local" ||
      autocompleteValue == "phone_local")
    return "Phone Local";

  if (autocompleteValue == "tel-local-prefix" ||
      autocompleteValue == "phone-local-prefix" ||
      autocompleteValue == "tel_local_prefix" ||
      autocompleteValue == "phone_local_prefix")
    return "Phone Prefix";

  if (autocompleteValue == "tel-local-suffix" ||
      autocompleteValue == "phone-local-suffix" ||
      autocompleteValue == "tel_local_suffix" ||
      autocompleteValue == "phone_local_suffix")
    return "Phone Suffix";

  if (autocompleteValue == "email" ||
      autocompleteValue == "username")
    return "Email";

  return false;
}

/////////////////////////////////////////////////////////////////////////////
//identify autofill type based on el's attributes
/////////////////////////////////////////////////////////////////////////////
function identifyType(el){
	//autofill type determined by autocomplete;
	var type = TypeFromAutocompleteAttributeValue(el);
	if(type){
		if(debugMode) console.log('type from autocomplete--', type);
		return type;
	}
	//autofill type determined by label, name, value, id, placeholder;
	var labelVal =  (el.labels[0]) ? el.labels[0].textContent : '';
	var elAttrs = [labelVal, el.name, el.value, el.id, el.placeholder];
	if(debugMode) console.log(elAttrs);
	// <select> of country type may not have matching attributes. look at options
	if(el.tagName == 'SELECT'){
		optionLen = el.options.length;
		if(optionLen >= 50){
			try{
				for(var i = 0; i<= optionLen; i++){
					if(el.options[i].text.includes("Austria")){
						return "Country";
					}
				}
			}catch(e){
			}
		}
	}
	for (var prop in typePatts) {
		for(var i = 0; i < elAttrs.length; i++){
			if(elAttrs[i] && elAttrs[i].match(typePatts[prop])){
				return prop;
			}
			}
		}
	return false;
}


function filterEls(els){
	var filteredEls = [];
	for (var i = 0; i < els.length; i++) {
		if((els[i].tagName === 'INPUT' && inputTypes.includes(els[i].type)) || (els[i].tagName === 'SELECT'&& selectTypes.includes(els[i].type))){
			filteredEls.push(els[i]);
		}
	}
	return filteredEls;
}

function getForms(){
	var elGroups = {}, nonFormEls = [], formEls = [];
	var allEls = filterEls(Array.from(document.getElementsByTagName('INPUT')).concat(Array.from(document.getElementsByTagName('SELECT'))));
	formsCollection = document.getElementsByTagName('form');
	for(var i = 0; i < formsCollection.length; i++)
	{
		var inputEls = filterEls(formsCollection[i].elements);
		if(inputEls.length){
			elGroups[i] = inputEls;
			formEls = formEls.concat(elGroups[i]);
		}
	}
	if(allEls.length !== formEls.lengh){
		nonFormEls = allEls.filter(el => !formEls.includes(el));
		elGroups["-1"] = nonFormEls; //fields outside of form
	}
	if(debugMode) {console.log(elGroups)};
	return elGroups;
}

function ifAutofillable(visibileEls, hiddenEls, visibleTypes, hiddenTypes){
	inputFlag = 0;
	for(var t = 0; t < visibileEls.length; t++){
		if(visibileEls[t][2].tagName === 'INPUT'){
			inputFlag = 1;
		}
	}
	if(!inputFlag){
		if(debugMode) console.log('no visible input')
		unautofillableDetected = unautofillableDetected.concat(hiddenEls);
		return null;
	}
	var foundCC = ccTypes.some(r=> hiddenTypes.includes(r));
	if(foundCC && !ccTypes.some(r=> visibleTypes.includes(r))){
		for(var i = 0; i < hiddenEls.length; i++){
			if(ccTypes.includes(hiddenEls[i][0])){
				if(debugMode) console.log('remove unautofillable cc types', hiddenEls[i][2]);
				hiddenEls.splice(i,1);
				i = -1;
			}
		}
	}
	if(debugMode) console.log('hidden els--', hiddenEls)
	return hiddenEls;
}

/////////////////////////////////////////////////////////////////////////////
//perform the checks on visibility
/////////////////////////////////////////////////////////////////////////////
scrollFlag = 0;
function performChecks(elGroups, mode){
	for (const formNum in elGroups) {
		var visibleTypes = [], hiddenTypes = [], els = elGroups[formNum], hiddenEls = [], visibileEls = [];
		if(debugMode) {
			console.log('form--', formNum)
			console.log(els);
		}
		if(els.length < 2){
			continue;
		}
		if(els.length == 2){
			autoArr = [els[0].autocomplete, els[1].autocomplete];
			if(autoArr.length < 2 || autoArr.some(el => ["off", "on"].includes(el))){
				if(debugMode) console.log(autoArr, '2 elements without autocomplete specified');
				continue;
			}
		}
		for (var i = 0, len = els.length; i < len; i++) {
			var el = els[i];
			if(el.tagName === 'INPUT' && !inputTypes.includes(el.type)) {continue;}
			var fillType = identifyType(el)
			if(!fillType) {continue;}
			elPos = el.getBoundingClientRect();
			if(debugMode) console.log('precessing--', el);
			var visi = ifHidden(el, elPos);
			if(debugMode) console.log('type--', fillType, visi);
			if(visi){
				if(['display', 'visibility'].some(r=> visi.includes(r)) && el.tagName === 'INPUT'){ //<input> hidden by display/visibility are not autofillable
					unautofillableDetected.push([fillType, visi, el]);
				}else{
					hiddenEls.push([fillType, visi, el]);
					hiddenTypes.push(fillType);
				}
			}
			else{
				visibileEls.push([fillType, visi, el]);
				visibleTypes.push(fillType);
			}
			}
		var filterEls = ifAutofillable(visibileEls, hiddenEls, visibleTypes, hiddenTypes);
		if(!!filterEls)
			detected = detected.concat(filterEls);
	}
	if(scrollFlag) window.scrollTo(0, 0);
	if (!detected.length && debugMode){
		console.log('no such element');
	}
	else{
		if(debugMode) console.log('detected hidden els--', detected, detected.length);
		if (mode == 'strict'){
			for (var k = 0, len = detected.length; k < len; k++) {
				var el = detected[k][2];
				if(debugMode) console.log('strict--', el);
				el.parentNode.removeChild(el);
			}
		}
		if (mode == 'lax'){
			var labels = new Array;
			for (var k = 0, len = detected.length; k < len; k++) {
				var el = detected[k];
				labels.push(el);
			}
			uniqueLabels = labels.filter(function(item, pos) {
				return labels.indexOf(item) == pos;
			});
			var numHid = uniqueLabels.length;
			var message = '';
			var hasVisibleTypes = new Array;
			var hiddenTypes = [];
			for (var k = 0, len = uniqueLabels.length; k < len; k++) {
				if(visibleTypes.includes(uniqueLabels[0])){
					hasVisibleTypes.push(uniqueLabels[0]);
				}
				var elHTML = uniqueLabels[k][2].outerHTML.substring(0,100).replace(/</g, '&lt;').replace(/>/g, '&gt;')+'...';
				var hiddenReason = uniqueLabels[k][1];
				hiddenTypes.push(uniqueLabels[k][0]);
				message += (`${elHTML}<span style="color: #E0C91F"> ${uniqueLabels[k][0]}</span> filltype hidden by <span style="color: #E0C91F">${hiddenReason}</span>.<br>`);
			}
			var addressLine = ['Address Line1', 'Address Line2', 'Address Line3'];
			for(var i = 0; i < 3; i++){
				var indexAddress = hiddenTypes.indexOf(addressLine[i]);
				if (indexAddress !== -1) {
					hiddenTypes[indexAddress] = 'Street Address';
				}
			}
			hiddenTypes = [...new Set(hiddenTypes)];
			if(hasVisibleTypes.length){
				var messageAdd = '';
				for(var t=0; t < hasVisibleTypes; t++){
					messageAdd = `hidden elements ${hasVisibleTypes} have identical visible ones `
				}
			}
			var warning = document.createElement('div');
			warning.id = "warning";
			warning.innerHTML = `This page has hidden input fields to collect: <span style="color: #E0C91F">${hiddenTypes.join(", ")}</span>. Please do not use autofill or`;
			document.body.appendChild(warning);
			addEl('span', 'strict', 'Enable Strict Mode', warning);
			addEl('span', 'end', '.', warning);
			addEl('div', 'close', 'X', warning);
			addEl('div', 'popup', 'More Info', warning);
			var more = document.getElementById('popup');
			var hiddenMessage = `<span style="color: #809fff; font-weight:bold">This page has ${numHid} hidden fields that are autofillable in Chrome.</span> <br> ${message}`;
			addEl('span','popuptext', hiddenMessage, warning);
			var popupText = document.getElementById('popuptext');
			popupText.style.display = 'none';
			toggleInfo(more, popupText);
			addEl('div', 'closeMore', 'X', popupText);
			var closeMore = document.getElementById('closeMore');
			closeWindow(closeMore);
			var close = document.getElementById('close');
			closeWindow(close);
			closeMore.addEventListener('click', function(){
				more.innerHTML = 'More Info';
			})
			var enableMode = document.getElementById('strict');
			enableMode.addEventListener('click', () => {
				if(debugMode) console.log('set strict mode');
				chrome.storage.local.set({'mode': 'strict'});
				chrome.runtime.sendMessage({command: 'strict'});
			})
			if(!!unautofillableDetected.length){
				more.style.display = 'none';
				if(debugMode) console.log('unautofillable els', unautofillableDetected);

				var addMessage = '';
				for (var k = 0; k < unautofillableDetected.length; k++) {
					var addElHTML = unautofillableDetected[k][2].outerHTML.substring(0,100).replace(/</g, '&lt;').replace(/>/g, '&gt;')+'...';
					addMessage += (`${addElHTML} <span style="color: #E0C91F">${unautofillableDetected[k][0]}</span> filltype hidden by <span style="color: #E0C91F">${unautofillableDetected[k][1]}</span><br>`);
				}
				addEl('span', 'addText', `<br>This page includes additional hidden input fields that will not be autofilled by Chrome.`, warning);
				addEl('div', 'addPopup', 'More Info', warning);
				addEl('span','addPopuptext', `${hiddenMessage} <span style="color: #809fff; font-weight:bold">Chrome will not autofill ${unautofillableDetected.length} additional hidden fields</span>.<br> ${addMessage}`, warning);
				var addMore = document.getElementById('addPopup');
				var textAdd = document.getElementById('addPopuptext');
				addEl('div', 'closeAdd', 'X', textAdd);
				var closeAdd = document.getElementById('closeAdd');
				closeWindow(closeAdd);
				textAdd.style.display = 'none';
				toggleInfo(addMore, textAdd);
				closeAdd.addEventListener('click', function(){
					addMore.innerHTML = 'More Info';
				})
				}
		}
	}
}
function addEl(tagText, idText, htmlText, parentEl){
	var el = document.createElement(tagText);
	el.id =idText;
	el.innerHTML = htmlText;
	parentEl.appendChild(el);
}
function closeWindow(el){
	el.addEventListener("click", function() {
		this.parentElement.style.display = 'none';
	})
}
function toggleInfo(el, textEl){
	el.addEventListener('click', ()=>{
		if (textEl.style.display  === 'none') {
			textEl.style.display  = 'block';
			el.innerHTML = 'Close Info';
		} else {
			textEl.style.display  = 'none';
		  	el.innerHTML = 'More Info';
		}
	})
}
/////////////////////////////////////////////////////////////////////////////
//calculate the visibility
/////////////////////////////////////////////////////////////////////////////

function ifHidden(el, elPos){
	// OK!!  -- display property of el
	// els hidden by the display/visibility property have no effective size
	if (checkDisplay(el)){
		return 'css property display:none';
	}
	// OK!!  -- display property of ancestors
	if (checkDisplayAncestors(el)){
		return 'css property display:none of ancestor';
	}
	// OK!!  -- visibility property of el
	if (checkVisibility(el)){
		return 'css property visibility:none/collapse';
	}
	// OK!!  -- visibility property of ancestors
	if (checkVisibilityAncestors(el)){
		return 'css property visibility:none/collapse of ancestor';
	}
	// OK!!  -- els of non-effective size
	if (checkNonEffectiveSize(el, elPos)) {
		return 'having non-effective size';
	}
	// OK!!  -- els out of the screen
	if (checkOffScreen(el, elPos)) {
		return 'being offscreen';
	}
	// OK!!  -- opacity property of el
	// set 0.0 as the threshold
	if (checkOpacity(el, 0.0)){
		return 'being transparent';
	}

	// OK!!  -- opacity property of ancetors
	if (checkOpacityAncestors(el, 0.0)){
		return 'having transparent ancestor';
	}

	// OK!!  -- overflow property of ancetors of non-effective size
	if (checkAncestorsOverflow(el, elPos)) {
		return 'being out of bounds of ancetor';
	}

	// OK!!  -- el is out of the bounds of ancestor's overflow
	if (checkAncestorsOverflowClip(el)){
		return 'being out of bounds of ancestor';
	}

	// OK!!  -- covered by another non-transparent el
	if (checkIfCovered(el, elPos)) {
		return 'being covered by another element';
	}
	return false;
}

function checkNonEffectiveSize(el, elPos) {
	if(debugMode) console.log('checking non-effective size');
	return (elPos.height <= 0) || (elPos.width <= 0) ;
}

function checkDisplay(el) {
	if(debugMode) console.log('checking display');
    var style = window.getComputedStyle(el);
    return  style.display === 'none'
}

function checkDisplayAncestors(el) {
	if(debugMode) console.log('checking display ancestors');
	for ( ; el && el !== document; el = el.parentNode ) {
		var style = window.getComputedStyle(el);
		if(style.display === 'none'){
			return true;
		}
	}
	return false;
}

function checkVisibility(el) {
	if(debugMode) console.log('checking visibility');
    var style = window.getComputedStyle(el);
    return (style.visibility === 'hidden') || (style.visibility === 'collapse')
}

function checkVisibilityAncestors(el) {
	if(debugMode) console.log('checking visibility ancestors');
	for ( ; el && el !== document; el = el.parentNode ) {
		var style = window.getComputedStyle(el);
		if ((style.visibility === 'hidden') || (style.visibility === 'collapse')) {
			return true;
		}
	}
	return false;
}

//we do NOT consider select tag. Options cannot be fully transparent, as they are OS/browser dependent.
function checkOpacity(el, threshold) {
	if(debugMode) console.log('checking opacity');
	if (el.tagName == 'select'){
		return false
	}
	var style = getComputedStyle(el);
	if (style.opacity <= threshold){
		siEl = el.previousElementSibling;
		parentEl = el.parentNode;
		if(ifVisibleLable(siEl)||ifVisibleLable(parentEl)){
			return false;
		//there is a label el or a dedicated parent node to make it visually visible
		} else if (!isRoot(parentEl) && parentStyle.opacity > threshold && parentEl.childElementCount<=1 ){
			if(debugMode)
				console.log('visible due to dedicated parent el')
			return false;
		} else {
			return true;
		}
	}
	return false;
}

function ifVisibleLable(el){
	if(!el)
		return false
	var elStyle = getComputedStyle(el);
	if(el.tagName == 'LABEL' && elStyle.opacity > threshold)
		if(debugMode)
			console.log(el, 'visible label');
		return true;
	return false;
}

//opacity is not inherited, but el cannot be less transparent than the parent
function checkOpacityAncestors(el, threshold) {
	if(debugMode) console.log('checking opacity ancestors');
	if (el.tagName == 'select'){
		return false
	}
	el = el.parentNode;
	for ( ; el && el !== document; el = el.parentNode ) {
		var style = window.getComputedStyle(el);
		if (style.opacity <= threshold){
			return true
		}
	}
	return false;
}

//if the el is position fixed, we consider x >= win_width or y >= self.win_height
function checkOffScreen(el, elPos){
	if(debugMode) console.log('checking offscreen');
	window.scrollTo(elPos.x, elPos.y - 300);
	scrollFlag = 1;
	if ((elPos.x + elPos.width <=0) || (elPos.y + elPos.height <=0)){
		if(debugMode) console.log(elPos.x, elPos.width, elPos.y, elPos.height);
		return true
	}
	for ( ; el && el !== document; el = el.parentNode) {
		var style = window.getComputedStyle(el);
		if (style.position == 'fixed'){
			if((elPos.x >= window.innerWidth) || (elPos.y >= window.innerHeight)){
				console.log('fixed--', elPos.x, window.innerWidth, elPos.y, window.innerHeight);
				return true
			}
		}
	}
	return false
}

function isDescendant(topEl, bottomEl){
	for ( ; topEl && (!isRoot(topEl)); topEl = topEl.parentNode ) {
		if (topEl === bottomEl){
			return true
		}
	return false
	}
}

function determinePosition(el, pos){
	if(el.style.position === pos|| (el.offsetParent && el.offsetParent.style.position === pos))
		return true;
	return false;
}

// use the center point instead of top-left
// top el at the point is different, not transparent, and has fixed|absolute position,
// top el is fixed, covered el has to be fixed
// top el is absolute, covered el cannot be fixed
// display:none/visibility:hidden will return True
function checkIfCovered(el, elPos){
	if(debugMode) console.log('checking covered');
	if(elPos.x >= window.innerWidth || elPos.y >= window.innerHeight || elPos.y <= 0){
		window.scrollTo(elPos.x, elPos.y - 300); //leave 300px for the navigator bar
		scrollFlag = 1;
	}
	elPos = el.getBoundingClientRect();
	var xCenter = elPos.x + elPos.width/2;
	var yCenter = elPos.y + elPos.height/2;
	topEl = document.elementFromPoint(xCenter, yCenter);
	if (topEl && (topEl != el) && (!isDescendant(topEl, el))){
		if(debugMode) console.log('top element', topEl, xCenter, yCenter);
		if (topEl.tag_name === 'label' && topEl.childNodes.length === 0){
			if(debugMode) console.log('top element is the label for', topEl.getAttribute('for'))
			return false
		}
		if(isRoot(topEl)){
			if(debugMode) console.log('it is root el')
			return false;
		}
		for ( ; topEl && (!isRoot(topEl)); topEl = topEl.parentNode) {
			if(debugMode) console.log('checking top element');
			if (checkVisibility(topEl)||checkDisplay(topEl)||checkVisibilityAncestors(topEl)||checkDisplayAncestors(topEl)){
				return false
			}
			var topStyle = getComputedStyle(topEl);
			if (topStyle.position !== 'static' || (!['BODY', 'HTML'].includes(topEl.offsetParent.tagName))){
				if (topStyle.opacity < 1.0 || checkOpacityAncestors(topStyle, 1.0)){
					if(debugMode)
						console.log('top element is transparent');
					return false;
				} else{
					topRect = topEl.getBoundingClientRect();
					topX = topRect.x;
					topY = topRect.y;
					topWidth = topRect.width;
					topHeight = topRect.height;
					if(debugMode){
						console.log(topX, topY, topWidth, topHeight);
						console.log(elPos.x, elPos.y, elPos.width, elPos.height);
					}
					//allow small deviation
					if (((topX + topWidth) >= (elPos.x + elPos.width - 2)) && ((topY + topHeight) >= (elPos.y + elPos.height - 2))){
						if(determinePosition(topEl, 'absolute') && determinePosition(el, 'fixed')){
							if(debugMode)
								console.log('top element has absolute position and element has fixed position');
							return false
						}
						if(determinePosition(topEl, 'fixed') && !determinePosition(el, 'fixed')){
							if(debugMode)
								console.log('top element has fixed position but element has not')
						}
						return true
					}
				}
			}
		}
	}
	return false
}

function overflowHidden(el){
	elStyle = getComputedStyle(el);
	if((elStyle.overflow + elStyle.overflowX + elStyle.overflowY).includes('hidden'))
		return true;
	return false;
}

//ancestor has hidden overflow properties and not effective size
//any el between el and ancestor(not included) is not fixed or absolute position
function checkAncestorsOverflow(el){
	if(debugMode) console.log('checking ancestor overflow hidden');
	parentEl = el.parentNode;
	flag = false;
	for ( ; parentEl && parentEl !== document; parentEl = parentEl.parentNode ) {
		var parentPos = parentEl.getBoundingClientRect();
		if (overflowHidden(parentEl) && checkNonEffectiveSize(parentEl, parentPos)){
			ancestor = parentEl;
			flag = true;
			break;
		}
	}
	if (!flag){
		return false
	}
	el = el.parentNode;
	for ( ; el && el != ancestor; el = el.parentNode) {
		var el_style = window.getComputedStyle(el);
		if ((el_style.position == 'absolute') || (el_style.position == 'fixed')){
			return false
		}
	}
	return true
}


function isRoot(el){
	if(['BODY', 'HTML'].includes(el.tagName) || el === window.document)
		return true
	return false
}

//ancestor has hidden overflow properties
//offset parent is a parent of the ancestor and el's position is absolute, false
//offset parent is a child of the ancestor and offset parent's position is absolute, false
function checkAncestorsOverflowClip(el){
	if(debugMode) console.log('checking out of bounds of ancestor overflow');
	parentEl = el.parentNode;
	offsetParentEl = el.offsetParent;
	if(debugMode)
		console.log('offsetparent', offsetParentEl);
	if (isRoot(parentEl)){
		return false
	} else {
		var flag = false;
		while(!isRoot(parentEl)) {
			if (overflowHidden(parentEl)){
				ancestor = parentEl;
				flag = true;
				break;
			}
			parentEl = parentEl.parentNode;
		}
		if (!flag){
			return false;
		}
		if (ancestor.tagName == 'label'){
			return false;
		}
		if (offsetParentEl){
			var style = getComputedStyle(el);
			var offsetStyle = getComputedStyle(offsetParentEl);
			if (isChild(offsetParentEl, ancestor) && (style.position == 'absolute')){
				if(debugMode)
					console.log("offset parent is a parent of the ancestor and el's position is absolute");
				return false;
			}
			var ancStyle = getComputedStyle(ancestor);
			if (isChild(ancestor, offsetParentEl) && (offsetStyle.position == 'absolute')){
				if(debugMode)
					console.log("offset parent is a child of the ancestor and offset parent's position is absolute");
				return false;
			}
		}
		ancestorRec = ancestor.getBoundingClientRect();
		ancestorX = ancestorRec.x;
		ancestorY = ancestorRec.y;
		ancestorWidth = ancestorRec.width;
		ancestorHeight = ancestorRec.height;
		elRec = el.getBoundingClientRect();
		elX = elRec.x;
		elY = elRec.y;
		elWidth = elRec.width;
		elHeight = elRec.height;
		if ((elX > ancestorX + ancestorWidth) || (elX + elWidth < ancestorX) || (elY > ancestorY + ancestorHeight) || (elY + elHeight < ancestorY)){
			return true;
		}
		else{
			if(debugMode)
				console.log('inside the bounds of ancestor');
			return false;
		}
	}
}

function isChild(parentEl, el){
	while(!isRoot(el)) {
		if (parentEl == el){
			return true;
		}
		el = el.parentNode;
	}
	return false;
}

//future work: hidden by clip-path property
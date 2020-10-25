var inputArr = [];
$( ":input" ).change(function(){
    var input = $(this);
    var inputObj = {};
    inputObj[this.name] =  this.value;
    //console.log("obj", inputObj)
    inputArr.push(inputObj); 
    
})
var str = "";
$('#name').change(function(){
    setTimeout(function(){
        inputArr.forEach(function (item, index) {
            //console.log(JSON.stringify(item));
            str = str.concat(JSON.stringify(item)+'\n');
            });
    alert(str);
    }, 1);
})


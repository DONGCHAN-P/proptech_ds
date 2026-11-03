$(document).ready(function(){
	/*$(".tab > li").click(function(){
		var index = $(this).index();
		$(this).addClass("on").siblings().removeClass("on");
		$(".tab-cont > div").eq(index).addClass("on").siblings().removeClass("on");
	});
	$(".tab2 > li").click(function(){
		var index = $(this).index();
		$(this).addClass("on").siblings().removeClass("on");
		$(".tab-cont2 > div").eq(index).addClass("on").siblings().removeClass("on");
	});*/
	
});

//숫자만 입력
function InpuOnlyNumber(event,obj){
	var chkKey = event.key;
	var regexp = /^[0-9\b]*$/

	if(!regexp.test(chkKey)) {
		if(chkKey =='Backspace'){
			return true;
		}else{
			event.returnValue = false;
			return false;
		}
	} else {
		return true;
	}
}

// 숫자 구분단위 컴마 찍기
var formatCommas = function(numString) {
	if(isNaN(numString)){
		return numString;
	}else{
		var tempNum1, tempNum2;
		numString = numString.toString();
		if(numString.indexOf(".")!=-1){
			var tempNum = numString.split(".");
			tempNum1 = tempNum[0];
			tempNum2 = "."+tempNum[1];
		}else{
			tempNum1 = numString;
			tempNum2 = "";
		}
		var re = /(-?\d+)(\d{3})/;
		while (re.test(tempNum1)) {
			tempNum1 = tempNum1.replace(re, "$1,$2");
		}
		return tempNum1+tempNum2;
	}
}

var stripCommas = function(numString){
	var re = /,/g;
	if(numString == "" || numString == null){
		return 0;
	}
	return numString.replace(re,"");
}

function set_price(field_id) {
	//return;
	frm = $("#" + field_id );
	var originVal = frm.val();
	var frm_price = originVal.replace(/[^0-9]/g, "");
	frm_price = frm_price.replace(/,/g,"");
	frm.val( formatCommas(frm_price) );
}

// 계산 초기화
function reCal() {
	if(!confirm('다시 계산하시겠습니까?')) return;
	location.reload();
}

//계산식 보기
function showCal()	{
    if($(".tax_info").css("display") == "none"){
        $('.cal-formula-btn > span').text('산출계산식 닫기');
        $(".tax_info").show();
        $(".tax_info").slideDown(300);
        
    } else {
        $(this).addClass("show");
        $('.cal-formula-btn > span').text('산출계산식 보기');
        $(".tax_info").slideUp(300);
    }
}
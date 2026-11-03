// 숫자 계산기
var roundXL = function(n, digits) {

	console.log("n>> ",n);
	console.log(" digits1 >> ",digits);
	if(digits >= 0) {
		n = Math.floor(n/10) * 10; // 절삭관련 수식
		console.log(" 값은 >> ", n );

		return n
	}

	digits = Math.pow(10, digits);
	console.log(" digits2 >> ",digits);

	var t = Math.round(n * digits) / digits;
	console.log("t >> ",t);

	console.log("parseFloat>> ",  parseFloat(t.toFixed(0)));
	return parseFloat(t.toFixed(0));
}

//엔터값 분류
var executeCalc = function(obj, event, func) {

	if( event.keyCode=='13' || event.keyCode=='9') {
		if (func == "calcFindersFee") {
			if (obj.id == "txtPrice") {
				var price = obj.value.replace(/,/gi,"");
				if (price <= 600000000)
					$("#comboFFGoodType").val("1");
				else if (price > 600000000)
					$("#comboFFGoodType").val("2");
			}
			if ($("[name=comboFFGoodTypeCode]").val() == "3" && obj.id == "txtPrice") {
				$("#txtRentPrice").focus();
			}
		} else if (obj.id == "acquisitionTaxAmount") {
			var price = obj.value.replace(/,/gi,"");
			if (price <= 600000000)
				$("#houseType").val("1");
			else if (price > 600000000 && price <= 900000000)
				$("#houseType").val("2");
			else if (price > 900000000)
				$("#houseType").val("3");

			$("#area").focus();
		} else if(obj.id == "txtConAreaMt") {
			$("#txtConAreaPy").focus();
		} else if(obj.id == "txtConAreaPy") {
			$("#txtConAreaMt").focus();
		} else {
			eval(func + "()");
		}
		event.preventDefault();
		return false;
	}
};

/*** 우리집 재산세 ***/
// 재산세(주택분) 계산
function calcPropertyTax() {
	var marketRate = 0.6; // 공정시장가액비율(60%)
	var standardPrice = stripCommas( $("#txtStandardPrice").val() ); // 입력 기준시가
	var standardTaxBase = standardPrice * marketRate; // 과세표준
	var propertyTax = 0; // 주택 재산세

	if(standardTaxBase <= 60000000) { //6천이하
		propertyTax = standardTaxBase * 0.001; // 0.1%
	} else if(standardTaxBase <= 150000000) { // 1억5천이하
		propertyTax = 60000 + (standardTaxBase - 60000000) * 0.0015; // 60,000 원 + 60,000,000 원 초과금액의 0.15 %
	} else if(standardTaxBase <= 300000000) { // 3억이하
		propertyTax = 195000 + (standardTaxBase - 150000000) * 0.0025; // 195,000 원 + 150,000,000 원 초과금액의 0.25 %
	} else { // 3억초과
		propertyTax = 570000 + (standardTaxBase - 300000000) * 0.004; // 570,000 원 + 300,000,000 원 초과금액의 0.4 %
	}

	var localEducationTax = propertyTax * 0.2; // 지방교육세 = 재산세액 X 20 %
	var taxOfCityPlanning = standardTaxBase * 0.0014; // 재산세 도시지역분 = 재산세 과세표준 X 0.14 %

	propertyTax = roundXL(propertyTax, 0);
	standardTaxBase = roundXL(standardTaxBase, 0);
	localEducationTax = roundXL(localEducationTax, 0);
	taxOfCityPlanning = roundXL(taxOfCityPlanning, 0);
	var total = propertyTax + localEducationTax + taxOfCityPlanning;
	total = roundXL(total, 0);

	var princ = $('#txtStandardPrice').val();
	$("#principal").html(formatCommas(princ) + " 원"); // 원금
	$("#resultStandardTaxBase").html(formatCommas(standardTaxBase) + " 원"); // 과세표준액
	$("#resultPTTax").html(formatCommas(propertyTax) + " 원"); // 재산세
	$("#resultPTEdu").html(formatCommas(localEducationTax)  + " 원"); // 지방교육세
	$("#resultPTCity").html(formatCommas(taxOfCityPlanning) + " 원"); // 도시계획세
	$("#resultPTTotal").html("<span>" + formatCommas(total) + "</span>" + " 원"); // 합계
	
	$('.white-box2').hide();
	$('.btn-group').hide();
	$('.result-cont').show();
}

//재산세 (토지분)
function calcPropertyTaxLand(cate, num) {

	var standardPrice = stripCommas( $("#txtStandardPriceLand").val() ); // 입력 기준시가
	var category = cate;
	var cateNum = String(num);
	var citytax = 0; //도시세
	var localEduTax = 0; //지방 교육세
	var propertyTax = 0; // 재산세 본세
	var taxation  = standardPrice * 0.7; //과세표준 값 구하기

	// 종합합산, 종합합산 과세대상
	if(category == 'landDetail') {
		
		if(cateNum == "1") { //종합합산 과세대상
			//2억보다 작음
			if(taxation < 200000000) {
				propertyTax = taxation * 0.002; //0.2% 세율
				citytax = taxation * 0.0014; //0.14% 도시 지역분
				localEduTax = propertyTax * 0.2; //20% 지방교육세
			} else if(taxation >= 200000000 && taxation < 1000000000) {
				propertyTax = 400000 + (taxation-200000000)*(3/1000); //제산세 본새엑 2억 초과 10억 이하
				citytax = taxation * 0.0014; //0.14% 도시 지역분
				localEduTax = propertyTax * 0.2; //20% 지방교육세
			} else {
				propertyTax = 2800000 + (taxation-1000000000)*(4/1000);  //제산세 본새엑 10억 초과
				citytax = taxation * 0.0014; //0.14% 도시 지역분
				localEduTax = propertyTax * 0.2; //20% 지방교육세
			}
			
		} else if(cateNum == "2") { //별도합산 과세대상
			if(taxation < 50000000) {  //5천
				propertyTax = taxation * 0.002; // 0.2% 세율
				citytax = taxation * 0.0014; //0.14% 도시 지역분
				localEduTax = propertyTax * 0.2; //20% 지방교육세
	
			} else if(taxation >= 50000000 && taxation < 100000000) { //5천 ~ 1억
				propertyTax = 100000 + (taxation-50000000)*(3/1000); //세율 0.3% 0.003%
				citytax = taxation * 0.0014; //0.14% 도시 지역분
				localEduTax = propertyTax * 0.2; //20% 지방교육세
	
			} else {
				propertyTax = 250000 + (taxation-100000000)*(5/1000);
				citytax = taxation * 0.0014; //0.14% 도시 지역분
				localEduTax = propertyTax * 0.2; //20% 지방교육세
			}
		}
		
		$('.white-box2').hide();
		$('.btn-group').hide();
		$('.result-cont').show();
		
	} else {
		//분리 과세대상(landDetailEtc, 1): 전답과수원
		//분리 과세대상(landDetailEtc, 2): 골프장 및  오락장용 토지
		//분리 과세대상(landDetailEtc, 3): 그 밖의 토지
		
		if(category == 'landDetailEtc' && cateNum == "1") {
			/*console.log(" hello >>: 전답과수원 ");*/
			propertyTax = taxation * (0.7/1000);
			citytax = taxation * 0.0014; //0.14% 도시 지역분
			localEduTax = propertyTax * 0.2; //20% 지방교육세

		} else if(category == 'landDetailEtc' && cateNum == '2') {
			/*console.log(" hello 골프장");*/
			propertyTax = taxation * (4/100);//4%
			citytax = taxation * 0.0014; //0.14% 도시 지역분
			localEduTax = propertyTax * 0.2; //20% 지방교육세
		} else {
			/*console.log("hello >>:그밖의 토지 ");*/
			propertyTax = taxation * (2/1000);
			citytax = taxation * 0.0014; //0.14% 도시 지역분
			localEduTax = propertyTax * 0.2; //20% 지방교육세
		}
		
		$('.tab-cont2').hide();
		$('.btn-group').hide();
		$('.result-cont').show();
	}

	propertyTax = roundXL(propertyTax, 0);
	citytax = roundXL(citytax, 0);
	localEduTax = roundXL(localEduTax, 0);
	total = propertyTax + localEduTax + citytax;
	total = roundXL(total, 0);

	var princ = $('#txtStandardPriceLand').val();
	$("#principal").html(formatCommas(princ) + " 원"); // 시가표준액
	$("#resultPTTaxLand").html(formatCommas(propertyTax) + " 원"); //  재산세
	$("#resultPTCity").html(formatCommas(citytax) + " 원"); //  재산세
	$("#resultPTEdu").html(formatCommas(localEduTax) + " 원"); //  재산세
	$("#resultPTTotal").html("<span>" + formatCommas(total) + "</span>" + " 원"); // 합계
}
/*** // 우리집 재산세 ***/

/*** 우리집 취득세 ***/

// 주택(부속토지 포함) - 일반매매 및 신규분양(1세대 4주택미만)
function calAcqu(value) {
	
	var standardPrice = stripCommas( $("#txtStandardPrice").val() ); // 입력 기준시가
	var localEducationTax = 0;
	var propertyTax = 0; // 주택 재산세
	var resultPTTotal = 0;
	var ruralTax = 0;
	var category = value;//분기처리 값

	//취득세 구하기 세금 분기처리
	if(standardPrice <= 600000000) {
		propertyTax = standardPrice * 0.01 //1%
	} else if( standardPrice > 600000000 && standardPrice <= 900000000) {
		propertyTax = standardPrice * Math.round(((standardPrice * 2/300000000)-3)*100)/10000; //취득가액 x 2÷3 - 3%
	} else {
		propertyTax = standardPrice * 0.03 //3%
	}

	//교육세 구하기
	localEducationTax = propertyTax  * 0.1; // 세금에 10%

	//총납부 취득세액 구하기
	propertyTax = roundXL(propertyTax, 0);
	localEducationTax = roundXL(localEducationTax, 0);
	resultPTTotal = propertyTax + localEducationTax;

	// 85이상 농어촌세 추가
	if(category == 'Y'){
		ruralTax = standardPrice  * 0.002; //0.2% 농어촌세
		ruralTax = roundXL(ruralTax, 0);
		resultPTTotal =  resultPTTotal + ruralTax;
		$("#ruralTax").html(  formatCommas(ruralTax) +'</strong>'+ " 원"); // 지방교육세
	}

	resultPTTotal = roundXL(resultPTTotal, 0);
	var princ = $('#txtStandardPrice').val();
	$("#principal").html(formatCommas(princ) + " 원"); // 원금
	$("#resultPTTax").html(formatCommas(propertyTax) + " 원"); // 재산세
	$("#resultPTEdu").html(formatCommas(localEducationTax) + " 원"); // 지방교육세
	$("#resultPTTotal").html("<span>" + formatCommas(resultPTTotal)+ "</span>" + " 원"); // 도시계획세
	
	$('.tab-cont2').hide();
	$('.btn-group').hide();
	$('.result-cont').show();
}

//주택(부속토지 포함) - 일반매매 및 신규분양(1세대 4주택 이상)
function calAcqu2(value){
	var standardPrice = stripCommas( $("#txtStandardPrice").val() ); // 입력 기준시가
	var localEducationTax = 0;
	var propertyTax = 0; // 주택 재산세
	var resultPTTotal = 0;
	var ruralTax = 0;
	//분기처리 값
	var category = value;

	propertyTax = standardPrice * 0.04;

	//교육세 구하기
	localEducationTax = propertyTax  * 0.1; // 세금에 10%

	//총납부 취득세액 구하기
	propertyTax = roundXL(propertyTax, 0);
	localEducationTax = roundXL(localEducationTax, 0);
	resultPTTotal = propertyTax + localEducationTax;

	//85이상 농어촌세 추가
	if(category == 'Y'){
		ruralTax = standardPrice  * 0.002; //0.2% 농어촌세
		ruralTax = roundXL(ruralTax, 0);
		resultPTTotal =  resultPTTotal + ruralTax;
		$("#ruralTax").html(formatCommas(ruralTax) + " 원"); // 농어촌세 추가
	}

	resultPTTotal = roundXL(resultPTTotal, 0);
	var princ = $('#txtStandardPrice').val();
	$("#principal").html(formatCommas(princ) + " 원"); // 원금
	$("#resultPTTax").html(formatCommas(propertyTax) + " 원"); // 재산세
	$("#resultPTEdu").html(formatCommas(localEducationTax) + " 원"); // 지방교육세
	$("#resultPTTotal").html("<span>" + formatCommas(resultPTTotal) + "</span>" + " 원"); // 도시계획세
	
	$('.tab-cont2').hide();
	$('.btn-group').hide();
	$('.result-cont').show();
}

// 증여세
function giftTax(value){
	var standardPrice = stripCommas( $("#txtStandardPrice").val() ); // 입력 기준시가
	var localEducationTax = 0;
	var propertyTax = 0; // 주택 재산세
	var resultPTTotal = 0;
	var ruralTax = 0;
	var category = value; //분기처리 값

	propertyTax = standardPrice  * 0.035; // 세금 3.5%
	localEducationTax = standardPrice  * 0.003; //교육세 구하기 원금 0.3%


	propertyTax = roundXL(propertyTax, 0);
	localEducationTax = roundXL(localEducationTax, 0);
	resultPTTotal = propertyTax + localEducationTax;//총납부 취득세액 구하기

	//85mm이상 농어촌세 추가
	if(category == 'Y'){
		ruralTax = standardPrice * 0.002; //농어촌세 원금 0.2%
		ruralTax = roundXL(ruralTax, 0);
		resultPTTotal =  resultPTTotal + ruralTax;
		resultPTTotal = roundXL(resultPTTotal, 0);
		$("#ruralTax").html(  formatCommas(ruralTax) +'</strong>'+ " 원"); // 지방교육세
	}

	var princ = $('#txtStandardPrice').val();
	$("#principal").html(formatCommas(princ) + " 원"); // 원금
	$("#resultPTTax").html(formatCommas(propertyTax) + " 원"); // 재산세
	$("#resultPTEdu").html(formatCommas(localEducationTax) + " 원"); // 지방교육세
	$("#resultPTTotal").html("<span>" + formatCommas(resultPTTotal) + "</span>" + " 원"); // 도시계획세
	
	$('.tab-cont2').hide();
	$('.btn-group').hide();
	$('.result-cont').show();
}

// 상속세 - 일반과세 
function Inher(value){
	var standardPrice = stripCommas( $("#txtStandardPrice").val() ); // 입력 기준시가
	var localEducationTax = 0;
	var propertyTax = 0; // 주택 재산세
	var resultPTTotal = 0;
	var ruralTax = 0;
	//분기처리 값
	var category = value;

	//세금
	propertyTax = standardPrice  * 0.028; // 2.8%

	//교육세 구하기
	localEducationTax = standardPrice  * 0.0016; //원금 0.16%

	propertyTax = roundXL(propertyTax, 0);
	localEducationTax = roundXL(localEducationTax, 0);
	resultPTTotal = propertyTax + localEducationTax;


	//85mm이상 농어촌세 추가
	if(category == 'Y'){
		ruralTax = standardPrice * 0.002; //농어촌세 원금 0.2%
		ruralTax = roundXL(ruralTax, 0);
		resultPTTotal =  resultPTTotal + ruralTax;
		$("#ruralTax").html(  formatCommas(ruralTax) + " 원"); // 지방교육세
	}

	//총납부 취득세액 구하기
	resultPTTotal = roundXL(resultPTTotal, 0);

	var princ = $('#txtStandardPrice').val();
	$("#principal").html(formatCommas(princ) + " 원"); // 원금
	$("#resultPTTax").html(formatCommas(propertyTax) + " 원"); // 재산세
	$("#resultPTEdu").html(formatCommas(localEducationTax) + " 원"); // 지방교육세
	$("#resultPTTotal").html("<span>" +  formatCommas(resultPTTotal) + "</span>" + " 원"); // 도시계획세
	
	$('.tab-cont2').hide();
	$('.btn-group').hide();
	$('.result-cont').show();
}

// 상속세 - 1가구1주택 
function InherOneHouse(){
	
	var standardPrice = stripCommas( $("#txtStandardPrice").val() ); // 입력 기준시가
	var localEducationTax = 0;
	var propertyTax = 0; // 주택 재산세
	var resultPTTotal = 0;
	var ruralTax = 0;

	//세금
	propertyTax = standardPrice  * 0.008; // 0.8%

	//교육세 구하기
	localEducationTax = standardPrice  * 0.0016; //원금 0.16%

	propertyTax = roundXL(propertyTax, 0);
	localEducationTax = roundXL(localEducationTax, 0);
	resultPTTotal = propertyTax + localEducationTax;


	//총납부 취득세액 구하기
	resultPTTotal = roundXL(resultPTTotal, 0);

	var princ = $('#txtStandardPrice').val();
	$("#principal").html(formatCommas(princ) + " 원"); // 원금
	$("#resultPTTax").html(formatCommas(propertyTax) + " 원"); // 재산세
	$("#resultPTEdu").html(formatCommas(localEducationTax) + " 원"); // 지방교육세
	$("#resultPTTotal").html("<span>" + formatCommas(resultPTTotal) + "</span>" + " 원"); // 도시계획세
	
	$('.tab-cont2').hide();
	$('.btn-group').hide();
	$('.result-cont').show();
}

//오피스 취득세
function offiAcq(category){
	var standardPrice = stripCommas( $("#txtStandardPrice").val() ); // 입력 기준시가
	var propertyTax = 0; // 주택 재산세
	var localEducationTax = 0; //지방 교육세
	var ruralTax = 0; //농어촌 특별세
	var resultPTTotal = 0; //총납부 취득세액
	
	if(category == "1") {
		propertyTax = standardPrice  * 0.04; //  취득세 본세 4%
		localEducationTax = standardPrice  * 0.004; //지방 교육세 구하기 원금 0.4%
		
	} else if(category == "2") {
		propertyTax = standardPrice  * 0.035; //  취득세 본세 3.5%
		localEducationTax = standardPrice  * 0.003; //지방 교육세 구하기 원금 0.3%
		
	} else if(category == "3") {
		propertyTax = standardPrice  * 0.028; //  취득세 본세 2.8%
		localEducationTax = standardPrice  * 0.0016; //지방 교육세 구하기 원금 0.16%
	}
	ruralTax = standardPrice * 0.002; // 농어촌세 원금 0.2%
	
	propertyTax = roundXL(propertyTax, 0);
	localEducationTax = roundXL(localEducationTax, 0);
	ruralTax = roundXL(ruralTax, 0);
	resultPTTotal = propertyTax + ruralTax + localEducationTax //총납부 취득세액 구하기
	resultPTTotal = roundXL(resultPTTotal, 0);

	var princ = $('#txtStandardPrice').val();
	$("#principal").html(formatCommas(princ) + " 원"); // 원금
	$("#resultPTTax").html(formatCommas(propertyTax) + " 원"); // 재산세
	$("#resultPTEdu").html(formatCommas(localEducationTax) + " 원"); // 지방교육세
	$("#ruralTax").html(formatCommas(ruralTax) + " 원"); // 지방교육세
	$("#resultPTTotal").html("<span>" + formatCommas(resultPTTotal) + "</span>" + " 원");
	
	$('.tab-cont2').hide();
	$('.btn-group').hide();
	$('.result-cont').show();
}

/*** // 우리집 취득세 ***/








/*
//2_3_2 재산세 건축물 계산
function calcPropertyTaxStructure() {
	var standardPrice = stripCommas( $("#txtStandardPriceStructure").val() ); // 입력 기준시가
	var propertyTax = 0; // 건축물 재산세
	if(structureDetail == "1"){
		propertyTax = standardPrice*(40/1000);
	}else{
		propertyTax = standardPrice*(2.5/1000);
	}

	$('#goCal').addClass('tax_result');
	var princ = $('#txtStandardPriceStructure').val();
	console.log("princ ", princ);
	$("#principal").html( formatCommas(princ)+ " 원"); // 재산세
	$("#resultPTTaxStructure").html( formatCommas(propertyTax)+ " 원"); // 재산세
	$("#resultPTTotalStructure").html('<span  class="redtext"><strong>' + formatCommas(propertyTax)+'</strong></span>'  + " 원"); // 합계
}

*/

	var lines = new Tmap.Layer.Vector('Tmap Vector Layer');
	var startFlag = false;
	var endFlag = false;
	
	// 초기화
	function resetRoute(){
		jQuery("#ipStart").val("출발지를 선택해주세요");
		jQuery("#ipEnd").val("도착지를 선택해주세요");
		startFlag = false;
		endFlag = false;
		jQuery("#mainInfo").show();
		jQuery("#roadSearchResult").css("display", "none");
	}
	
	// 경로검색 (출발지, 도착지)
	var startEndStatus;
	function roadSearchStartEnd(tabStat, startEnd){
		jQuery("#mainInfo").hide();
		searchStat = (tabStat != 1) ? 0 : 1;
		startEndStatus = startEnd;
		
		//검색일때만 페이징 초기화
		if(searchStat == 0){
			pageOfRoute = 1;
			pageOfBus = 1;
			pageOfSubway = 1;
			pageOfPOI = 1;
		}
		
		var searchKeyword = '';
		if(startEnd){
			searchKeyword = jQuery('#ipStart').val().toUpperCase();
			jQuery("#beforeStartBtn").hide();
			jQuery("#afterStartBtn").show();
		}else{
			searchKeyword = jQuery('#ipEnd').val().toUpperCase();
			jQuery("#beforeEndBtn").hide();
			jQuery("#afterEndBtn").show();
		}
		var url = "/gbis2014/schBusAPI.action";
		var data = 'cmd=searchAllJson';
		data += '&searchKeyword='+searchKeyword;
		data += '&pageOfRoute='+pageOfRoute;
		data += '&pageOfBus='+pageOfBus;
		data += '&pageOfSubway='+pageOfSubway;
		data += '&pageOfPOI='+pageOfPOI;

		$.ajax({
			type: "post",
			contentType: "application/x-www-form-urlencoded;charset=UTF-8",
			dataType: "json",
			url: url,
			data: data,
			success:function(data){
				
				// poi, subwayStation을 항상 초기화
				data.result.poi = {
					count: 0,
					pageOfPOI: String(pageOfPOI),
					list: []
				};
				data.result.subwayStation = {
					count: 0,
					pageOfSubway: String(pageOfSubway),
					list: []
				};

				// poi API 호출 후 채워 넣기
				fetch('https://apis.openapi.sk.com/tmap/pois?version=1&searchType=all&page=1&count=10&resCoordType=EPSG3857&multiPoint=N&searchtypCd=A&reqCoordType=EPSG3857&poiGroupYn=N&searchKeyword=' + searchKeyword, {
					method: 'GET',
					headers: {
					'Content-Type': 'application/json',
					'appKey': '01ab749a-7332-4a8d-93ee-dc823cbe3de1'
					}
				})
				.then(response => response.json())
				.then(searchMap => {
					const tempList = (searchMap.searchPoiInfo?.pois?.poi) || [];
					const poiList = [];
					const subwayStationList = [];

					tempList.forEach((item, idx) => {
					const upperAddrName = item.upperAddrName || "";
					const middleAddrName = item.middleAddrName || "";
					const lowerAddrName = item.lowerAddrName || "";
					const detailAddrName = item.detailAddrName || "";
					const firstNo = item.firstNo || "";
					const secondNo = item.secondNo || "";

					const addr = secondNo
						? `${upperAddrName} ${middleAddrName} ${lowerAddrName} ${detailAddrName} ${firstNo}-${secondNo}`
						: firstNo
						? `${upperAddrName} ${middleAddrName} ${lowerAddrName} ${detailAddrName} ${firstNo}`
						: `${upperAddrName} ${middleAddrName} ${lowerAddrName} ${detailAddrName}`;

					const upperBizName = item.upperBizName || "";
					const middleBizName = item.middleBizName || "";
					const lowerBizName = item.lowerBizName || "";

					if (["서울","경기","인천"].includes(upperAddrName)) {
						if (upperBizName === "교통편의" && middleBizName === "교통시설" && lowerBizName === "지하철역") {
						subwayStationList.push({
							lon: item.noorLon || "",
							lat: item.noorLat || "",
							poiNm: item.name || "",
							poiId: item.id || "",
							poiTelNo: item.telNo || "",
							poiBizName: item.bizName || "",
							poiUpperBizName: upperBizName,
							poiMiddleBizName: middleBizName,
							poiAddrName: addr,
							poiRpFlag: item.rpFlag || "",
							subwaySeq: String(idx+1)
						});
						} else {
						poiList.push({
							lon: item.noorLon || "",
							lat: item.noorLat || "",
							poiNm: item.name || "",
							poiId: item.id || "",
							poiTelNo: item.telNo || "",
							poiBizName: item.bizName || "",
							poiUpperBizName: upperBizName,
							poiMiddleBizName: middleBizName,
							poiAddrName: addr,
							poiRpFlag: item.rpFlag || "",
							poiSeq: String(idx+1)
						});
						}
					}
					});

					// 초기화된 data.result에 채워 넣기
					data.result.poi = {
					count: poiList.length,
					pageOfPOI: String(pageOfPOI),
					list: poiList
					};
					data.result.subwayStation = {
					count: subwayStationList.length,
					pageOfSubway: String(pageOfSubway),
					list: subwayStationList
					};

					// 기존 로직 실행
					searchTotalSuccess(data);
				})
				.catch(err => {
					console.error("POI API error:", err);
					// 실패해도 초기화된 구조는 유지되므로 안전
					searchTotalSuccess(data);
				});
			} ,
			error: ajaxErrorRoute,
			beforeSend: ajaxBeforeSend,
		    complete: ajaxComplete
		});
		
		jQuery("#mainInfo").hide();
		jQuery("#roadbusSearchResult").css("display", 'none');
		jQuery("#roadSearchResult").css("display", "");
		jQuery("#search_result1").html('<div></div>');
		resetSearch();
	}
	
// 마커 마우스 클릭시 이벤트
var popupFlag = false;
var routeName;
var startLon, startLat, endLon, endLat;
var startLocName, endLocName;
// 리스트 클릭시 이벤트
function selectRoute(val){

	if(val == 'recommand'){
		jQuery(".busRecommand").addClass("active");
		
		jQuery(".goBusChosen").text('');
		jQuery(".busTransferChosen").text('');
		jQuery(".busRecommandChosen").text('선택됨');
		
		jQuery(".busRecommand").siblings("a").removeClass("active");
		jQuery(".listRoute_recommand").show();
		jQuery(".listRoute_recommand").siblings("ul").hide();
	}else if(val == 'bus'){
		jQuery(".goBus").addClass("active");
		
		jQuery(".busTransferChosen").text('');
		jQuery(".busRecommandChosen").text('');
		jQuery(".goBusChosen").text('선택됨');
		
		jQuery(".goBus").siblings("a").removeClass("active");
		jQuery(".listRoute_bus").show();
		jQuery(".listRoute_bus").siblings("ul").hide();
	}else{
		jQuery(".busTransfer").addClass("active");

		jQuery(".busRecommandChosen").text('');
		jQuery(".goBusChosen").text('');
		jQuery(".busTransferChosen").text('선택됨');
		
		jQuery(".busTransfer").siblings("a").removeClass("active");
		jQuery(".listRoute_transfer").show();
		jQuery(".listRoute_transfer").siblings("ul").hide();
	}
}

// 대중교통 길찾기 버튼 클릭시 ajax
 var routeSeq = 0;

 function searchRoute( ){
	 
	//열려있는 툴팁 있을 시 툴팁 닫기
	if(crPopup) tooltipClose();
		
	 if(!startFlag || !endFlag){
		 alert("출발지와 도착지를 선택해주세요.");
		 return;
	 }
	 
	 var url = 'https://gg-bis-open.tmobiapi.com/pubtrans/routeplan?';
	 var coordResultSt=[];
	 coordResultSt = epsg2Wgs(startLon,startLat);
	 var startLatWgs84 = coordResultSt[0];
	 var startLonWgs84 = coordResultSt[1];
	 var coordResultEd=[];
	 coordResultEd = epsg2Wgs(endLon,endLat);
	 var endLatWgs84 = coordResultEd[0];
	 var endLonWgs84 = coordResultEd[1]; 

	 url = url+'origin=출발지,'+startLonWgs84+','+startLatWgs84+'&destination=도착지,'+endLonWgs84+','+endLatWgs84;
	 
	 $.ajax({
		type: "get",
		dataType: "json",
		url: url,
		contentType: "application/x-www-form-urlencoded;charset=UTF-8",
		dataType: "json",
		beforeSend: function(xhr){
			ajaxBeforeSend();
			xhr.setRequestHeader("x-api-key","TfMsSUCJmdaKSnverUXDZ91U3EGNcLZp6T15JmhZ");
			xhr.setRequestHeader("Content-type","application/json");
		},
		success: searchRouteSuccess,
		error: ajaxErrorRoute,
	    complete: ajaxComplete
	});

	 jQuery("#mainInfo").hide();
	 selectRoute('recommand');
	 jQuery("#roadSearchResult").css('display' , 'none');
	 jQuery("#roadbusSearchResult").css('display', '');
	 jQuery("#list_cmn_recommand").show();
	 jQuery("#list_cmn_bus").hide();
	 jQuery("#list_cmn_transfer").hide();
}
 
 // ajax 완료 시 결과
 var busTotal, transferTotal; 
 var routeData;
 var resetSearchFlag = false;
 function searchRouteSuccess(data){
	 //jQuery("#mainInfo").hide();
	 // 초기화 구문 추가
	 routeData = new Array();
	 jQuery(".listRoute_recommand").text('');
	 jQuery(".listRoute_bus").text('');
	 jQuery(".listRoute_transfer").text('');
	 busTotal = 0;
	 transferTotal = 0;
	 routeSeq = 0;
	 resetSearchFlag = true;	 
	 // 경로검색 시작 차례대로
	 var routes = data.routes;
	 
	 var routeData_c = ['bus' , 'transfer'];
	 for(var i=0; i<routeData_c.length; i++){
		 routeResult(routes, routeData_c[i]); // 직행, 환승 리스트 실행		 		 
	 }
	 //추천리스트 실행
	 recommandList();
 }
 
// 버스, 환승 경로 결과 반영
 var busTransferMap = new HashMap();
 var childMap = new HashMap();
 var walkMap = new HashMap();
 var recomWalkMap = new HashMap();
 function routeResult(routes, type) {

	 var routesFiltered;
	 if(type == 'bus'){
		 routesFiltered = routes.filter(item => item["transferCount"] == 0);
	 }else{
		 routesFiltered = routes.filter(item => item["transferCount"] > 0);
	 }
	 
	 for(var i=0; i<routesFiltered.length; i++){
		 routeData[routeSeq] = routesFiltered[i]; // 경로데이터를 임시 array 에 저장
		 routeSeq++;
	 }
 
	// 정렬임시 array 에 시간과 seq키를 저장
	 var totalTimeArr = new Array();
	 for(var i=0; i<routeData.length; i++){
		 var routeDataSample = routeData[i].duration;
		 totalTimeArr[i] = [routeDataSample, i];  
	 }

	 
	// 시간을 기준으로 정렬	 
	 totalTimeArr.sort(function(a, b){   
		 return a[0] - b[0];
	 });
	 // 마지막 transfer가 실행할때 리스트에 뿌리기
	 if(type == 'transfer'){
		 var seqNum = 1;
		 var startLocName_c = (startLocName.length > 11) ? startLocName.substring(0,10)+'...' : startLocName;  // 글자수 제한
		 var endLocName_c =(endLocName.length > 11) ? endLocName.substring(0,10)+'...' : endLocName; // 글자수 제한
		 for(var a = 0; a < totalTimeArr.length; a++){
			 var sortTime = totalTimeArr[a][0]; // 시간
			 var sortSeq = totalTimeArr[a][1]; // SEQ 키
			 for(var b = 0; b<routeData.length; b++){
				 var oriTime = routeData[b].duration;  // 원본리스트에서 차례로 비교
				 
				 if(sortTime == oriTime){ // 정렬된 시간과 
					 if(sortSeq == b){  // 키값이 같다면
						    var path	= routeData[b].steps;
							var distance = routeData[b].distance; //거리를 숫자로
							var distanceMiterType = 'm';
							if(distance >= 1000){ // 거리가 1000m가 넘으면 km로 변환 ( 소수점 2자리까지 반올림)
								distance = (routeData[b].distance /1000).toFixed(2);
								distanceMiterType = 'km';
							}
							var payment	= routeData[b].fare;
							var time	= (routeData[b].duration/60).toFixed(0);
							var pathChildren = path; //////////////////// steps = pathChildren
							
							var type_c ;  // 노드 이름 // 직행 환승에 따라서  bus 또는 transfer 넣어주기  노드이름 정해주자..
							if(routeData[b].transferCount == 0){
								type_c = 'bus';
							}else{
								type_c = 'transfer';
							}
								
							var child_id = 'child_'+type_c+'_'+seqNum;
							childMap.put(child_id, pathChildren);
							
							var laneId = 'lane_pos_'+type_c+'_'+seqNum;
							var LanePath = new Array;								//경로 좌표를 hashMap에 저장 
							for(var i=0; i<routeData[b].steps.length; i++){
								var pathIndex = i;
								var transitMode = routeData[b].steps[i].transitMode;
								var polyLines = routeData[b].steps[i].polylines;
								LanePath.push([pathIndex, transitMode, polyLines]); 
							}
							
							busTransferMap.put(laneId,LanePath);
							var walkTime	= 0;
							var busCount	= 0;
							var subwayCount	= 0;
							var html = '';
							var list_station  = '';
							var detailInfo = '';
							var detailCnt = 0;
							var walkSeq = new Array();

							for(var i = 0; i<pathChildren.length; i++){
								var pathChild = pathChildren[i];
								var nodeNm = pathChild.transitMode;
									if(nodeNm=='WALKING'){
										walkSeq.push(i);
										walkTime = walkTime + (pathChild.duration/60).toFixed(0); 
										var moveTime = (pathChild.duration/60).toFixed(0);
										var moveDistance = pathChild.distance;
										var moveMiterType = 'm';
										if(moveDistance >= 1000){ // 거리가 1000m가 넘으면 km로 변환 ( 소수점 2자리까지 반올림)
											moveDistance = (pathChild.distance/1000).toFixed(2);
											moveMiterType = 'km';
										}
										var startName = pathChild.startStationName;
										var endName =''; 
										if(i<pathChildren.length-1){
											endName = pathChildren[i+1].startStationName;
										}
										
										var endName_c = (endName.length > 13) ? endName.substring(0,12)+'...' : endName;
										
										if(i == 0){
											detailInfo += '<li class="step">';
											detailInfo += '<div class="pin"><img src="/gbis2014/images/ico/common/start.png" alt="출발" width="26" height="30" /></div>';
											detailInfo += '<div class="desc">';
											detailInfo += '<a href=\'javascript:detailCenter("bus", '+detailCnt+');\'>';
											detailInfo += '<p class="tit"><em>'+startLocName_c+'</em> 출발</p>';
											detailInfo += '</a>';
											detailInfo += '</div></li>';
											detailCnt++;
										}

										detailInfo += '<li class="step">';
										detailInfo += '<div class="pin"><img src="/gbis2014/images/ico/common/pin_walk_on.png" alt="" width="25" height="25" /></div>';
										detailInfo += '<div class="desc">';
										detailInfo += '<a href=\'javascript:detailCenter("bus", '+detailCnt+');\'>';
										var startPathChild = new Array() ;
										var moveType='';
										if( i < (pathChildren.length-1)){
											startPathChild = pathChildren[i+1];
											moveType = startPathChild.transitMode;
										}
										var stRTID ;
										if(moveType=='BUS'){
											stRTID = startPathChild.stations[0].displayId;
											//4자리 정류소번호 처리
											if(stRTID.length == 4){
												stRTID = "0"+stRTID;
											}
											detailInfo += '<p class="tit"><em>도보로 '+endName_c+'('+stRTID+') 정류소</em>까지 이동</em></p>';
										}else if(moveType=='SUBWAY'){
											detailInfo += '<p class="tit"><em>도보로 '+endName_c+'역</em>까지 이동</em></p>';	
										}
										
										detailInfo += '<p class="txt"><span class="time">약 '+moveTime+'분</span><span class="distance">'+moveDistance+moveMiterType+'</span></p>';
										detailInfo += '</a></div></li>';
										detailCnt++;
										
										if(i == parseInt(pathChildren.length)-1){
											detailInfo += '<li class="step">';
											detailInfo += '<div class="pin"><img src="/gbis2014/images/ico/common/pin_end.png" alt="도착" width="26" height="30" /></div>';
											detailInfo += '<div class="desc">';
											detailInfo += '<a href=\'javascript:detailCenter("bus", '+detailCnt+');\'>';
											detailInfo += '<p class="tit"><em>'+endLocName_c+'</em> 도착</p>';
											detailInfo += '</a>';
											detailInfo += '</div></li>';
											detailCnt++;
										}
								}

									
								if(nodeNm=='SUBWAY' || nodeNm=='BUS'){
									var moveType = nodeNm;
									
									if(moveType=='SUBWAY'){
										subwayCount	 = (pathChild.stations.length) - 1;
										var laneAlias = pathChild.subway.name;
										var expressYN = pathChild.subway.expressTypeName;
 										var subColor = '';
										var stName = pathChild.startStationName;
										var stName_c = (stName.length > 10) ? stName.substring(0,9)+'...' : stName;
										var enName = pathChild.endStationName;
										var moveTime = pathChild.endStationName;
										var moveDistance = pathChild.distance;
										var moveMiterType = 'm';
										if(moveDistance >= 1000){ // 거리가 1000m가 넘으면 km로 변환 ( 소수점 2자리까지 반올림)
											moveDistance = (pathChild.distance/1000).toFixed(2);
											moveMiterType = 'km';
										}
										
										if(laneAlias.indexOf('수인분당') != -1){
											subColor = 'sub000';
										}else if(laneAlias.indexOf('에버라인') != -1){  
											subColor = 'sub011';
										}else if(laneAlias.indexOf('인천1호선') != -1){   // 인천1호선 먼저 
											subColor = 'sub012';	
										}else if(laneAlias.indexOf('인천2호선') != -1){    // 인천2호선 먼저
											subColor = 'sub013';
										}else if(laneAlias.indexOf('경의중앙선') != -1){
											subColor = 'sub014';	
										}else if(laneAlias.indexOf('우이신설선') != -1){
											subColor = 'sub015';
										}else if(laneAlias.indexOf('김포골드라인') != -1){
											subColor = 'sub016';	
										}else if(laneAlias.indexOf('공항철도') != -1){
											subColor = 'sub020';
										}else if(laneAlias.indexOf('신분당선') != -1){
											subColor = 'sub022';	
										}else if(laneAlias.indexOf('경춘선') != -1){
											subColor = 'sub023';
										}else if(laneAlias.indexOf('의정부경전철') != -1){
											subColor = 'sub024';	
										}else if(laneAlias.indexOf('경강선') != -1){
											subColor = 'sub025';
										}else if(laneAlias.indexOf('서해선') != -1){
											subColor = 'sub026';
										}else if(laneAlias.indexOf('신림선') != -1){
											subColor = 'sub027';
										}else if(laneAlias.indexOf('동해선') != -1){
											subColor = 'sub028';
										}else if(laneAlias.indexOf('자기부상') != -1){
											subColor = 'sub029';
										}else if(laneAlias.indexOf('1호선') != -1){
											subColor = 'sub001';
										}else if(laneAlias.indexOf('2호선') != -1){
											subColor = 'sub002';
										}else if(laneAlias.indexOf('3호선') != -1){
											subColor = 'sub003';
										}else if(laneAlias.indexOf('4호선') != -1){
											subColor = 'sub004';
										}else if(laneAlias.indexOf('5호선') != -1){
											subColor = 'sub005';
										}else if(laneAlias.indexOf('6호선') != -1){
											subColor = 'sub006';
										}else if(laneAlias.indexOf('7호선') != -1){
											subColor = 'sub007';
										}else if(laneAlias.indexOf('8호선') != -1){
											subColor = 'sub008';
										}else if(laneAlias.indexOf('9호선') != -1){
											subColor = 'sub009';
										}else {
											subColor = 'sub100';   //default
										}



										
										
										//list_station += '<span><img src="/gbis2014/images/ico/subway/'+laneAlias+'.png" alt="'+laneAlias+'" /></span>';
										if (expressYN == "급행"){
											 expressYN = '<span class="express">급행</span>';
										}else{
											expressYN = "";
										} 
										list_station += '<span class="sub_icon '+subColor+'">'+laneAlias+'</span>'+expressYN;
										
										if(stName_c.indexOf("역")<1){
											list_station += '<span><em>'+stName_c+'역</em></span>';
										} else {
											list_station += '<span><em>'+stName_c+'</em></span>';
										}
										list_station += '<span class="arrow2"><img src="/gbis2014/images/ico/common/arrow_r.gif" alt="" /></span>';
										
										detailInfo += '<li class="step">';
										detailInfo += '<div class="pin"><img src="/gbis2014/images/ico/common/pin_subway_on.png" alt="" width="25" height="25" /></div>';
										detailInfo += '<div class="desc">';
										detailInfo += '<a href=\'javascript:detailCenter("bus", '+detailCnt+');\'>';
										if(stName_c.indexOf("역")<1){
											detailInfo += '<p class="tit"><span class="sub_icon '+subColor+'">'+laneAlias+'</span>'+expressYN+'&nbsp;<em>'+stName_c+'역</em> 승차 후 '+subwayCount+'개 역 이동</p>';
										} else {
											detailInfo += '<p class="tit"><span class="sub_icon '+subColor+'">'+laneAlias+'</span>'+expressYN+'&nbsp;<em>'+stName_c+'</em> 승차 후 '+subwayCount+'개 역 이동</p>';
										}
										if(enName.indexOf("역")<1){
											detailInfo += '<p class="tit"><span class="sub_icon '+subColor+'">'+laneAlias+'</span>&nbsp;<em>'+enName+'역</em>에서 하차</p>';
										} else {
											detailInfo += '<p class="tit"><span class="sub_icon '+subColor+'">'+laneAlias+'</span>&nbsp;<em>'+enName+'</em>에서 하차</p>';
										}
										
										detailInfo += '<p class="txt">약 '+moveTime+'분 '+moveDistance+moveMiterType+'</p>';
										detailInfo += '</a></div></li>';
										detailCnt++;
											
									}else if(moveType=='BUS'){
										busCount = busCount + (pathChild.stations.length - 1); 
										var laneAlias 	= pathChild.bus.typeName + pathChild.bus.name+'번';
										
										var stName = pathChild.startStationName;
										var stName_c = (stName.length > 10) ? stName.substring(0,9)+'...' : stName;
										var enName = pathChild.endStationName;
										var moveDistance = pathChild.distance;
										var moveMiterType = 'm';

										if(moveDistance >= 1000){ // 거리가 1000m가 넘으면 km로 변환 ( 소수점 2자리까지 반올림)
											moveDistance = (pathChild.distance/1000).toFixed(2);
											moveMiterType = 'km';
										}
										var moveTime = (pathChild.duration/60).toFixed(0);
										var stopCount = pathChild.stations.length - 1;
										//정류소번호
										var stRTID = pathChild.stations[0].displayId;
										//4자리 정류소번호 처리
										if(stRTID.length == 4){
											stRTID = "0"+stRTID;
										}
										stRTID = (stRTID != '') ? '(' + stRTID + ')' : '()';
										var edRTID = pathChild.stations[stopCount].displayId;
										//4자리 정류소번호 처리
										if(edRTID.length == 4){
											edRTID = "0"+edRTID;
										}
										edRTID = (edRTID != '') ? '(' + edRTID + ')' : '()';


										var alternatives = pathChild.bus.alternatives;
										if (alternatives && alternatives.length >= 1) {
											var alt_string ='';
											for(var j = 0; j<alternatives.length; j++){
												alt_string += '<p class="alternatives"> 대체버스 : '+alternatives[j].typeName + alternatives[j].name+'번</p>';
											}

											list_station += '<span><em class="num_red">'+laneAlias+'</em></span>';
											list_station += '<span>&nbsp;'+stName_c+'</span>';
											list_station += '<span class="arrow2"><img src="/gbis2014/images/ico/common/arrow_r.gif" alt="" /></span>';
											
											detailInfo += '<li class="step">';
											detailInfo += '<div class="pin"><img src="/gbis2014/images/ico/common/pin_bus_on.png" alt="" width="25" height="25" /></div>';
											detailInfo += '<div class="desc">';
											detailInfo += '<a href=\'javascript:detailCenter("bus", '+detailCnt+');\'>';
											detailInfo += '<p class="tit"><strong>'+laneAlias+'('+stName_c+stRTID+') 정류소</strong> 승차 후 '+stopCount+'개 정류소 이동, <strong>'+enName+edRTID+' 정류소</strong>에서 하차</p>';
											detailInfo += alt_string;

											detailInfo += '<p class="txt">약 '+moveTime+'분 '+moveDistance+moveMiterType+'</p>';
											detailInfo += '</a></div></li>';
											detailCnt++;	
										}else{
											list_station += '<span><em class="num_red">'+laneAlias+'</em></span>';
											list_station += '<span>&nbsp;'+stName_c+'</span>';
											list_station += '<span class="arrow2"><img src="/gbis2014/images/ico/common/arrow_r.gif" alt="" /></span>';
											
											detailInfo += '<li class="step">';
											detailInfo += '<div class="pin"><img src="/gbis2014/images/ico/common/pin_bus_on.png" alt="" width="25" height="25" /></div>';
											detailInfo += '<div class="desc">';
											detailInfo += '<a href=\'javascript:detailCenter("bus", '+detailCnt+');\'>';
											detailInfo += '<p class="tit"><strong>'+laneAlias+'('+stName_c+stRTID+') 정류소</strong> 승차 후 '+stopCount+'개 정류소 이동, <strong>'+enName+edRTID+' 정류소</strong>에서 하차</p>';
											
											detailInfo += '<p class="txt">약 '+moveTime+'분 '+moveDistance+moveMiterType+'</p>';
											detailInfo += '</a></div></li>';
											detailCnt++;
										}

										
									}
								}
							}

							list_station = list_station.substring(0, list_station.length-88);
							jQuery(".starting").text(startLocName_c);
							jQuery(".ending").text(endLocName_c);
							
							html += '<li>';
							html += '<a href=\'javascript:lineRoute("'+type_c+'","'+seqNum+'");\'>';
							html += '<div class="path_line">';
							html += list_station;
							html += '</div>';
							html += '<div class="path_infolst">';
							html += '<span class="time">소요시간 : 약 '+time+'분</span>';
							html += '<span class="pay">교통비 : 약 '+payment+'</span>';
							html += '<span class="distance">거리 : 약 '+distance+distanceMiterType+'</span>';
							html += '</div>';
							html += '<p class="path_more"></p>';
							html += '</a>';
							html += '<ol class="dtl_rute detailResult"  id="detailResult_'+type_c+'_'+seqNum+'" style="display:none;">';
							html += detailInfo;
							html += '</ol>';
							html += '</li>';
							
						    if(type_c == 'bus' || type_c == 'subway'){
								jQuery('.listRoute_bus').append(html);
								busTotal++;
							}else{
								jQuery('.listRoute_transfer').append(html);
								transferTotal++;
							}
						    
						    jQuery(".gobusRouteCnt").html("( " + busTotal + " )");
						    jQuery(".transferRouteCnt").html("( " + transferTotal + " )");
						    
							var id = 'lane_pos_'+type_c+'_'+seqNum;
							walkMap.put(id, walkSeq);
							seqNum++;
					 } // if문 끝
				} // if문 끝
			 } // for문 끝
		 } // time for문 끝
		 
		 if(busTotal == 0){
			 jQuery(".starting").text(startLocName_c);
			 jQuery(".ending").text(endLocName_c);
			 jQuery(".gobusRouteCnt").html("( 0 )");
			 var list = '';
			 list += '<li class=\'cannot_find\'>';
			 list += '검색 결과가 없습니다.';
			 list += '</li>';
			 jQuery('.listRoute_bus').append(list);
		 }
		 
		 if(transferTotal == 0){
			 jQuery(".starting").text(startLocName_c);
			 jQuery(".ending").text(endLocName_c);
			 jQuery(".transferRouteCnt").html("( 0 )");
			 var list = '';
			 list += '<li class=\'cannot_find\'>';
			 list += '검색 결과가 없습니다.';
			 list += '</li>';
			 jQuery('.listRoute_transfer').append(list);
		 }
	 } // subway if 문 끝
	 
	 searchListEvt();
	 
	//리스트 선택시 스크롤 이동
	$('#list_cmn_transfer .listRoute_transfer > li').click(function(){
		var thisIndex = $('#list_cmn_transfer .listRoute_transfer > li').index(this);
		var listScrollPoint = Number(thisIndex) * 95;
		jQuery("#list_cmn_transfer").animate({scrollTop:listScrollPoint}, 0);
	});
	
	//리스트 선택시 스크롤 이동
	$('#list_cmn_bus ul > li').click(function(){
		var thisIndex = $('#list_cmn_bus ul > li').index(this);
		var listScrollPoint = Number(thisIndex) * 95;
		jQuery("#list_cmn_bus").animate({scrollTop:listScrollPoint}, 0);
	});
}
 
 function searchListEvt(){
	// [백그라운드 음영] (통합,길찾기,실시간버스) 검색결과 List 마우스 오버 
 	$('.list_cmn .path_wrap li > a').hover(
 		function(){
 			$(this).addClass('over');
 	},
 		function() {
 			$(this).removeClass('over');
 	}).click(
 		function() {
 			$('.list_cmn .path_wrap li > a').removeClass('active');
 			$('.path_more').removeClass('active');
 			$('.dtl_rute').hide();			
 			$(this).addClass('active');
 			$(this).children('.path_more').addClass('active');			
 			$(this).next('ol').show();
 	});

 	$('.dtl_rute .step').hover(
 		function(){ $(this).addClass('over');
 	},
 		function(){ $(this).removeClass('over'); 
 	}).click(
 		function() {
 			$(this).toggleClass('active');	
 			$(this).siblings().removeClass('active');
 	});
	 
	// [탭 컨트롤] 추천, 직행, 환승 검색리스트 
 	var tabMenu = $('.search_rute_result .tab > a');
 	var resultList = $('.search_rute_result .list_cmn');
 	tabMenu.click(function(){
 		var onIndex = $(this).index();
 		resultList.hide().eq(onIndex).show();
 		tabMenu.removeClass('active');
 		$(this).addClass('active');
 	});
 }
 
 // 추천 리스트 생성
 var recommandMap = new HashMap();
 var recommandChildMap = new HashMap();
 function recommandList(){
	 
	 var totalTimeArr = new Array();
	 var startLocName_c = (startLocName.length > 11) ? startLocName.substring(0,10)+'...' : startLocName;  // 글자수 제한
	 var endLocName_c =(endLocName.length > 11) ? endLocName.substring(0,10)+'...' : endLocName; // 글자수 제한
	 var firstType = '';
	 var firstSeq = 0;
	 var searchFlag = false;
	 if(routeData.length > 0){
		 for(var i=0; i<routeData.length; i++){
			 totalTimeArr[i] = [routeData[i].duration , i];
		 }
		 totalTimeArr.sort(function(a, b){
			 return a[0] - b[0];
		 }); // 시간을 기준으로 정렬
		 
		 if(totalTimeArr.length > 2){  // totalTimeArr.length가 3이상일때만 max 3개로 짤라서 Arr을 
			 totalTimeArr = totalTimeArr.slice(0, 3);
		 }
		 var recom_seqNum = 1;
		 for(var a = 0; a < totalTimeArr.length; a++){
		 
			 /* 추천 3개 이하일 때 오류발생으로 인한 수정_장지원*/
			 /* if(a >= totalTimeArr.length) { //추천이 3개가 안될 때 추천개수까지만 반복 후 return
				 return;
			 } */
				 
			 var sortTime = totalTimeArr[a][0]; // 시간
			 var sortSeq = totalTimeArr[a][1]; // SEQ 키
			
			 jQuery(".recommandCnt").html("( "+ (a+1) + " )"); //추천 개수 입력
			 
			 for(var b = 0 ; b<routeData.length; b++){
				 
				 var oriTime = routeData[b].duration;  // 원본리스트에서 차례로 비교
				 if(sortTime == oriTime){ // 정렬된 시간과 
					 if(sortSeq == b){  // 키값이 같다면
						    var path	= routeData[b].steps;
							var distance = routeData[b].distance; //거리를 숫자로
							var distanceMiterType = 'm';
							if(distance >= 1000){ // 거리가 1000m가 넘으면 km로 변환 ( 소수점 2자리까지 반올림)
								distance = (routeData[b].distance /1000).toFixed(2);
								distanceMiterType = 'km';
							}
							var payment	= routeData[b].fare;
							var time	= (routeData[b].duration/60).toFixed(0);
							var pathChildren = path; //////////////////// steps = pathChildren
						
							var type ;  // 노드 이름 // 직행 환승에 따라서  bus 또는 transfer 넣어주기  노드이름 정해주자..
							if(routeData[b].transferCount == 0){
								type = 'bus';
							}else{
								type = 'transfer';
							}
						
							var id = 'lane_recom_'+type+'_'+recom_seqNum;
							var LanePath = new Array;								//경로 좌표를 hashMap에 저장 
							for(var i=0; i<routeData[b].steps.length; i++){
								LanePath.push([i , routeData[b].steps[i].polylines]); 
							}
							recommandMap.put(id,LanePath);
		
							var childId = 'child_'+type+'_'+recom_seqNum;
							recommandChildMap.put(childId, pathChildren);
				
							var walkTime	= 0;
							var busCount	= 0;
							var subwayCount	= 0;
							var html = '';
							var list_station  = '';
							var detailInfo = '';
							var detailCnt = 0;
							var walkSeq = new Array();
						
							for(var i = 0; i<pathChildren.length; i++){
								var pathChild = pathChildren[i];
								var nodeNm = pathChild.transitMode;
								if(nodeNm=='WALKING'){
									walkSeq.push(i);
									walkTime = walkTime + (pathChild.duration/60).toFixed(0);
									var moveTime = (pathChild.duration/60).toFixed(0);  //(pathChild.duration/60).toFixed(0);
									var moveDistance = pathChild.distance;
									var moveMiterType = 'm';
									if(moveDistance >= 1000){ // 거리가 1000m가 넘으면 km로 변환 ( 소수점 2자리까지 반올림)
										moveDistance = (pathChild.distance/1000).toFixed(2);
										moveMiterType = 'km';
									}
									
									var startName = pathChild.startStationName;
									var endName = ''; 
									if(i<pathChildren.length-1){	
										endName = pathChildren[i+1].startStationName;
									}	
									var endName_c = (endName.length > 13) ? endName.substring(0,12)+'...' : endName;
									
									if(i == 0){
										detailInfo += '<li class="step">';
										detailInfo += '<div class="pin"><img src="/gbis2014/images/ico/common/start.png" alt="출발" width="26" height="30" /></div>';
										detailInfo += '<div class="desc">';
										detailInfo += '<a href=\'javascript:detailCenter("recommand", '+detailCnt+');\'>';
										detailInfo += '<p class="tit"><em>'+startLocName_c+'</em> 출발</p>';
										detailInfo += '</a>';
										detailInfo += '</div></li>';
										detailCnt++;
									}

									detailInfo += '<li class="step">';
									detailInfo += '<div class="pin"><img src="/gbis2014/images/ico/common/pin_walk_on.png" alt="" width="25" height="25" /></div>';
									detailInfo += '<div class="desc">';
									detailInfo += '<a href=\'javascript:detailCenter("recommand", '+detailCnt+');\'>';
									var startPathChild = new Array() ;
									var moveType='';
									if( i < (pathChildren.length-1)){
										startPathChild = pathChildren[i+1];
										moveType = startPathChild.transitMode;
									}
									var stRTID ;
									if(moveType=='BUS'){
										stRTID = startPathChild.stations[0].displayId;
										//4자리 정류소번호 처리
										if(stRTID.length == 4){
											stRTID = "0"+stRTID;
										}
										detailInfo += '<p class="tit"><em>도보로 '+endName_c+'('+stRTID+') 정류소</em>까지 이동</em></p>';
									}else if(moveType=='SUBWAY'){
										detailInfo += '<p class="tit"><em>도보로 '+endName_c+'역</em>까지 이동</em></p>';	
									}
									
									detailInfo += '<p class="txt"><span class="time">약 '+moveTime+'분</span><span class="distance">'+moveDistance+moveMiterType+'</span></p>';
									detailInfo += '</a></div></li>';
									detailCnt++;
									
									if(i == parseInt(pathChildren.length)-1){
										detailInfo += '<li class="step">';
										detailInfo += '<div class="pin"><img src="/gbis2014/images/ico/common/pin_end.png" alt="도착" width="26" height="30" /></div>';
										detailInfo += '<div class="desc">';
										detailInfo += '<a href=\'javascript:detailCenter("recommand", '+detailCnt+');\'>';
										detailInfo += '<p class="tit"><em>'+endLocName_c+'</em> 도착</p>';
										detailInfo += '</a>';
										detailInfo += '</div></li>';
										detailCnt++;
									}
								}
								if(nodeNm=='SUBWAY' || nodeNm=='BUS'){
									var moveType = nodeNm;
									
									if(moveType=='SUBWAY'){
										subwayCount	 = (pathChild.stations.length) - 1;
										var laneAlias = pathChild.subway.name;
										var expressYN = pathChild.subway.expressTypeName;
										var subColor = '';
										var stName = pathChild.startStationName;
										var stName_c = (stName.length > 10) ? stName.substring(0,9)+'...' : stName;
										var enName = pathChild.endStationName;
										var moveTime = (pathChild.duration/60).toFixed(0);
										var moveDistance = pathChild.distance;
										var moveMiterType = 'm';
										if(moveDistance >= 1000){ // 거리가 1000m가 넘으면 km로 변환 ( 소수점 2자리까지 반올림)
											moveDistance = (pathChild.distance/1000).toFixed(2);
											moveMiterType = 'km';
										}
										
										if(laneAlias.indexOf('수인분당') != -1){
											subColor = 'sub000';
										}else if(laneAlias.indexOf('에버라인') != -1){  
											subColor = 'sub011';
										}else if(laneAlias.indexOf('인천1호선') != -1){   // 인천1호선 먼저 
											subColor = 'sub012';	
										}else if(laneAlias.indexOf('인천2호선') != -1){    // 인천2호선 먼저
											subColor = 'sub013';
										}else if(laneAlias.indexOf('경의중앙선') != -1){
											subColor = 'sub014';	
										}else if(laneAlias.indexOf('우이신설선') != -1){
											subColor = 'sub015';
										}else if(laneAlias.indexOf('김포골드라인') != -1){
											subColor = 'sub016';	
										}else if(laneAlias.indexOf('공항철도') != -1){
											subColor = 'sub020';
										}else if(laneAlias.indexOf('신분당선') != -1){
											subColor = 'sub022';	
										}else if(laneAlias.indexOf('경춘선') != -1){
											subColor = 'sub023';
										}else if(laneAlias.indexOf('의정부경전철') != -1){
											subColor = 'sub024';	
										}else if(laneAlias.indexOf('경강선') != -1){
											subColor = 'sub025';
										}else if(laneAlias.indexOf('서해선') != -1){
											subColor = 'sub026';
										}else if(laneAlias.indexOf('신림선') != -1){
											subColor = 'sub027';
										}else if(laneAlias.indexOf('동해선') != -1){
											subColor = 'sub028';
										}else if(laneAlias.indexOf('자기부상') != -1){
											subColor = 'sub029';
										}else if(laneAlias.indexOf('1호선') != -1){
											subColor = 'sub001';
										}else if(laneAlias.indexOf('2호선') != -1){
											subColor = 'sub002';
										}else if(laneAlias.indexOf('3호선') != -1){
											subColor = 'sub003';
										}else if(laneAlias.indexOf('4호선') != -1){
											subColor = 'sub004';
										}else if(laneAlias.indexOf('5호선') != -1){
											subColor = 'sub005';
										}else if(laneAlias.indexOf('6호선') != -1){
											subColor = 'sub006';
										}else if(laneAlias.indexOf('7호선') != -1){
											subColor = 'sub007';
										}else if(laneAlias.indexOf('8호선') != -1){
											subColor = 'sub008';
										}else if(laneAlias.indexOf('9호선') != -1){
											subColor = 'sub009';
										}else {
											subColor = 'sub100';   //default
										}

										
										//list_station += '<span><img src="/gbis2014/images/ico/subway/'+laneAlias+'.png" alt="'+laneAlias+'호선" /></span>';
										if (expressYN == "급행"){
											 expressYN = '<span class="express">급행</span>';
										}else{
											expressYN = "";
										} 
										list_station += '<span class="sub_icon '+subColor+'">'+laneAlias+'</span>'+expressYN;
										
										if(stName_c.indexOf("역")<1){
											list_station += '<span><em>'+stName_c+'역</em></span>';
										} else {
											list_station += '<span><em>'+stName_c+'</em></span>';
										}
										list_station += '<span class="arrow2"><img src="/gbis2014/images/ico/common/arrow_r.gif" alt="" /></span>';
										
										detailInfo += '<li class="step">';
										detailInfo += '<div class="pin"><img src="/gbis2014/images/ico/common/pin_subway_on.png" alt="" width="25" height="25" /></div>';
										detailInfo += '<div class="desc">';
										detailInfo += '<a href=\'javascript:detailCenter("recommand", '+detailCnt+');\'>';
										if(stName_c.indexOf("역")<1){
											detailInfo += '<p class="tit"><span class="sub_icon '+subColor+'">'+laneAlias+'</span>'+expressYN+'&nbsp;<em>'+stName_c+'역</em> 승차 후 '+subwayCount+'개 역 이동</p>';
										} else {
											detailInfo += '<p class="tit"><span class="sub_icon '+subColor+'">'+laneAlias+'</span>'+expressYN+'&nbsp;<em>'+stName_c+'</em> 승차 후 '+subwayCount+'개 역 이동</p>';
										}
										if(enName.indexOf("역")<1){
											detailInfo += '<p class="tit"><span class="sub_icon '+subColor+'">'+laneAlias+'</span>&nbsp;<em>'+enName+'역</em>에서 하차</p>';
										} else {
											detailInfo += '<p class="tit"><span class="sub_icon '+subColor+'">'+laneAlias+'</span>&nbsp;<em>'+enName+'</em>에서 하차</p>';
										}
										
										detailInfo += '<p class="txt">약 '+moveTime+'분 '+moveDistance+moveMiterType+'</p>';
										detailInfo += '</a></div></li>';
										detailCnt++;
											
									}else if(moveType=='BUS'){
										busCount = busCount + (pathChild.stations.length - 1); 
										var laneAlias 	= pathChild.bus.typeName + pathChild.bus.name+'번';
										//버스번호에 경기도가 있을 때 경기도 글자 삭제
										//if(laneAlias.indexOf('경기도') != -1) laneAlias = laneAlias.replace('경기도','');
										
										var stName = pathChild.startStationName;
										var stName_c = (stName.length > 10) ? stName.substring(0,9)+'...' : stName;
										var enName = pathChild.endStationName;
										var moveDistance = pathChild.distance;
										var moveMiterType = 'm';

										if(moveDistance >= 1000){ // 거리가 1000m가 넘으면 km로 변환 ( 소수점 2자리까지 반올림)
											moveDistance = (pathChild.distance/1000).toFixed(2);
											moveMiterType = 'km';
										}
										var moveTime = (pathChild.duration/60).toFixed(0);
										var stopCount = pathChild.stations.length - 1;
										//정류소번호
										var stRTID = pathChild.stations[0].displayId;
										//4자리 정류소번호 처리
										if(stRTID.length == 4){
											stRTID = "0"+stRTID;
										}
										stRTID = (stRTID != '') ? '(' + stRTID + ')' : '()';
										var edRTID = pathChild.stations[stopCount].displayId;
										//4자리 정류소번호 처리
										if(edRTID.length == 4){
											edRTID = "0"+edRTID;
										}
										edRTID = (edRTID != '') ? '(' + edRTID + ')' : '()';


										var alternatives = pathChild.bus.alternatives;
										if (alternatives && alternatives.length >= 1) {
											var alt_string ='';
											for(var j = 0; j<alternatives.length; j++){
												alt_string += '<p class="alternatives"> 대체버스 : '+alternatives[j].typeName + alternatives[j].name+'번</p>';
											}

											list_station += '<span><em class="num_red">'+laneAlias+'</em></span>';
                                            list_station += '<span>&nbsp;'+stName_c+'</span>';
                                            list_station += '<span class="arrow2"><img src="/gbis2014/images/ico/common/arrow_r.gif" alt="" /></span>';
                                            
                                            detailInfo += '<li class="step">';
                                            detailInfo += '<div class="pin"><img src="/gbis2014/images/ico/common/pin_bus_on.png" alt="" width="25" height="25" /></div>';
                                            detailInfo += '<div class="desc">';
                                            detailInfo += '<a href=\'javascript:detailCenter("recommand", '+detailCnt+');\'>';
                                            //detailInfo += '<p class="tit"><em>'+stName_c+' ' +stopCount+'개 정류소 이동</em></p>';
                                            detailInfo += '<p class="tit"><strong>'+laneAlias+'('+stName_c+stRTID+') 정류소</strong> 승차 후 '+stopCount+'개 정류소 이동, <strong>'+enName+edRTID+' 정류소</strong>에서 하차</p>';
											detailInfo += alt_string;

											detailInfo += '<p class="txt">약 '+moveTime+'분 '+moveDistance+moveMiterType+'</p>';
											detailInfo += '</a></div></li>';
											detailCnt++;	
										}else{
											list_station += '<span><em class="num_red">'+laneAlias+'</em></span>';
                                            list_station += '<span>&nbsp;'+stName_c+'</span>';
                                            list_station += '<span class="arrow2"><img src="/gbis2014/images/ico/common/arrow_r.gif" alt="" /></span>';
                                            
                                            detailInfo += '<li class="step">';
                                            detailInfo += '<div class="pin"><img src="/gbis2014/images/ico/common/pin_bus_on.png" alt="" width="25" height="25" /></div>';
                                            detailInfo += '<div class="desc">';
                                            detailInfo += '<a href=\'javascript:detailCenter("recommand", '+detailCnt+');\'>';
                                            //detailInfo += '<p class="tit"><em>'+stName_c+' ' +stopCount+'개 정류소 이동</em></p>';
                                            detailInfo += '<p class="tit"><strong>'+laneAlias+'('+stName_c+stRTID+') 정류소</strong> 승차 후 '+stopCount+'개 정류소 이동, <strong>'+enName+edRTID+' 정류소</strong>에서 하차</p>';
                                            detailInfo += '<p class="txt">약 '+moveTime+'분 '+moveDistance+moveMiterType+'</p>';
                                            detailInfo += '</a></div></li>';
                                            detailCnt++;
										}

										
									}
								}	
							}

							list_station = list_station.substring(0, list_station.length-88);
							jQuery(".starting").text(startLocName_c);
							jQuery(".ending").text(endLocName_c);
							
							html += '<li>';
							html += '<a href="javascript:recommandLineRoute(\''+type+'\',\''+recom_seqNum+'\')">';
							html += '<div class="path_line">';
							html += list_station;
							html += '</div>';
							html += '<div class="path_infolst">';
							html += '<span class="time">소요시간 : 약 '+time+'분</span>';
							html += '<span class="pay">교통비 : 약 '+payment+'</span>';
							html += '<span class="distance">거리 : 약 '+distance+distanceMiterType+'</span>';
							html += '</div>';
							html += '<p class="path_more"></p>';
							html += '</a>';
							html += '<ol class="dtl_rute detailResult" id="detailResult_recom_'+recom_seqNum+'" style="display:none;">';
							html += detailInfo;
							html += '</ol>';
							html += '</li>';
									
						if(recom_seqNum == 1){  //추천 최초 항목 변수 저장
							firstType = type;
							firstSeq = 1; 
						}
						recomWalkMap.put(id, walkSeq);
						jQuery('.listRoute_recommand').append(html);
						recom_seqNum++;
						searchFlag = true;
					 }
				 }
			 }
			 
			//리스트 선택시 스크롤 이동
			$('#list_cmn_recommand .listRoute_recommand > li').click(function(){
				var thisIndex = $('#list_cmn_recommand .listRoute_recommand > li').index(this);
				var listScrollPoint = Number(thisIndex) * 100;
				jQuery("#list_cmn_recommand").animate({scrollTop:listScrollPoint}, 0);
				
			});
	   }
  }else{
	  removeLineMarker(); //경로 및 마크 삭제
	  jQuery(".starting").text(startLocName_c);
	  jQuery(".ending").text(endLocName_c);
	  var list = '';
	  list += '<li class=\'cannot_find\'>';
	  list += '검색 결과가 없습니다.';
      list += '</li>';
	  jQuery(".recommandCnt").html("( 0 )");
	  jQuery('.listRoute_recommand').append(list);
	  searchFlag = false;
  }	 
	 if(searchFlag){ // 검색결과가 있을경우만
		 
		 removeLineMarker(); // 예전 경로 및 마크 삭제
		 recommandFlag = true;
		 recommandLineRoute(firstType, firstSeq);  //검색 완료시 추천 첫번째 경로 뿌리기
	 }
	 jQuery('.arrow').show();
	 searchListEvt();
 }
 
 
 
//버스, 환승 경로 표현
 var _Markers  = new Tmap.Layer.Markers();
 var busTransferFlag = false;
 var beforeType = '';
 var beforeSeq = '';
 var childData_bus = '';
 function lineRoute(type, seq){
	 if(beforeType == type && beforeSeq == seq){
		 if(!busTransferFlag){
			 jQuery(".detailResult").hide();  //전체 상세리스트 숨기기
			 busTransferFlag = true;
		 }else{
			 jQuery("#detailResult_"+type+"_"+seq+"").css('display', 'block');  //선택한 상세리스트 보여주기
			 busTransferFlag = false;
		 }
	 }else{
		 jQuery(".detailResult").hide();  //전체 상세리스트 숨기기
		 jQuery("#detailResult_"+type+"_"+seq+"").css('display', 'block');  //선택한 상세리스트 보여주기
		 busTransferFlag = false;
	 }
	 
	 beforeType = type;
	 beforeSeq = seq;
	 
	 removeLineMarker(); // 경로 및 마크 지우기
	 var childId = 'child_'+type+'_'+seq;
	 childData_bus = childMap.get(childId);
	 
	 // 도보는 초록라인, 그 외는 빨강 라인으로 경로 뿌리기
	 routeLineMake(childData_bus); // 경로 그리기
 }
 
 // 경로 그려주는 함수 // 
 function routeLineMake(childData){
	 var startEndPoint = new HashMap();
	 var walkSeq_c = new Array();
	 var tranSeq_c = new Array();
	 var walkTimeCnt =0;
	 var dualExChange=0;
	 for(var t = 0; t<childData.length; t++){
		 var DataChild = childData[t];
		 var moveType = childData[t].transitMode;
		 
		 if(moveType == "WALKING"){  // 워크일때 초록색으로 경로표시

			 if (t==0){
				var lineList = [];
			 	var x = startLon;
				var y = startLat;				
				
				lineList.push(new Tmap.Geometry.Point(x,y));
				
				for(var u=0; u<DataChild.polylines.length; u++){
					var x_wgs84 = DataChild.polylines[u].x;
					var y_wgs84 = DataChild.polylines[u].y;
					var coordResult=[];
					 coordResult = wgs2espg(x_wgs84,y_wgs84);
					var x = coordResult[0];
					var y = coordResult[1];
					
					lineList.push(new Tmap.Geometry.Point(x,y));
				}
				var lineString = new Tmap.Geometry.LineString(lineList);
				var up_style_bold = {strokeWidth: 5, strokeColor:"green"}; //라인스타일
				var mLineFeature = new Tmap.Feature.Vector(lineString, null, up_style_bold);
				map.addLayers([lines]);
				lines.addFeatures([mLineFeature]);
			 }
			 			 
			 var lineList = [];
			 if(t>0){
				var tmpBefore = childData[t-1];
				var tmpBeforePoly = tmpBefore.polylines;
				var x_wgs84 =  tmpBeforePoly[tmpBeforePoly.length-1].x;
				var y_wgs84 =  tmpBeforePoly[tmpBeforePoly.length-1].y;
				var coordResult=[];
				 coordResult = wgs2espg(x_wgs84,y_wgs84);
				var x = coordResult[0];
				var y = coordResult[1];
				
				lineList.push(new Tmap.Geometry.Point(x,y));
			 }
			 for(var u=0; u<DataChild.polylines.length; u++){
				var x_wgs84 = DataChild.polylines[u].x;
				var y_wgs84 = DataChild.polylines[u].y;
				var coordResult=[];
				 coordResult = wgs2espg(x_wgs84,y_wgs84);
				var x = coordResult[0];
				var y = coordResult[1];
				
				lineList.push(new Tmap.Geometry.Point(x,y));
			 }
		     
			 if(t<childData.length-1){
					var tmpBefore = childData[t+1];
					var tmpBeforePoly = tmpBefore.polylines;
					var x_wgs84 =  tmpBeforePoly[0].x;
					var y_wgs84 =  tmpBeforePoly[0].y;
					var coordResult=[];
					 coordResult = wgs2espg(x_wgs84,y_wgs84);
					var x = coordResult[0];
					var y = coordResult[1];
					
					lineList.push(new Tmap.Geometry.Point(x,y));
			 }
			 if(t == childData.length-1){
				 	var x = endLon;
					var y = endLat;					
					lineList.push(new Tmap.Geometry.Point(x,y));
			 }
		     var lineString = new Tmap.Geometry.LineString(lineList);
			 var up_style_bold = {strokeWidth: 5, strokeColor:"green"}; //라인스타일
			 var mLineFeature = new Tmap.Feature.Vector(lineString, null, up_style_bold);
			 map.addLayers([lines]);
			 lines.addFeatures([mLineFeature]);
			 startEndPoint.put(u, lineList);
	 
			 
		 } else if (moveType != "WALKING" && t!=childData.length-1){  // 워크 외의 경로는 빨강색으로 경로 표시
			 var lineList = [];
			 for(var u=0; u<DataChild.polylines.length; u++){
				var x_wgs84 = DataChild.polylines[u].x;
				var y_wgs84 = DataChild.polylines[u].y;
				var coordResult=[];
				 coordResult = wgs2espg(x_wgs84,y_wgs84);
				var x = coordResult[0];
				var y = coordResult[1];
				lineList.push(new Tmap.Geometry.Point(x,y));
			  }
		     var lineString = new Tmap.Geometry.LineString(lineList);
			 var up_style_bold = {strokeWidth: 5, strokeColor:"#FF0000"}; //라인스타일
			 var mLineFeature = new Tmap.Feature.Vector(lineString, null, up_style_bold);
			 map.addLayers([lines]);
			 lines.addFeatures([mLineFeature]);
			 startEndPoint.put(u, lineList);
	 	}
 	}	
	 
	 // 경로 icon 표시
	 iconMaking(childData);
 }
 
//추천 경로 표현
 var recommandFlag = false;
 var recommandType = '';
 var recommandSeq = '';
 var childData_recom = '';
 function recommandLineRoute(type, seq){
	 if(recommandType == type && recommandSeq == seq){
		 if(!recommandFlag){
			 jQuery(".detailResult").hide();  //전체 상세리스트 숨기기
			 $('.path_more').removeClass('active');
			 recommandFlag = true;
		 }else{
			 jQuery("#detailResult_recom_"+seq).css('display', 'block');  //선택한 상세리스트 보여주기
			 recommandFlag = false;
		 }
	 }else{
		 jQuery(".detailResult").hide();  //전체 상세리스트 숨기기
		 jQuery("#detailResult_recom_"+seq).css('display', 'block');  //선택한 상세리스트 보여주기
		 /*첫번째 리스트 스타일 추가_장지원*/
		 jQuery("#detailResult_recom_"+seq).parent('li').find('.path_more').addClass('active');
		 jQuery("#detailResult_recom_"+seq).parent('li').children('a').addClass('active');
		 recommandFlag = false;
	 }
	 recommandType = type;
	 recommandSeq = seq;
	 
	 removeLineMarker(); // 경로 및 마크 지우기

	 var id = 'lane_recom_'+type+'_'+seq;
	 var line = recommandMap.get(id);
	 var walkLine = recomWalkMap.get(id);
	 
	 var childId = 'child_'+type+'_'+seq;
	 childData_recom = recommandChildMap.get(childId);

		 //경로 그리기
		 routeLineMake(childData_recom); // 경로 그리기

 }
 // 상세 정보 클릭시 해당 지역으로 이동 (버스, 환승)
 function detailCenter(type, seq){
	 if(type == 'bus'){ // 버스나 환승 상세정보 클릭시 좌표이동
		 if(seq == 0){
			 var x = startLon;
			 var y = startLat;
			 map.setCenter(new Tmap.LonLat(x, y), 18);
		 }else if(seq == 1){
			 
		 }else if (seq == childData_bus.length+1){
			 var x = endLon;
			 var y = endLat;
			 map.setCenter(new Tmap.LonLat(x, y), 18);
		 }else{
			 for(var i=0; i<childData_bus.length+1; i++){
				 var child = childData_bus[i-1];
				 if(seq == i){
					 var x_wgs84 = child.polylines[0].x;
					 var y_wgs84 = child.polylines[0].y;
					 var coordResult=[];
					  coordResult = wgs2espg(x_wgs84,y_wgs84);
					 var x = coordResult[0];
					 var y = coordResult[1];
					 map.setCenter(new Tmap.LonLat(x, y), 18);
			     }
		      }
		 }

	 }else{  // 추천에서 상세정보 클릭시 좌표이동
		 if(seq == 0 || seq == 1){
			 var x = startLon;
			 var y = startLat;
			 map.setCenter(new Tmap.LonLat(x, y), 18);
		 }else if (seq == childData_recom.length+1){
			 var x = endLon;
			 var y = endLat;
			 map.setCenter(new Tmap.LonLat(x, y), 18);
		 }else{
			 for(var i=0; i<childData_recom.length+1; i++){
				 var child = childData_recom[i-1];
				 
				  if(seq == i){
					 var x_wgs84 = child.polylines[0].x;
					 var y_wgs84 = child.polylines[0].y;
					 var coordResult=[];
					  coordResult = wgs2espg(x_wgs84,y_wgs84);
					 var x = coordResult[0];
					 var y = coordResult[1];
					 map.setCenter(new Tmap.LonLat(x, y), 18);
				 }
			} 
		 }
	 }
 }
 // 경로 위 아이콘 표시
 var routeIconXy = new HashMap();
 function iconMaking(childData){
	 
		for(var i=0; i<childData.length; i++){
				var child = childData[i];
				var nodeNm = child.transitMode;
				if(nodeNm=='WALKING'){
					if(i>0){
						var x_wgs84 = child.polylines[0].x;
						var y_wgs84 = child.polylines[0].y;
						var coordResult=[];
						 coordResult = wgs2espg(x_wgs84,y_wgs84);
						var x = coordResult[0];
						var y = coordResult[1];
						
						addMarker('images/ico/common/pin_walk.png',x ,y ,nodeNm+i, i);  // 도보 아이콘
					}
				}else{
					if(nodeNm=='SUBWAY'){
						var x_wgs84 = child.polylines[0].x;
						var y_wgs84 = child.polylines[0].y;
						var coordResult=[];
						 coordResult = wgs2espg(x_wgs84,y_wgs84);
						var x = coordResult[0];
						var y = coordResult[1];
						addMarker('images/ico/common/trans_subway.png',x,y, nodeNm+i, i); // 지하철 아이콘
						
					}else if(nodeNm=='BUS'){
						var x_wgs84 = child.polylines[0].x;
						var y_wgs84 = child.polylines[0].y;
						var coordResult=[];
						 coordResult = wgs2espg(x_wgs84,y_wgs84);
						var x = coordResult[0];
						var y = coordResult[1];
						addMarker('images/ico/common/trans_bus.png',x,y, nodeNm+i, i);  // 버스 아이콘
					}
				}
				// 출발 아이콘
				if(i==0){
					var x = startLon;
					var y = startLat;
					addMarker('images/ico/common/pin_start.png',x,y);
					addMarkerStartEnd('images/ico/common/pin_start.png',x,y);
				}
				
				// 도착지 아이콘
				if(i==childData.length-1){
					var x = endLon;
					var y = endLat;
					addMarker('images/ico/common/pin_end.png',x ,y);
					addMarkerStartEnd('images/ico/common/pin_end.png',x ,y);
				}
			}
 }
 // 경로 위 아이콘 표시
 function addMarkerStartEnd(img, x, y){
	  var imgType = img.substring(img.lastIndexOf("_")+1, img.lastIndexOf("."));
	  var size = new Tmap.Size(26, 30);
	  
	  var offset = new Tmap.Pixel(-(size.w / 2), -size.h);
	  var images = "<img src=/gbis2014/"+img+" />";
	  
	  var iconHtml = new Tmap.IconHtml(images, size, offset);
	  var marker_c = new Tmap.Marker(new Tmap.LonLat(x, y), iconHtml);
	  map.addLayer(_Markers);
	  if(imgType == 'start'){
		  startMarkers.addMarker(marker_c);
	  }else if(imgType == 'end'){
		  endMarkers.addMarker(marker_c);
	  }
 }
 
 var _MarkersMap = new HashMap();
 function addMarker(img, x, y, id, seq){
		
	    var imgType = img.substring(img.lastIndexOf("_")+1, img.lastIndexOf("."));
	    var size;
	    if(imgType == 'start' || imgType == 'end'){
	    	size = new Tmap.Size(26, 30);
	    }else if(imgType == 'walk'){
	    	size = new Tmap.Size(35, 35);
	    }else{
	    	size = new Tmap.Size(50, 40);
	    }
		 
		var offset = new Tmap.Pixel(-(size.w / 2), -size.h);
		var images = '';
		if(id){
			images = "<img class="+ imgType + seq +"  src=/gbis2014/"+img+" />";
	    }else{
	    	images = "<img src=/gbis2014/"+img+" />";
		}
		var iconHtml = new Tmap.IconHtml(images, size, offset);
		var marker_c = new Tmap.Marker(new Tmap.LonLat(x, y), iconHtml);
		
		if(imgType == 'bus'){
		//	marker_c.events.register("click", marker_c, onTouchMarker);
		}
		
		map.addLayer(_Markers);
		_Markers.addMarker(marker_c);
		if(!busTransferFlag && !recommandFlag){
			map.zoomToExtent(_Markers.getDataExtent());
		}
		if(id){
			_MarkersMap.put(id, marker_c);
			marker_c.events.register('mouseover', imgType+seq, onMarkerover);
			marker_c.events.register('mouseout', imgType+seq, onMarkerout);
		}else{
			_MarkersMap.put(img, marker_c);
		}
}

// 경로 마크 마우스오버시 이벤트
function onMarkerover(evt){
	
	var imgType = '';
	for(var i = 0; i<this.length; i++){
		imgType += this[i];
	}
	
	var imgType_c = imgType.substring(0, this.length-1);
	
	if(imgType_c == 'walk'){
		jQuery("."+imgType).attr("src", "/gbis2014/images/ico/common/pin_walk_on.png");
	}else if(imgType_c == 'subway'){
		jQuery("."+imgType).attr("src", "/gbis2014/images/ico/common/trans_subway_on.png");
	}else if(imgType_c == 'bus'){
		jQuery("."+imgType).attr("src", "/gbis2014/images/ico/common/trans_bus_on.png");
	}
}
//경로 마크 마우스아웃시 이벤트
function onMarkerout(evt){
	
	var imgType = '';
	for(var i = 0; i<this.length; i++){
		imgType += this[i];
	}
	var imgType_c = imgType.substring(0, this.length-1);
	
	if(imgType_c == 'walk'){
		jQuery("."+imgType).attr("src", "/gbis2014/images/ico/common/pin_walk.png");
	}else if(imgType_c == 'subway'){
		jQuery("."+imgType).attr("src", "/gbis2014/images/ico/common/trans_subway.png");
	}else if(imgType_c == 'bus'){
		jQuery("."+imgType).attr("src", "/gbis2014/images/ico/common/trans_bus.png");
	}
}

function removeLineMarker(){
	 lines.destroyFeatures();  // 예전 경로 지우기
	 _Markers.clearMarkers();  // 예전 경로 위 마크 지우기
}

function ajaxErrorRoute(){
	alert("해당경로를 검색할 수 없습니다");
}

function onTouchMarker(evt){
//	console.log("marekt touch and event start");
}

function  wgs2espg( x_wgs84,  y_wgs84 ){
	epsg = [];
	var r_major, r_minor, deg_rad, temp, es, eccent, phi, sinphi, con, com, ts, pa, xx, yy;

	xx = x_wgs84;
	yy = y_wgs84;
	
	r_major = 6378137.0;
	r_minor = 6356752.3142;
	
	pa = 3.1415926535897932384626433832795028842;
    deg_rad = pa / 180;
    
    epsg[0] = r_major * ( xx * deg_rad);
    
    if( yy > 89.5 ) {
    	yy = 89.5;
    }
    else if( yy < -89.5) {
    	yy = -89.5;
    }
	
    temp = r_minor / r_major;
    es = 1 - Math.pow(temp, 2);
    eccent = Math.sqrt(es);
    phi = yy * deg_rad;
    sinphi = Math.sin(phi);
    con = eccent * sinphi;
    com = 0.5 * eccent;
    con = Math.pow( 1-con / 1+con, com );
    ts = Math.tan( 0.5 * ((pa*0.5)-phi) ) / con;
    epsg[1] = 0 - r_major * Math.log(ts);
    
	return epsg;
}

function epsg2Wgs( x_epsg, y_epsg ) {
	
	wgs = [];
	var   r_major, r_minor, rad_deg, temp, eccent, phi, dphi, con, com, ts, pa, pa2, xx, yy;
	var      ii;

	xx           = x_epsg;
	yy           = y_epsg;
	
	r_major      = 6378137.0;
	r_minor      = 6356752.3142;
	
	pa           = 3.1415926535897932384626433832795028842;
	pa2          = 3.1415926535897932384626433832795028842 / 2.0;
	
    rad_deg      = 180 / pa;
    
    
    temp         = r_minor / r_major;
    eccent       = Math.sqrt(1.0 - (temp * temp));
    com          = 0.5 * eccent;
    
    wgs[0]       = (xx * rad_deg) / r_major; // x_wgs
    
    ts           = Math.exp((yy - yy * 2) / r_major);
    phi          = pa2 - 2 * Math.atan(ts);
    dphi         = 1.0;
    
    ii           = 0;
    
    while((Math.abs(dphi) > 0.000000001) && (ii < 15)) {
    	
    	con      = eccent * Math.sin(phi);
    	dphi     = pa2 - 2 * Math.atan(ts * Math.pow(1.0 - con / 1.0 + con, com)) - phi;
    	phi      = phi + dphi;
    	ii       = ii + 1;
    }
    
    wgs[1]       = rad_deg * phi; // y_wgs
    
	return wgs;
}

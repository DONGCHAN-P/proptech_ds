// server
var map;
var rightLonlat;
var clientX, clientY;
var lnbStatus = true;
var dataTmp;
var searchGubun; 

var poiObj = {};
var stationObj = {};
var subwayObj = {};
var routeObj = {};
var upRouteStationObj = {};
var downRouteStationObj = {};

var poiMarkerLayer = new Tmap.Layer.Markers();
var stationMarkerLayer = new Tmap.Layer.Markers();
var subwayMarkerLayer = new Tmap.Layer.Markers();
var routeMarkerLayer = new Tmap.Layer.Markers();
var upRouteMarkerLayer = new Tmap.Layer.Markers();
var downRouteMarkerLayer = new Tmap.Layer.Markers();
var upRealBusRouteMarkerLayer = new Tmap.Layer.Markers();
var downRealBusRouteMarkerLayer = new Tmap.Layer.Markers();
var upRealBusRouteLowMarkerLayer = new Tmap.Layer.Markers();
var downRealBusRouteLowMarkerLayer = new Tmap.Layer.Markers();

var stationMarker, subwayMarker, poiMarker, routeMarker;

var startMarkers = new Tmap.Layer.Markers();
var endMarkers = new Tmap.Layer.Markers();
var viaMarkers = new Tmap.Layer.Markers();
var startMarker;
var endMarker;
 
var up_line_layer = new Tmap.Layer.Vector('Tmap Vector Layer');
var down_line_layer = new Tmap.Layer.Vector('Tmap Vector Layer');

//pr_3857 인스탄스 생성.
var pr_3857 = new Tmap.Projection("EPSG:3857");
//pr_4326 인스탄스 생성.
var pr_4326 = new Tmap.Projection("EPSG:4326");	//wgs84

var panZoomBar;
var chkNum = 1;
var crPopup;
var crLon;
var crLat;

var route_station_id;
var station_id;
var route_id;
var route_name = "";
var si_flag;
var route_tp;
var updown_status;

var tab_status;

var now = new Date(); // 현재시간
var nowtime1 = now.getHours();
var nowtime2 = now.getHours() + "" + now.getMinutes();
// && (nowtime2 > 640 && nowtime1 < 9)

//다중노선
var upRouteStationObjArr = [];
var downRouteStationObjArr = [];
var upRouteMarkerLayerArr = [];
var downRouteMarkerLayerArr = [];
var up_line_layerArr = [];
var down_line_layerArr = [];
var lineStyleArr = ["rgba(128, 000, 128, 0.4)","rgba(255, 000, 000, 0.4)","rgba(000, 000, 255, 0.4)","rgba(000, 255, 255, 0.4)","rgba(000, 128, 0, 0.4)",
                    "rgba(255, 000, 255, 0.4)","rgba(255, 255, 000, 0.4)","rgba(000, 102, 102, 0.4)","rgba(255, 153, 000, 0.4)","rgba(223, 6, 249, 0.4)"];

for (var i=0; i <= 10; i++){
	upRouteStationObjArr[i] = {};
	downRouteStationObjArr[i] = {};
	upRouteMarkerLayerArr[i] = new Tmap.Layer.Markers();
	downRouteMarkerLayerArr[i] = new Tmap.Layer.Markers();
	up_line_layerArr[i] = new Tmap.Layer.Vector('Tmap Vector Layer');
	down_line_layerArr[i] = new Tmap.Layer.Vector('Tmap Vector Layer');
}
//End 다중노선

var localBusMarker, localSubwayMarker, localOfficeMarker;

var localBusMarkerLayer = new Tmap.Layer.Markers();
var localSubwayMarkerLayer = new Tmap.Layer.Markers();
var localOfficeMarkerLayer = new Tmap.Layer.Markers();

var startX,startY,startAddr;

var select;

//정보갱신 변수
var refreshRouteInterval = 300;
var routeT;

//잠시후 도착 예정버스 스크롤러 변수
var s;

//통합검색 정류소 검색결과 저장
var stationIdArr = new Array();
//노선상세 정류소 검색결과 저장
var routeStationIdArr = new Array();
//주변정류장인지 아닌지 구분
var localBusStation = false;

$(window).resize(function() {
	var h = $('.map_view').height() - $('.local_info').height();

	if (map) {
		//$('#map_div').css('height', h + "px");
		map.updateSize();
		
		//줌바 위치 조정
		$(".tmControlPanZoomBar").css("left","");
		$(".tmControlPanZoomBar").css("right","45px");
		$(".tmControlPanZoomBar").css("top","20px");
	}
});

function init() {
	var h = $('.map_view').height() - $('.local_info').height();
	console.log($('.local_info').height());
	map = new Tmap.Map({
		div:'map_div', 
		width: '100%',
		//height: h+'px',
		displayProjection: new Tmap.Projection("EPSG:3857"),
		transitionEffect: 'resize',
		minZoom:7,
		ignoreOSM: true
	});
	map.setCenter(new Tmap.LonLat("14138635.805841","4477459.6504941"));
	
	addLayerForSpace(map); //거리재기
	ReverseGeocoding(); //초기 로드 시 리버스지오코딩
	map.events.register("moveend", map, onMoveEnd); //지도 이동 시 리버스지오코딩
	map.events.register("mouseup", map, onRightMenu); //마우스 우측버튼 클릭 이벤트
	map.removeZoomControl(); // 줌컨트롤 삭제
	map.removeControl(map.ctrl_info); // 로고 삭제
	map.removeControl(map.ctrl_scale); //축척 삭제
	panZoomBar = new Tmap.Control.PanZoomBar({panIcons:false});
	map.addControl(panZoomBar); //새 줌컨트롤 추가
	
	//축척 텍스트
	moveZoom(); //초기 축척 텍스트 삽입
	map.events.register("zoomend", map, moveZoom); //줌 변경 이벤트 등록
	
	//줌바 위치 조정
	$(".tmControlPanZoomBar").css("left","");
	$(".tmControlPanZoomBar").css("right","45px");
	$(".tmControlPanZoomBar").css("top","20px");
	
	//지역 설정 값 호출
	getStartArea();
	
	//현재 위치 좌표
	if(startX != "" && startY != "" && startX != null && startY != null && startX != "null" && startY != "null"){
		map.setCenter(new Tmap.LonLat(startX, startY));
	}else{
		getLocation();
	}
}

//지역 설정 값 호출
function getStartArea() {
	
	var url = "/service/mybus/MyBus.action";
	var data = 'cmd=getStartArea';
	
	$.ajax({
		async: false,
		type: "post",
		contentType: "application/x-www-form-urlencoded;charset=UTF-8",
		dataType: "json",
		url: url,
		data: data,
		success: getStartAreaSuccess
	});
}

function getStartAreaSuccess(data){
	
	if(data != null){
		startX = data.START_X;
		startY = data.START_Y;
		startAddr = data.START_ADDR;
	}
	
}

//HTML5 navigator.geolocation API
function getLocation(){
	if(navigator.geolocation)
	{
	    navigator.geolocation.getCurrentPosition(	    		
	        // successCallback
	        function(position) {
	        	getGeoLocationJson(position.coords.longitude,position.coords.latitude); // WGS <--> EPSG 좌표변환
	            //console.log( "경도: " + position.coords.longitude ); // 경도
	        	//console.log( "위도: " + position.coords.latitude );  // 위도
	        }, 
	        // errorCallback
	        function(error)
	        {
	            switch(error.code) 
	            {    
	                case error.TIMEOUT:
	                    //alert ('시간 초과');
	                    break;
	                case error.POSITION_UNAVAILABLE:
	                    //alert ('위치를 사용할 수 없음 (이 오류는 위치 정보 공급자가 응답)');    
	                    break;
	                case error.PERMISSION_DENIED: 
	                    //alert ('권한 거부');
	                    break;
	                case error.UNKNOWN_ERROR:    
	                    //alert ('알 수 없는 오류');
	                    break;
	                default : 
	                    //alert ( errro.code);
	            }
	        });
	}
	else
	{
	    //alert("이 브라우저는 geolcation API를 지원하지 않습니다");
	}
}

//WGS <--> EPSG 좌표변환
function getGeoLocationJson(lon,lat){
	var url = "/gbis2014/schBus.action";
	var data = 'cmd=geoLocation';
	data += '&lon='+lon;
	data += '&lat='+lat;
	
	$.ajax({
		type: "post",
		contentType: "application/x-www-form-urlencoded;charset=UTF-8",
		dataType: "json",
		url: url,
		data: data,
		success: getGeoLocationJsonSuccess
	});
}

//현재 위치 좌표 이동
function getGeoLocationJsonSuccess(data){
	map.setCenter(new Tmap.LonLat(data.lon, data.lat));
}

function moveZoom(){
	//축척 텍스트 삽입
	$("#mapFooter .mapScale em").text(map.ctrl_scale.div.innerText);
	
	//줌레벨 14이하 버스노선 정류소 마커 숨김
	if(map.getZoom() < 15){
		layerMarkerHidden(upRouteMarkerLayer);
		layerMarkerHidden(downRouteMarkerLayer);
	}else{
		layerMarkerVisible(upRouteMarkerLayer);
		layerMarkerVisible(downRouteMarkerLayer);
	}
}

function layerMarkerHidden(layer){
	if(layer.markers.length > 0){
		for(var i = 0; i < layer.markers.length; i++){
			if(i != 0 && i != layer.markers.length - 1) layer.markers[i].icon.imageDiv.style.display = "none";
		}
	}
}

function layerMarkerVisible(layer){
	if(layer.markers.length > 0){
		for(var i = 0; i < layer.markers.length; i++){
			layer.markers[i].icon.imageDiv.style.display = "block";
		}
	}
}

function onRightMenu(evt){
	if(evt.button==2 || evt.button==3){
		showMenu(evt);
	}else{
		closeMenu(evt);
	}
}

var pixelX = '';
var pixelY = '';
function showMenu(evt) {
	var menu1 = document.getElementById("rightMenu");
   	
	clientX = evt.clientX;
	clientY = evt.clientY;
	
   	var cX = (lnbStatus) ? evt.clientX-380 : evt.clientX;
   	var cY = evt.clientY - ($("header").height() + $("nav").height());
   	
	var xy = evt.xy; // 맵 XY
	rightLonlat = map.getLonLatFromPixel(xy); // 맵 좌표
   	
   	menu1.style.left=cX+"px";
   	menu1.style.top=cY+"px";
   	menu1.style.display='block';
}
	
function closeMenu(evt) {
	var menu1 = document.getElementById("rightMenu");
   	menu1.style.display='none';
}	

//쿠키 저장하기
function setMyword(){
	var myword = $("#bisSearchKeyword").val();
	myword = myword.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll("\"", "&quot;").replaceAll("'", "&#x27").replaceAll("/", "&#x2F").replaceAll("script","").replaceAll("alert","").replaceAll("document","").replaceAll("cookie","");
	var cookieArr = [];
	if(myword != ""){
		if($.cookie('myword')){ //myword라는 쿠키가 있으면
			var getMyword = $.cookie('myword').split(',');
			
			//검색어 중복제거
			for(var i=0; i < getMyword.length; i++){
				if(getMyword[i] == myword){
					getMyword.splice(i, 1);
				}
			}
			
			if(getMyword.length < 10){ //검색어가 10개 미만이면
				getMyword.push(myword); //검색어 추가
				cookieArr = getMyword;
        		$.cookie('myword', cookieArr);
	    	}else{ //검색어가 10개 이상이면
    			getMyword.shift(); // 첫번째 검색어 삭제
    			getMyword.push(myword); //검색어 추가
				cookieArr = getMyword;
        		$.cookie('myword', cookieArr); //쿠키 저장
	    	}
		}else{ //myword라는 쿠키가 없으면
			cookieArr[0] = myword;
			$.cookie('myword', cookieArr); //쿠키 저장
		}
	}
}

//쿠키 불러오기
function getMyword(){
	if($.cookie('myword')){ //myword라는 쿠키가 있으면
		var getMyword = $.cookie('myword').split(',');
		getMyword.reverse(); //쿠키 역순으로 정렬
		var myword_list = "";
		for (var i=0; i < getMyword.length; i++){
			myword_list += '<li><a href="javascript:selectMyword(\''+getMyword[i]+'\')">'+getMyword[i]+'</a></li>';
		}
		$("#myword").html(myword_list);
	}
}
var clickStatus = true; //표출상태
function frmChk(flag){
	if(flag){
		if(!clickStatus) { //두번째 클릭시 미표출
			$(".recent_list").hide();
		}else{ //첫번째 클릭시 표출
			if(jQuery("#bisSearchKeyword").val() == ""){
				getMyword();
				$(".recent_list").show();
				clickStatus = false; 
			}
		}
	}else{
		$(".recent_list").hide();
	}
}

function frmChkBlur(flag){
	if(!frmFlag){
		if(!flag){
			$(".recent_list").hide();
		}
	}
	clickStatus = true; //표출상태 초기화
}

function frmChkList(flag){
	
	
	if(flag){
		frmFlag = true;
		$(".recent_list").show();
	}else{
		frmFlag = false;
	}
}
function selectMyword(selectword){
	$("#bisSearchKeyword").val(selectword);
	$(".recent_list").hide();
}

var pageOfRoute = 1;
var pageOfBus = 1;
var pageOfSubway = 1;
var pageOfPOI = 1;
var searchStat = 0;

//통합 검색
function searchTotal(tabStat, routeTabSelect){
	
	var searchKeyword = $('#bisSearchKeyword').val();

	searchKeyword = searchKeyword.toUpperCase();
	
	if (searchKeyword == ""){
		return alert("검색어를 입력해주세요");
	}
	
	var regExp = /[\{\}\[\]\/?.,;:|\)*~`!^\_+<>@\#$%&\\\=\(\'\"]/gi;
	if(regExp.test(searchKeyword)){
		searchKeyword = searchKeyword.replace(regExp, "");
	}

	var routeNameType ;
	var singleKeyword = searchKeyword;
	if (singleKeyword.length == 1){
		if( singleKeyword*1 ){
			routeNameType = 'number';
		}else{
			routeNameType = 'string';
		}	
	}
	
	searchGubun = routeTabSelect;
	
	if (routeTabSelect == null || routeTabSelect == ""){
		searchGubun = $('#searchGubun').val();
	}
	searchStat = (tabStat != 1) ? 0 : 1;
	
	//검색일때만 페이징 초기화
	if(searchStat == 0){
		pageOfRoute = 1;
		pageOfBus = 1;
		pageOfSubway = 1;
		pageOfPOI = 1;
	}
	
	var url = "/gbis2014/schBusAPI.action";
	var data = 'cmd=searchAllJson';
	data += '&searchKeyword='+searchKeyword;
	data += '&pageOfRoute='+pageOfRoute;
	data += '&pageOfBus='+pageOfBus;
	data += '&pageOfSubway='+pageOfSubway;
	data += '&pageOfPOI='+pageOfPOI;
	data += '&searchGubun='+searchGubun;
	data += '&routeNameType='+routeNameType;
	
	$.ajax({
		type: "post",
		contentType: "application/x-www-form-urlencoded;charset=UTF-8",
		dataType: "json",
		url: url,
		data: data,
		success:function(data){
			if((gunbunVal == 'busInfo' || gunbunVal == 'excelBusInfo') && routeNm == searchKeyword){
				busInfoSuccess(data);
			}else{
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
            }
		} ,
		error: ajaxError,
		beforeSend: ajaxBeforeSend,
	    complete: ajaxComplete
	});
	
	setMyword(); //검색어 쿠키 저장
}

function goToPage(tab, page_num){
	if(tab == 1){
		
		tab_status = 1;
		pageOfRoute = page_num;
		if(selectSecFlag == 1) //통합검색
			searchTotal(1,searchGubun);
		else if(selectSecFlag == 2) //경로검색
			roadSearchStartEnd(1, startEndStatus);
	}else if(tab == 2){
		tab_status = 2;
		pageOfBus = page_num;
		if(selectSecFlag == 1) //통합검색
			searchTotal(1);
		else if(selectSecFlag == 2) //경로검색
			roadSearchStartEnd(1, startEndStatus);
	}else if(tab == 3){
		tab_status = 3;
		pageOfSubway = page_num;
		if(selectSecFlag == 1) //통합검색
			searchTotal(1);
		else if(selectSecFlag == 2) //경로검색
			roadSearchStartEnd(1, startEndStatus);
	}else if(tab == 4){
		tab_status = 4;
		pageOfPOI = page_num;
		if(selectSecFlag == 1) //통합검색
			searchTotal(1);
		else if(selectSecFlag == 2) //경로검색
			roadSearchStartEnd(1, startEndStatus);
	}
}


function resetSearch(){
	//기존 마커 삭제
	routeMarkerLayer.clearMarkers();
	poiMarkerLayer.clearMarkers();
	stationMarkerLayer.clearMarkers();
	subwayMarkerLayer.clearMarkers();
	upRouteMarkerLayer.clearMarkers();
	downRouteMarkerLayer.clearMarkers();
	upRealBusRouteMarkerLayer.clearMarkers();
	downRealBusRouteMarkerLayer.clearMarkers();
	upRealBusRouteLowMarkerLayer.clearMarkers();
	downRealBusRouteLowMarkerLayer.clearMarkers();
	startMarkers.clearMarkers();
	endMarkers.clearMarkers();
	//기존 경로 삭제
	if(up_line_layer != null) up_line_layer.destroyFeatures();
	if(down_line_layer != null) down_line_layer.destroyFeatures();
	
	//다중노선 초기화
	resetMultiRoute();
	
	//열려있는 툴팁 있을 시 툴팁 닫기
	if(crPopup) tooltipClose();
}

function searchTotalSuccess(data){

	gunbunVal = "main";
	
	dataTmp=data;
	
	jQuery("#busLoading").hide();
	
	if(data.success){
		
		$("#search_main1").hide();
		$("#search_main1_1").hide();
		$("#mainInfo").hide();
		$("#search_result1").show();
		$("#roadSearchResult").show();
		
		//검색 결과 리셋
		resetSearch();
		
		//스크롤 상단으로 이동
		$( ".list_cmn" ).scrollTop(0);
		
		var resultPoi = data.result.poi;
		var resultBusRoute = data.result.busRoute;
		var resultBusStation = data.result.busStation;
		var resultSubwayStation = data.result.subwayStation;
		
		var poiCnt = resultPoi.count;
		var busRouteCnt = resultBusRoute.totalCount;
		var busStationCnt = resultBusStation.totalCount;
		var subwayStationCnt = resultSubwayStation.count;
		
		var poiTotalCnt = resultPoi.totalCount;
		var busTotalRouteCnt = resultBusRoute.totalCount;
		var busTotalStationCnt = resultBusStation.totalCount;
		var subwayTotalStationCnt = resultSubwayStation.totalCount;
		var busType= resultBusRoute.busType;
		
		var list_place = "";
		var list_station = "";
		var list_bus = "";
		var list_subway = "";
		
		var routeId_t = "";
		var siFlag_t = "";
		var routeTp_t = "";
		
		//poi 검색결과
		if(poiCnt > 0){
			$.each(resultPoi.list,function(i){
				var poiNm = resultPoi.list[i].poiNm;
				var poiId = resultPoi.list[i].poiId;
				var poiSeq = resultPoi.list[i].poiSeq;
				var poiLon = resultPoi.list[i].lon;
				var poiLat = resultPoi.list[i].lat;
				//var poiTelNo = resultPoi.list[i].poiTelNo;
				var poiTelNo = (resultPoi.list[i].poiTelNo != "") ? resultPoi.list[i].poiTelNo : '전화번호 정보 없음';
				var poiAddrName = resultPoi.list[i].poiAddrName;
				var poiBizName = resultPoi.list[i].poiBizName;
				var poiUpperBizName = resultPoi.list[i].poiUpperBizName;
				var poiMiddleBizName = resultPoi.list[i].poiMiddleBizName;
				
				list_place += '<a id="list_place_'+i+'" href="JavaScript: getPoiMap(\''+i+'\',\''+poiLon+'\',\''+poiLat+'\');focusPlacePopup('+i+')" title="'+poiNm+' 위치를 지도위 팝업으로 표시">';
				list_place += 	'<span class="sound_only">장소 검색결과</span>';
				list_place += 	'<li class="wa_list">';
				list_place += 		'<span class="ico">';
				list_place += 			'<img src="/gbis2014/images/ico/number/circle'+(i+1)+'.png" alt="'+(i+1)+'" />';
				list_place += 		'</span>';
				list_place += 		'<div class="wa_list_sub">';
				list_place += 			'<strong style="font-family:\'S-Core\';font-size:16px;font-weight:500;color:#222121;">'+poiNm+'</strong>';
				list_place += 			'<p style="font:normal 13px S-Core;font-weight:400px;">'+poiAddrName+'</p>';
				list_place += 		'</div>';
				list_place += 	'</li>';
				list_place += '</a>';
	
				var size = new Tmap.Size(20, 20);
				var offset = new Tmap.Pixel(-(size.w / 2), -size.h);
				var iconHtml = new Tmap.IconHtml('<div class="poi'+i+'"><img src="/gbis2014/images/ico/number/circle'+(i+1)+'.png" alt="'+(i+1)+'" /></div>',size,offset);
				poiMarker = new Tmap.Marker(new Tmap.LonLat(poiLon, poiLat), iconHtml);
				
				// 마커 레이어 생성
				map.addLayer(poiMarkerLayer);
				
				// 마커 생성
				poiMarkerLayer.addMarker(poiMarker);
	
				//팝업 생성
				/****************************************************************************************************
				 * Tmap.Popup.Anchored offset 처리 방식
				 * tl : popup.anchor.offset.x - popup.size.w / popup.anchor.offset.y - popup.size.h
				 * tr : popup.anchor.offset.x + popup.anchor.size.w /  popup.anchor.offset.y - popup.size.h
				 * bl : popup.anchor.offset.x - popup.size.w/ popup.anchor.offset.y + popup.anchor.size.h
				 * br : popup.anchor.offset.x + popup.anchor.size.w / popup.anchor.offset.y + popup.anchor.size.h
				 ****************************************************************************************************/
				poiObj[i] = poiMarker;
				var sizeW = 380;
				var alonlat = new Tmap.LonLat(poiLon, poiLat);
				var aSize = new Tmap.Size(10, 20);
				var aOffset = new Tmap.Pixel(-(size.w / 2), -size.h);
				var anchorObj = {
					size : aSize,
					offset : aOffset
				};
				var cSize = new Tmap.Size(sizeW, 183);
				//poi검색결과
				var label = '<div class="tooltip_place" id="pop_id_'+i+'"><!--poi검색결과 지도위 팝업-->';
				
				label += '<h1><a href="javascript:busStationView(\''+poiId+'\',\''+poiNm+'\');" title="장소명 통합검색 결과 새 창으로 보기">'+poiNm+'<span class="crNm" style="display:none">'+poiNm+'</span></a></h1>';
				label += '<div class="tooltip_content">';
				label += '<div class="inner">';
				label += poiTelNo+' <span class="mline">|</span> '+poiMiddleBizName+'<br />';
				label += poiAddrName;
				label += '</div>';
				label += '</div>';
				label += '<div class="tooltip_btn">';
				label += '<button type="button" onclick="btnStartFlag();" id="roadStart" class="w_btn start"><span>출발</span></button>\n';
				label += '<button type="button" onclick="btnEndFlag()" id="roadEnd" class="w_btn end"><span>도착</span></button>';
				label += '</div>';
				label += '<a class="close" id="close_id_'+i+'"  title="장소 정보 창 닫기"  href="javascript:tooltipClose();focusBackToPlaceList('+i+');"><i class="fa fa-times" aria-hidden="true"></i></a>';
				label += '<div class="tooltip_arrow_place"></div>';														 //focusBackToList('+i+');">
				label += '</div>';
				
				poiMarker.popup = new Tmap.Popup.Anchored("customLabel", alonlat, cSize, label, anchorObj, false);
				poiMarker.popup.relativePosition = 'tr';
	
				poiMarker.popup.updateRelativePosition();
				poiMarker.popup.calculateRelativePosition = function(px) {
					return poiMarker.popup.relativePosition;
				};
				poiMarker.popup.panMapIfOutOfView = false;
				poiMarker.popup.keepInMap = false;
				
				//팝업 스타일링 부분
				poiMarker.popup.contentDiv.style.overflow = "hidden";
				poiMarker.popup.contentDiv.style.padding = "0px 0px 30px 0px";
				poiMarker.popup.setBackgroundColor("transparent");
				/*
				map.addPopup(poiMarker.popup);
				var pContentDivW = jQuery(poiMarker.popup.contentDiv).find('div').width();
				poiMarker.popup.anchor.offset.x = poiMarker.popup.anchor.offset.x - (pContentDivW / 2);
				poiMarker.popup.hide();
				*/
				$(poiMarker.icon.imageDiv).find('div').css('cursor', 'pointer'); //마커 오버 시 스타일
				
				poiMarker.events.register('click', poiObj[i], onMarkerClick);
				poiMarker.events.register('mouseover', poiObj[i], onMouseMarker);
				poiMarker.events.register('mouseout', poiObj[i], outMouseMarker);
				poiMarker.popup.events.register('mouseover',poiMarker, onMousePopup);
				poiMarker.popup.events.register('mouseout',poiMarker, outMousePopup);
				
	    	});
			
			//페이징 삽입
			list_place += '<li class="paginate_wrap">';
			list_place += '<div class="paginate" id="pageDiv_place">';
			list_place += '</div>';
			list_place += '</li>';
			
			poiMarkerLayer.setVisibility(false);
		}else{
			list_place += "<li class='cannot_find'>";
			list_place += "검색 결과가 없습니다.";
			list_place += "</li>";
		}
		//busStation 검색결과
		stationIdArr.length = 0; //검색결과 정류소ID 초기화
		if(busStationCnt > 0){
			$.each(resultBusStation.list,function(i){
				
				var stationNo = resultBusStation.list[i].stationNo;
				var stationNo_ = resultBusStation.list[i].stationNo;
				var stationNm = resultBusStation.list[i].stationNm;
				var stationNmOrg = resultBusStation.list[i].stationNm;
				var toolStationNm = resultBusStation.list[i].stationNm;
				if(stationNm.length > 15) stationNm = stationNm.substring(0,15)+"...";				
				toolStationNm  = (toolStationNm .length > 15) ? toolStationNm .substring(0,15)+'...' : toolStationNm;
				var stationSeq = resultBusStation.list[i].stationSeq;
				var stationId = resultBusStation.list[i].stationId;
				var stationLon = resultBusStation.list[i].lon;
				var stationLat = resultBusStation.list[i].lat;
				var districtGnm = resultBusStation.list[i].districtGnm;
				var stationNoSi = resultBusStation.list[i].stationNoSi;
				var centerYn = resultBusStation.list[i].centerYn;
				
				//서울,인천 번호 있을 시 서울,인천 번호로 표출
				if(stationNoSi) stationNo = stationNoSi;
				
				
				//stationNoSi가 0일 경우 stationNo_로 표출
				if(stationNoSi == "00000") stationNo = stationNo_;
				
				//검색결과 정류소ID 저장
				stationIdArr.push(stationId);
				
				//list_station += '<a href="JavaScript: getStationMap(\''+i+'\',\''+stationLon+'\',\''+stationLat+'\');searchPopStation(\''+stationNmOrg+'\',\''+stationNo+'\')">';
				//list_station += '<a href="JavaScript: getStationMap(\''+i+'\',\''+stationLon+'\',\''+stationLat+'\');">';
				//list_station += '<a id="list_station_'+i+'" href="JavaScript: getStationMap(\''+i+'\',\''+stationLon+'\',\''+stationLat+'\');focusStationPopup('+i+')" title="'+stationNm+'정류소 도착정보 지도위 팝업으로 표시">';
				list_station += '<a id="list_station_'+i+'" href="JavaScript: getStationMap(\''+i+'\',\''+stationLon+'\',\''+stationLat+'\'); searchPopStation(\''+stationNmOrg+'\',\''+stationNo+'\'); focusStationPopup('+i+')" title="'+stationNm+'정류소 도착정보 지도위 팝업으로 표시">';
				list_station += 	'<span class="sound_only">정류소 검색결과</span>';
				list_station += 	'<li class="wa_list">';
				list_station += 		'<span class="ico">';
				list_station += 			'<img src="/gbis2014/images/ico/number/circle'+(i+1)+'.png" alt="'+(i+1)+'" />';
				list_station += 		'</span>';
				list_station += 		'<div class="wa_list_sub">';
				list_station += 			'<strong style="font-family:\'S-Core\';font-size:16px;font-weight:500;color:#222121;">'+stationNm+' ['+districtGnm+']</strong>';
				list_station += 			'<p style="font-family:\'S-Core\';">'+stationNo+'</p>';
				list_station += 		'</div>';
				list_station += 	'</li>';
				list_station += '</a>';
				
				var size = new Tmap.Size(20, 20);
				var offset = new Tmap.Pixel(-(size.w / 2), -size.h);
				//중앙차로 여부
				var iconHtml;
				iconHtml = new Tmap.IconHtml('<div class="icon_wa line station'+i+'"><img src="/gbis2014/images/ico/common/station1.png" alt="'+(i+1)+'" /></div>',size,offset);
				stationMarker = new Tmap.Marker(new Tmap.LonLat(stationLon, stationLat), iconHtml);
				// 마커 레이어 생성
				map.addLayer(stationMarkerLayer);
	
				// 마커 생성
				stationMarkerLayer.addMarker(stationMarker);
	
				//팝업 생성
				/****************************************************************************************************
				 * Tmap.Popup.Anchored offset 처리 방식
				 * tl : popup.anchor.offset.x - popup.size.w / popup.anchor.offset.y - popup.size.h
				 * tr : popup.anchor.offset.x + popup.anchor.size.w /  popup.anchor.offset.y - popup.size.h
				 * bl : popup.anchor.offset.x - popup.size.w/ popup.anchor.offset.y + popup.anchor.size.h
				 * br : popup.anchor.offset.x + popup.anchor.size.w / popup.anchor.offset.y + popup.anchor.size.h
				 ****************************************************************************************************/
				stationObj[i] = stationMarker;
				var sizeW = 380;
				var alonlat = new Tmap.LonLat(stationLon, stationLat);
				var aSize = new Tmap.Size(10, 20);
				var aOffset = new Tmap.Pixel(-(size.w / 2), -size.h);
				var anchorObj = {
					size : aSize,
					offset : aOffset
				};
				var cSize = new Tmap.Size(sizeW, 400);
				
				var label = '<div class="tooltip" id="pop_id_'+i+'">';
				
				//label += '<h1><a href="javascript:busStationView(\''+stationId+'\',\''+stationNmOrg+'\');" title="'+stationNmOrg+' 정류소 통합검색 결과 새 창으로 보기">'+toolStationNm+' <span class="line">|</span> <span class="station_code" alt="stationNo">'+stationNo+'</span><span class="crNm" style="display:none">'+stationNm+'</span><span class="stationId" style="display:none">'+stationId+'</span></a></h1>';
				label += '<h1>'+toolStationNm+' <span class="line">|</span> <span class="station_code" alt="stationNo">'+stationNo+'</span><span class="crNm" style="display:none">'+stationNm+'</span><span class="stationId" style="display:none">'+stationId+'</span></h1>';
				label += '<div class="tooltip_content">';
				label += '<div class="after_bus">';
				label += '<h2>잠시후 도착버스 <span class="line">|</span></h2>';
				label += '<div id="scroller" class="scroller scroller_'+stationId+'" style="position:relative;margin-left:100px;width:218px;height:31px">';
				label += '<div class="scroller_mask" style="width:210px;height:31px;">';
				label += '<ul class="station_bus_scroll_'+stationId+'">';
				label += '</ul>';
				label += '</div>';
				label += '<ul class="scroller_nav" style="width: 238px;">';
				label += '<li></li>';
				//label += '<a tabindex="0" title="잠시후 도착버스 더보기"  style="width: 15px; height: 15px; right: 0px; top: 8px; background-image: url(/gbis2014/images/location/bg_tooltip.png); background-position: -20px 0px; background-repeat: no-repeat;"></a>';
				label += '</ul>';
				label += '</div>';
				label += '</div>';
				label += '<div class="station_bus_list">';
				label += '<ul class="station_bus_list_'+stationId+'">';
				label += '</ul>';
				label += '</div>';
				label += '</div>';
				label += '<div class="tooltip_btn">';
				label += '<button type="button" onclick="btnStartFlag()" class="w_btn start"><span>출발</span></button>\n';
				label += '<button type="button" onclick="btnEndFlag()" class="w_btn end"><span>도착</span></button>';
				label += '</div>';
				label += '<a class="close" id="close_id_'+i+'"  title="정류소 정보 창 닫기"  href="javascript:tooltipClose();focusBackToStationList('+i+');"><i class="fa fa-times" aria-hidden="true"></i></a>';
				label += '<div class="tooltip_arrow"></div>';
				label += '</div>';
				
				stationMarker.popup = new Tmap.Popup.Anchored("customLabel", alonlat, cSize, label, anchorObj, false);
				stationMarker.popup.relativePosition = 'tr';
	
				stationMarker.popup.updateRelativePosition();
				stationMarker.popup.calculateRelativePosition = function(px) {
					return stationMarker.popup.relativePosition;
				};
				stationMarker.popup.panMapIfOutOfView = false;
				stationMarker.popup.keepInMap = false;
				
				//팝업 스타일링 부분
				stationMarker.popup.contentDiv.style.overflow = "hidden";
				stationMarker.popup.contentDiv.style.padding = "0px 0px 30px 0px";
				stationMarker.popup.setBackgroundColor("transparent");
				/*
				map.addPopup(stationMarker.popup);
				var pContentDivW = jQuery(stationMarker.popup.contentDiv).find('div').width();
				stationMarker.popup.anchor.offset.x = stationMarker.popup.anchor.offset.x - (pContentDivW / 2);
				stationMarker.popup.hide();
				*/
				$(stationMarker.icon.imageDiv).find('div').css('cursor', 'pointer'); //마커 오버 시 스타일
				stationMarker.events.register('click', stationObj[i], onMarkerClick);
				stationMarker.events.register('mouseover', stationObj[i], onMouseMarker);
				stationMarker.events.register('mouseout', stationObj[i], outMouseMarker);
				stationMarker.popup.events.register('mouseover',stationMarker, onMousePopup);
				stationMarker.popup.events.register('mouseout',stationMarker, outMousePopup);
				
				
	    	});
			
			//페이징 삽입
			list_station += '<li class="paginate_wrap">';
			list_station += '<div class="paginate" id="pageDiv_station">';
			list_station += '</div>';
			list_station += '</li>';
			
			stationMarkerLayer.setVisibility(false); //정류장 마커레이어 숨김
		}else{
			list_station += "<li class='cannot_find'>";
			list_station += "검색 결과가 없습니다.";
			list_station += "</li>";
		}
		
		
		//busRoute 검색결과
		if(busRouteCnt > 0){
			
			var className = "";
			var iconTag = '<span style="display:inline-block;width:35px;height:35px;background:#background;border-radius:2px;font-size:13px;font-weight:900;color:#color;text-align:center;line-height:35px;box-shadow:0px 1px 2px rgb(0 0 0 / 10%);margin-right:5px;">#text</span>';
			var iconImg = "";
			
			//라디오버튼//
			list_bus += '<div class="busTypeRadio">';
				
			list_bus += '<label id="metroLab"><input type="radio" value="metro" onClick="javascript:selectSec2(\'metro\')">일반</label>';	
			list_bus += '<label id="wideLab"><input type="radio" value="wideDir"  onClick="javascript:selectSec2(\'wideDir\')">직행좌석</label>'; /*광역ㆍ공항*/
			list_bus += '<label id="townLab"><input type="radio" value="town" onClick="javascript:selectSec2(\'town\')">마을</label>';	
			list_bus += '<label id="outLab"><input type="radio" value="outAir" onClick="javascript:selectSec2(\'outAir\')">시외∙공항</label>';
			list_bus += '</div>';
				
			list_bus += '<li class="btn_multi_new">';
//			list_bus += '<a href="#" class="open" id="showTray">노선도 비교하기</a>';
			list_bus += '<a href="#" class="open" id="showTrayNselectMulti">노선도 비교</a>';
			list_bus += '<a href="javascript:resetMultiRouteDraw()" class="open" id="clearAll">초기화</a>';
			// list_bus += '<a href="javascript:getMultiRoute()" class="view">다중노선 보기</a>';
			// list_bus += '<a href="javascript:resetMultiRoute()" class="reset">초기화</a>';
			list_bus += '</li>';
		
			list_bus += '<div style="max-height:calc(100% - 220px);overflow-y:auto;">';
			//list_bus += '<div style="max-height:calc(100% - 175px);overflow-y:auto;">';
			$.each(resultBusRoute.list,function(i){
				
				var routeRegoin = resultBusRoute.list[i].routeRegoin;
                var routeRegoinTitle = resultBusRoute.list[i].routeRegoin;
                if(routeRegoin.length > 19) routeRegoin = routeRegoin.substring(0,19)+"...";
				var siFlag = resultBusRoute.list[i].siFlag;
				var routeTp = resultBusRoute.list[i].routeTp;
				var routeId = resultBusRoute.list[i].routeId;
				var routeNm = resultBusRoute.list[i].routeNm;
				var startLon = resultBusRoute.list[i].startLon;
				var startLat = resultBusRoute.list[i].startLat;
				var endLon = resultBusRoute.list[i].endLon;
				var endLat = resultBusRoute.list[i].endLat;
				
				//노선번호 색상
				/*
					Route_tp = 11, 21, 14  --> red(직행)
					Route_tp = 12  --> blue
					Route_tp = 30  --> yellow
					Route_tp = 41, 42, 43  --> violet(시외)
					Route_tp = 51, 52, 53  --> grey (공항)
					나머지 --> green
				*/
				if(routeTp == 11 || routeTp == 21 || routeTp == 14 || routeTp == 16){
					className = "num_red";
				}else if(routeTp == 12){
					className = "num_blue";
				}else if(routeTp == 30 ){
					className = "num_yellow";
				}else if(routeTp == 41 || routeTp == 42 || routeTp == 43){
					className = "num_purple";
				}else if(routeTp == 51 || routeTp == 52 || routeTp == 53){
					className = "num_gray";
				}else{
					className = "num_green";
				}
				
				var routeTpNm="";
				//노선 아이콘
				/*
					SI_FLAG = 1 --> 서울
						Route_tp = 51,52, 53  --> 공항버스(seoul.gif, airport.gif)
						Route_tp = 41, 42, 43  --> 시외버스(seoul.gif, si.gif)
						Route_tp = 나머지 --> seoul.gif
					SI_FLAG = 3 --> 인천
						Route_tp = 51,5 2, 53  --> 공항버스(inchon.gif airport.gif)
						Route_tp = 41, 42, 43  --> 시외버스(inchon.gif, si.gif)
						Route_tp = 나머지 --> inchon.gif
					SI_FLAG = 나머지 --> 경기도
						Route_tp = 51,5 2, 53  --> 공항버스(airport.gif)
						Route_tp = 41, 42, 43  --> 시외버스(si.gif)
						Route_tp = 나머지 --> 이미지 없음
				 */
				if(siFlag == 1){ //서울
					if(routeTp == 51 || routeTp == 52 || routeTp == 53){
						routeTpNm="공항";
						iconImg = iconTag.replace("#background","#558ed5").replace("#color","#fff").replace("#text","서울");
						iconImg += iconTag.replace("#background","#6d6d6d").replace("#color","#fff").replace("#text",routeTpNm);
					}else if(routeTp == 41 || routeTp == 42 || routeTp == 43){
						routeTpNm="시외";
						iconImg = iconTag.replace("#background","#558ed5").replace("#color","#fff").replace("#text","서울");
						iconImg += iconTag.replace("#background","#8400ff").replace("#color","#fff").replace("#text",routeTpNm);
					}else if(routeTp == 11 || routeTp == 21 || routeTp == 16){
						routeTpNm="직좌";
						iconImg = iconTag.replace("#background","#558ed5").replace("#color","#fff").replace("#text","서울");
						iconImg += iconTag.replace("#background","#ff0000").replace("#color","#fff").replace("#text",routeTpNm);
					}else if(routeTp == 14){
						routeTpNm="광역";
						iconImg = iconTag.replace("#background","#558ed5").replace("#color","#fff").replace("#text","서울");
						iconImg += iconTag.replace("#background","#ff0000").replace("#color","#fff").replace("#text",routeTpNm);
					}else if(routeTp == 12 ){
						routeTpNm="좌석";
						iconImg = iconTag.replace("#background","#558ed5").replace("#color","#fff").replace("#text","서울");
						iconImg += iconTag.replace("#background","#0000ff").replace("#color","#fff").replace("#text",routeTpNm);
					}else if(routeTp == 30){
						routeTpNm="마을";
						iconImg = iconTag.replace("#background","#558ed5").replace("#color","#fff").replace("#text","서울");
						iconImg += iconTag.replace("#background","#efe600").replace("#color","#000").replace("#text",routeTpNm);
					}else{
						routeTpNm="일반";
						iconImg = iconTag.replace("#background","#558ed5").replace("#color","#fff").replace("#text","서울");
						iconImg += iconTag.replace("#background","#0b7240").replace("#color","#fff").replace("#text",routeTpNm);
					}
				}else if(siFlag == 3){ //인천
					if(routeTp == 51 || routeTp == 52 || routeTp == 53){
						routeTpNm="공항";
						iconImg = iconTag.replace("#background","#0b7204").replace("#color","#fff").replace("#text","인천");
						iconImg += iconTag.replace("#background","#6d6d6d").replace("#color","#fff").replace("#text",routeTpNm);
					}else if(routeTp == 41 || routeTp == 42 || routeTp == 43){
						routeTpNm="시외";
						iconImg = iconTag.replace("#background","#0b7204").replace("#color","#fff").replace("#text","인천");
						iconImg += iconTag.replace("#background","#8400ff").replace("#color","#fff").replace("#text",routeTpNm);
					}else if(routeTp == 11 || routeTp == 21 || routeTp == 16){
						routeTpNm="직좌";
						iconImg = iconTag.replace("#background","#0b7204").replace("#color","#fff").replace("#text","인천");
						iconImg += iconTag.replace("#background","#ff0000").replace("#color","#fff").replace("#text",routeTpNm);
					}else if(routeTp == 14){
						routeTpNm="광역";
						iconImg = iconTag.replace("#background","#0b7204").replace("#color","#fff").replace("#text","인천");
						iconImg += iconTag.replace("#background","#ff0000").replace("#color","#fff").replace("#text",routeTpNm);
					}else if(routeTp == 12 ){
						routeTpNm="좌석";
						iconImg = iconTag.replace("#background","#0b7204").replace("#color","#fff").replace("#text","인천");
						iconImg += iconTag.replace("#background","#0000ff").replace("#color","#fff").replace("#text",routeTpNm);
					}else if(routeTp == 30){
						routeTpNm="마을";
						iconImg = iconTag.replace("#background","#0b7204").replace("#color","#fff").replace("#text","인천");
						iconImg += iconTag.replace("#background","#efe600").replace("#color","#000").replace("#text",routeTpNm);
					}else{
						routeTpNm="일반";
						iconImg = iconTag.replace("#background","#0b7204").replace("#color","#fff").replace("#text","인천");
						iconImg += iconTag.replace("#background","#0b7240").replace("#color","#fff").replace("#text",routeTpNm);
					}
				}else{//경기도
					if(routeTp == 51 || routeTp == 52 || routeTp == 53){
						routeTpNm="공항";
						iconImg = iconTag.replace("#background","#6d6d6d").replace("#color","#fff").replace("#text",routeTpNm);
					}else if(routeTp == 41 || routeTp == 42 || routeTp == 43){
						routeTpNm="시외";
						iconImg = iconTag.replace("#background","#8400ff").replace("#color","#fff").replace("#text",routeTpNm);
					}else if(routeTp == 11 || routeTp == 21 || routeTp == 16){
						routeTpNm="직좌";
						iconImg = iconTag.replace("#background","#ff0000").replace("#color","#fff").replace("#text",routeTpNm);
					}else if(routeTp == 14){
						routeTpNm="광역";
						iconImg = iconTag.replace("#background","#ff0000").replace("#color","#fff").replace("#text",routeTpNm);
					}else if(routeTp == 12 ){
						routeTpNm="좌석";
						iconImg = iconTag.replace("#background","#0000ff").replace("#color","#fff").replace("#text",routeTpNm);
					}else if (routeTp == 30){
						routeTpNm="마을";
						iconImg = iconTag.replace("#background","#efe600").replace("#color","#000").replace("#text",routeTpNm);
					}else{
						routeTpNm="일반";
						iconImg = iconTag.replace("#background","#0b7240").replace("#color","#fff").replace("#text",routeTpNm);
					}
				}
				//DRT 노선 클릭시 셔클 홈페이지로 이동
				if(routeNm.includes('DRT')){
					list_bus += '<li style="cursor:pointer;width: 369px; border-top: 1px solid #e1e1e1;">';
					list_bus += '<a class="list_bus" id="list_route_'+routeId+'" style="display:inline-block;margin:0px 14px;padding:10px 0px;" href="http://www.shucle.com" target="_blank"  title="클릭시 셔클 홈페이지로 이동합니다" >';
					list_bus += '<span class="sound_only">버스 검색결과</span>';
					list_bus += iconImg+'<strong class="'+className+'" style="font-family:\'S-Core\';vertical-align:middle;font-size:15px;margin-right:10px;">'+routeNm+'</strong>';
					list_bus += '<p style="display:inline;font-weight:500;vertical-align:middle;">'+routeRegoin+'  [셔클 홈페이지]</p>';
					list_bus += '</a>';
					list_bus += '<div class="chk" style="display:none;margin-top:15px;" onclick="event.cancelBubble = true;"><button class="multiCheck" type="button" name="'+routeId+'" title="'+routeTpNm+' '+routeNm+' '+routeRegoinTitle+'">선택</button></div>';
					list_bus += '</li>';
				}else{
					list_bus += '<li style="cursor:pointer;width: 369px; border-top: 1px solid #e1e1e1;">';
					list_bus += '<a class="list_bus" id="list_route_'+routeId+'" style="display:inline-block;margin:0px 14px;padding:10px 0px;" href="javaScript: getRouteDetail(\''+routeId+'\',\''+routeNm+'\',\''+siFlag+'\',\''+routeTp+'\');focusRoutePopup('+routeId+')" title="'+routeNm+ routeRegoinTitle +'노선 상세정보 팝업 열림" >';
					list_bus += '<span class="sound_only">버스 검색결과</span>';
					list_bus += iconImg+'<strong class="'+className+'" style="font-family:\'S-Core\';vertical-align:middle;font-size:15px;margin-right:10px;">'+routeNm+'</strong>';
					list_bus += '<p style="display:inline;font-weight:500;vertical-align:middle;">'+routeRegoin+'</p>';
					list_bus += '</a>';
					list_bus += '<div class="chk" style="display:none;margin-top:15px;" onclick="event.cancelBubble = true;"><button class="multiCheck" type="button" name="'+routeId+'" title="'+routeTpNm+' '+routeNm+' '+routeRegoinTitle+'">선택</button></div>';
					list_bus += '</li>';
				}
				
				
				
				
				var size = new Tmap.Size(20, 20);
				var offset = new Tmap.Pixel(-(size.w / 2), -size.h);
				var iconHtml = new Tmap.IconHtml('<div class="route'+(i+1)+'"><img src="/gbis2014/images/ico/number/circle'+(i+1)+'.png" alt="'+(i+1)+'" /></div>',size,offset);
				routeMarker = new Tmap.Marker(new Tmap.LonLat(startLon, startLat), iconHtml);
				
				// 마커 레이어 생성
				map.addLayer(routeMarkerLayer);
	
				// 마커 생성
				routeMarkerLayer.addMarker(routeMarker);
				routeObj[i] = routeMarker;
				routeMarkerLayer.setVisibility(false);
				routeMarker.events.register('mouseover', routeObj[i], onMouseMarker);
				routeMarker.events.register('mouseout', routeObj[i], outMouseMarker);
				
				
				if(mainSearchTxt == routeNm){
					routeId_t = routeId;
					siFlag_t = siFlag;
					routeTp_t = routeTp;
				}
	    	});
			list_bus += '</div>';
			
			//페이징 삽입
			list_bus += '<li class="paginate_wrap" style="border-top:1px solid #e1e1e1;margin:0px 14px;padding;padding:15px 0 0px !important;">';
			list_bus += '<div class="paginate" id="pageDiv_bus">';
			list_bus += '</div>';
			list_bus += '</li>';
				
				
				/*if(gunbunVal == "excelBusInfo"){
					getRouteDetail(routeId_t, mainSearchTxt, siFlag_t, routeTp_t);
			}*/
				
		}else{
			if(busType=='' || busType==null || busType=="모든노선"){
//			if(busType!='metro' && busType!='town' && busType!="wideDirAir" && busType!="out"){
				list_bus += "<li class='cannot_find'>";
				list_bus += "검색 결과가 없습니다.";
				list_bus += "</li>";
			} else {
				list_bus += "<li class='cannot_find'>";
				list_bus += "검색 결과가 없습니다.";
				list_bus += "</li>";
			}
			
		}
		
		
		
		
		
		//subwayStation 검색결과
		if(subwayStationCnt > 0){
			
			$.each(resultSubwayStation.list,function(i){
				
				var subwaySeq = resultSubwayStation.list[i].subwaySeq;
				//var subwayNum = resultSubwayStation.list[i].subwayNum;
				var stationNm = resultSubwayStation.list[i].poiNm;
				var stationStart01 = stationNm.indexOf("[")+1;
				var stationStart02 = stationNm.indexOf("]");
				var stationNm_c = stationNm.indexOf("역");
				var subwayString = stationNm.substring(stationStart01, stationStart02);
				var stationName_c = stationNm.substring(0, stationNm_c);
				
				var subwayImg = "";
				var subwayNum = '';
                var subColor = '';
				if(subwayString.indexOf('인천') != -1){
					if(subwayString.indexOf('1호선') != -1){
						subwayImg = '101';
					}else if(subwayString.indexOf('2호선') != -1){
						subwayImg = '111';
					}else if(subwayString.indexOf('자기부상') != -1){
						subwayImg = '114';
					}					
				}else if(subwayString.indexOf('분당선') != -1){
					subwayImg = '102';
				}else if(subwayString.indexOf('신분당선') != -1){
					subwayImg = '103';
				}else if(subwayString.indexOf('지하철중앙선') != -1){
					subwayImg = '104';
				}else if(subwayString.indexOf('경의중앙') != -1){
					subwayImg = '104';
//				}else if(subwayString.indexOf('지하철경의선') != -1){ 
//					subwayImg = '105';
				}else if(subwayString.indexOf('지하철경춘선') != -1){
					subwayImg = '106';
				}else if(subwayString.indexOf('용인경전철') != -1){
					subwayImg = '107';
				}else if(subwayString.indexOf('공항철도') != -1){
					subwayImg = '108';
				}else if(subwayString.indexOf('수인선') != -1){
					subwayImg = '109';
				}else if(subwayString.indexOf('의정부경전철') != -1){
					subwayImg = '110';
				}else if(subwayString.indexOf('경강선') != -1){
					subwayImg = '112';
				}else if(subwayString.indexOf('우이신설') != -1){
					subwayImg = '113';
				}else if(subwayString.indexOf('자기부상') != -1){
					subwayImg = '114';				
				}else{
					subwayNum = subwayString.substring(0, 1);
					subwayImg = subwayNum;
				}
			
				
				var poiId = resultSubwayStation.list[i].poiId;
				var subwayLon = resultSubwayStation.list[i].lon;
				var subwayLat = resultSubwayStation.list[i].lat;
				var subwayAddr = resultSubwayStation.list[i].poiAddrName;
				var subwayNm = resultSubwayStation.list[i].poiNm;

                
                if(subwayString.indexOf('수인분당') != -1){
                    subColor = 'sub000';
                }else if(subwayString.indexOf('에버라인') != -1){  
                    subColor = 'sub011';
                }else if(subwayString.indexOf('인천1호선') != -1){   // 인천1호선 먼저 
                    subColor = 'sub012';	
                }else if(subwayString.indexOf('인천2호선') != -1){    // 인천2호선 먼저
                    subColor = 'sub013';
                }else if(subwayString.indexOf('경의중앙선') != -1){
                    subColor = 'sub014';	
                }else if(subwayString.indexOf('우이신설선') != -1){
                    subColor = 'sub015';
                }else if(subwayString.indexOf('김포골드라인') != -1){
                    subColor = 'sub016';	
                }else if(subwayString.indexOf('공항철도') != -1){
                    subColor = 'sub020';
                }else if(subwayString.indexOf('신분당선') != -1){
                    subColor = 'sub022';	
                }else if(subwayString.indexOf('경춘선') != -1){
                    subColor = 'sub023';
                }else if(subwayString.indexOf('의정부경전철') != -1){
                    subColor = 'sub024';	
                }else if(subwayString.indexOf('경강선') != -1){
                    subColor = 'sub025';
                }else if(subwayString.indexOf('서해선') != -1){
                    subColor = 'sub026';
                }else if(subwayString.indexOf('신림선') != -1){
                    subColor = 'sub027';
                }else if(subwayString.indexOf('동해선') != -1){
                    subColor = 'sub028';
                }else if(subwayString.indexOf('자기부상') != -1){
                    subColor = 'sub029';
                }else if(subwayString.indexOf('1호선') != -1){
                    subColor = 'sub001';
                }else if(subwayString.indexOf('2호선') != -1){
                    subColor = 'sub002';
                }else if(subwayString.indexOf('3호선') != -1){
                    subColor = 'sub003';
                }else if(subwayString.indexOf('4호선') != -1){
                    subColor = 'sub004';
                }else if(subwayString.indexOf('5호선') != -1){
                    subColor = 'sub005';
                }else if(subwayString.indexOf('6호선') != -1){
                    subColor = 'sub006';
                }else if(subwayString.indexOf('7호선') != -1){
                    subColor = 'sub007';
                }else if(subwayString.indexOf('8호선') != -1){
                    subColor = 'sub008';
                }else if(subwayString.indexOf('9호선') != -1){
                    subColor = 'sub009';
                }else {
                    subColor = 'sub100';   //default
                }


				
				
					list_subway += '<a id="list_subway_'+i+'" href="JavaScript: getSubwayMap(\''+i+'\',\''+subwayLon+'\',\''+subwayLat+'\');focusSubwayPopup('+i+')" title="'+subwayNm+' 위치를 지도위 팝업으로 표시">';
					list_subway += 		'<span class="sound_only">지하철 검색결과</span>';
					list_subway += 		'<li class="wa_list">';
					list_subway += 			'<span class="ico">';
					list_subway += 				'<img src="/gbis2014/images/ico/number/circle'+(i+1)+'.png" alt="'+(i+1)+'" />';
					list_subway += 			'</span>';
					list_subway += 			'<div class="wa_list_sub">';
					list_subway += 				'<div class="wa_lis_sub_02">';
                    list_subway += 					'<span class="sub_icon '+subColor+'">'+subwayString+'</span>';
					list_subway += 					'<strong style="font-family:\'S-Core\';font-size:16px;font-weight:500;color:#222121;vertical-align:top;line-height:5px;margin-left:10px;">'+subwayNm.substring(0,15)+'</strong>';
					list_subway += 				'</div>';
					list_subway += 			'</div>';
					list_subway += 		'</li>';
					list_subway += '</a>';
					
				
				var size = new Tmap.Size(20, 20);
				var offset = new Tmap.Pixel(-(size.w / 2), -size.h);
				var iconHtml = new Tmap.IconHtml('<div class="subway'+i+'"><img src="/gbis2014/images/ico/number/circle'+(i+1)+'.png" alt="'+(i+1)+'" /></div>',size,offset);
				subwayMarker = new Tmap.Marker(new Tmap.LonLat(subwayLon, subwayLat), iconHtml);
				
				// 마커 레이어 생성
				map.addLayer(subwayMarkerLayer);
	
				// 마커 생성
				subwayMarkerLayer.addMarker(subwayMarker);
	
				//팝업 생성
				/****************************************************************************************************
				 * Tmap.Popup.Anchored offset 처리 방식
				 * tl : popup.anchor.offset.x - popup.size.w / popup.anchor.offset.y - popup.size.h
				 * tr : popup.anchor.offset.x + popup.anchor.size.w /  popup.anchor.offset.y - popup.size.h
				 * bl : popup.anchor.offset.x - popup.size.w/ popup.anchor.offset.y + popup.anchor.size.h
				 * br : popup.anchor.offset.x + popup.anchor.size.w / popup.anchor.offset.y + popup.anchor.size.h
				 ****************************************************************************************************/
				subwayObj[i] = subwayMarker;
				var sizeW = 380;
				var alonlat = new Tmap.LonLat(subwayLon, subwayLat);
				var aSize = new Tmap.Size(10, 20);
				var aOffset = new Tmap.Pixel(-(size.w / 2), -size.h);
				var anchorObj = {
					size : aSize,
					offset : aOffset
				};
				var cSize = new Tmap.Size(sizeW, 164);
				
				var label = '<div class="tooltip_subway" id="pop_id_'+i+'"><!--지하철 검색결과 지도위 팝업-->';
			  //label += '<h1>																					<a href="javascript:busStationView(\''+poiId+'\',\''+poiNm+'\');" title="장소명 통합검색 결과 새 창으로 보기">'+poiNm+'<span class="crNm" style="display:none">'+poiNm+'</span></a></h1>';
				label += '<h1 tabindex="0"><span class="sub_icon '+subColor+'">'+subwayString+'</span><span class="crNm">'+subwayNm+'</span></h1>';
				label += '<div class="tooltip_content">';
				label += '<div class="inner">';
				label += subwayAddr;
				label += '</div>';
				label += '</div>';
				label += '<div class="tooltip_btn">';
				/** 지하철 상세정보, 실시간정보 주석처리 **/
				//label += '<div class="btn_clear_left">';
				label += '<button type="button" onclick="btnStartFlag()" class="w_btn start"><span>출발</span></button>\n';
				label += '<button type="button" onclick="btnEndFlag()" class="w_btn end"><span>도착</span></button>';
				label += '</div>';
				label += '<a class="close" id="close_id_'+i+'"  title="지하철 정보 창 닫기"  href="javascript:tooltipClose();focusBackToSubwayList('+i+');"><i class="fa fa-times" aria-hidden="true"></i></a>';
				label += '<div class="tooltip_arrow_subway"></div>';
				label += '</div>';
				
				subwayMarker.popup = new Tmap.Popup.Anchored("customLabel", alonlat, cSize, label, anchorObj, false);
				subwayMarker.popup.relativePosition = 'tr';
	
				subwayMarker.popup.updateRelativePosition();
				subwayMarker.popup.calculateRelativePosition = function(px) {
					return subwayMarker.popup.relativePosition;
				};
				subwayMarker.popup.panMapIfOutOfView = false;
				subwayMarker.popup.keepInMap = false;
				
				//팝업 스타일링 부분
				subwayMarker.popup.contentDiv.style.overflow = "hidden";
				subwayMarker.popup.contentDiv.style.padding = "0px 0px 30px 0px";
				subwayMarker.popup.setBackgroundColor("transparent");
				/*
				map.addPopup(subwayMarker.popup);
				var pContentDivW = jQuery(subwayMarker.popup.contentDiv).find('div').width();
				subwayMarker.popup.anchor.offset.x = subwayMarker.popup.anchor.offset.x - (pContentDivW / 2);
				subwayMarker.popup.hide();
				*/
				$(subwayMarker.icon.imageDiv).find('div').css('cursor', 'pointer'); //마커 오버 시 스타일
				subwayMarker.events.register('click', subwayObj[i], onMarkerClick);
				subwayMarker.events.register('mouseover', subwayObj[i], onMouseMarker);
				subwayMarker.events.register('mouseout', subwayObj[i], outMouseMarker);
				subwayMarker.popup.events.register('mouseover',subwayMarker, onMousePopup);
				subwayMarker.popup.events.register('mouseout',subwayMarker, outMousePopup);
				
	    	});
			
			//페이징 삽입
			list_subway += '<li class="paginate_wrap">';
			list_subway += '<div class="paginate" id ="pageDiv_subway">';
			list_subway += '</div>';
			list_subway += '</li>';
			
			subwayMarkerLayer.setVisibility(false);
		}else{
			list_subway += "<li class='cannot_find'>";
			list_subway += "검색 결과가 없습니다.";
			list_subway += "</li>";
		}
		
		var pageDiv;
		var listSelector, markerSelector;
		
		//장소
		$('.poiCnt').html(poiCnt);
		$('#search_result1 .list_place').html(list_place);
		$('#roadSearchResult .list_place').html(list_place);
		
		listSelector = '#search_result1 .list_place > li';
		markerSelector = '.poi';
		listMarkerMapping(listSelector, markerSelector);
		listSelector = '#roadSearchResult .list_place > li';
		listMarkerMapping(listSelector, markerSelector);
		
		pageDiv = document.getElementById("pageDiv_place");
		makePaging(pageDiv, poiTotalCnt, 10, pageOfPOI, 4);
		
		//정류장
		$('.busStationCnt').html(busStationCnt);
		$('#search_result1 .list_station').html(list_station);
		$('#roadSearchResult .list_station').html(list_station);
		
		listSelector = '#search_result1 .list_station > li';
		markerSelector = '.station';
		listMarkerMapping(listSelector, markerSelector);
		listSelector = '#roadSearchResult .list_station > li';
		listMarkerMapping(listSelector, markerSelector);
		
		pageDiv = document.getElementById("pageDiv_station");
		makePaging(pageDiv, busTotalStationCnt, 10, pageOfBus, 2);
		
		//버스
		// 최정빈 수정
		//if(gunbunVal != "excelBusInfo"){
			$('.busRouteCnt').html(busRouteCnt);
			$('#search_result1 .list_bus').html(list_bus);
			$('#roadSearchResult .list_bus').html(list_bus);
		//}
			
			
		const multiCheck = document.querySelectorAll('.chk > .multiCheck');
		
		for(var i = 0; i < multiCheck.length; i++){
			
			multiCheck[i].addEventListener("click", handleToDoSubmit);
		}	
			
			
		
		listSelector = '#search_result1 .list_bus > li';
		markerSelector = '.route';
		listMarkerMapping(listSelector, markerSelector);
		listSelector = '#roadSearchResult .list_bus > li';
		listMarkerMapping(listSelector, markerSelector);
		
		pageDiv = document.getElementById("pageDiv_bus");
		makePaging(pageDiv, busTotalRouteCnt, 10, pageOfRoute, 1);
		
		//지하철
		$('.subwayStationCnt').html(subwayStationCnt);
		$('#search_result1 .list_subway').html(list_subway);
		$('#roadSearchResult .list_subway').html(list_subway);
		
		listSelector = '#search_result1 .list_subway > li';
		markerSelector = '.subway';
		listMarkerMapping(listSelector, markerSelector);
		listSelector = '#roadSearchResult .list_subway > li';
		listMarkerMapping(listSelector, markerSelector);
		
		pageDiv = document.getElementById("pageDiv_subway");
		makePaging(pageDiv, subwayTotalStationCnt, 10, pageOfSubway, 3);
		listBusEvt();
		
		//다중노선 선택
		$("#selectMulti").toggle(function() {
			$(".chk").show();
		}, function() {
			var chkBox = $(".list_bus li input:checkbox");
			chkBox.attr("checked", false); //체크박스 전체 해제
			$(".chk").hide();
		});

		//노선 비교 선택 클릭 이벤트
		$("#showTrayNselectMulti").toggle(function() {
			$(".chk").show();
			$(".mapct_middle").removeClass("hide").addClass("show");
		}, function() {
			
			$(".mapct_middle").removeClass("show").addClass("hide");
			$(".chk").hide();
		});


		// 노선도 비교하기 닫기버튼
		$("#btnCloseTray").click(function(){
			$(".mapct_middle").removeClass("show").addClass("hide");
		});
		
		
		
		//검색일때만 탭 결정
		if(searchStat == 0){
			if(busRouteCnt > 0){
				tab_status = 1;
			}else if(busStationCnt > 0){
				tab_status = 2;
			}else if(subwayStationCnt > 0){
				tab_status = 3;
			}else if(poiCnt > 0){
				tab_status = 4;
			}else{
				tab_status = 1;
			}
		}
		
		//탭 이동
		if(tab_status == 1){
			selectSec2("bus");
		}else if(tab_status == 2){
			selectSec2("station");
		}else if(tab_status == 3){
			selectSec2("subway");
		}else if(tab_status == 4){
			selectSec2("place");
		}
		
		//페이징 경로검색에 복사
		$("#search_result1 #pageDiv_place").children().clone().appendTo( "#roadSearchResult #pageDiv_place" );
		$("#search_result1 #pageDiv_station").children().clone().appendTo( "#roadSearchResult #pageDiv_station" );
		$("#search_result1 #pageDiv_bus").children().clone().appendTo( "#roadSearchResult #pageDiv_bus" );
		$("#search_result1 #pageDiv_subway").children().clone().appendTo( "#roadSearchResult #pageDiv_subway" );
		
		//리스트 선택시 백그라운드 컬러 적용
		listSelectEvt();
		
		if(busType == "town"){
			$("input:radio:radio[value='town']").attr("checked",true);
			$("#townLab").css('font-weight','bold');
//			$("#townLab").css('color','#EFD200');
		} 
		if(busType== "metro"){
			$("input:radio:radio[value='metro']").attr("checked",true);
			$("#metroLab").css('font-weight','bold');
//			$("#metroLab").css('color','#0b7240');
		} 
		if(busType== "wideDir" || busType== "wide" || busType== "direct" || busType== "air"){
			$("input:radio:radio[value='wideDir']").attr("checked",true);
			document.getElementById("wideLab").style.fontWeight="bold";
//			$("#wideLab").css('color','#ff0000');
			
		}
		if(busType== "outAir"){
			$("input:radio:radio[value='outAir']").attr("checked",true);
			document.getElementById("outLab").style.fontWeight="bold";
//			$("#outLab").css('color','#8400ff');
		}
		
	}else{
		alert("조회 실패");
	}
}

var selectIndex; //선택된 리스트 인덱스
function listMarkerMapping(listSelector,markerSelector){
	
	//통합검색 리스트, 마커 마우스오버 이벤트 매핑
	var thisIndex;
	
	if(markerSelector == '.route'){//버스탭
		$(listSelector).hover(function(){
			thisIndex = $(listSelector).index(this);
			var markerImg = $(markerSelector+thisIndex).find("img").attr("src");
			if(!$(this).hasClass('paginate_wrap') && !$(this).hasClass('btn_multi') && !$(this).hasClass('btn_multi_new') && !$(this).hasClass('cannot_find')) {//페이징, 다중노선 li 제외
				$(markerSelector+thisIndex).find("img").attr("src", markerImg.replace(".png","_on.png"));
			}
		}, function(){
			var markerImg = $(markerSelector+thisIndex).find("img").attr("src");
			if(!$(this).hasClass('paginate_wrap') && !$(this).hasClass('btn_multi') && !$(this).hasClass('btn_multi_new') && !$(this).hasClass('cannot_find')) {//페이징, 다중노선 li 제외
				$(markerSelector+thisIndex).find("img").attr("src", markerImg.replace("_on.png",".png"));
			};
		});
	}else if(markerSelector == '.station'){//정류소탭
		$(listSelector).hover(function(){
			thisIndex = $(listSelector).index(this);
			var markerImg = $(markerSelector+thisIndex).find("img").attr("src");
			if(!$(this).hasClass('paginate_wrap') && !$(this).hasClass('btn_multi') && !$(this).hasClass('btn_multi_new') && !$(this).hasClass('cannot_find')) {//페이징, 다중노선 li 제외
				$(listSelector).eq(thisIndex).find("img").attr("src", $(listSelector).eq(thisIndex).find("img").attr("src").replace(".png","_on.png"));//리스트 아이콘
				if(selectIndex != thisIndex){//선택된 마커 제외
					$(markerSelector+thisIndex).find("img").attr("src", markerImg.replace("station1.png","station5.png"));//지도 마커
				}
			}
		}, function(){
			var markerImg = $(markerSelector+thisIndex).find("img").attr("src");
			if(!$(this).hasClass('paginate_wrap') && !$(this).hasClass('btn_multi') && !$(this).hasClass('btn_multi_new') && !$(this).hasClass('cannot_find')) {//페이징, 다중노선 li 제외
				$(listSelector).eq(thisIndex).find("img").attr("src", $(listSelector).eq(thisIndex).find("img").attr("src").replace("_on.png",".png"));//리스트 아이콘
				if(selectIndex != thisIndex){//선택된 마커 제외
					$(markerSelector+thisIndex).find("img").attr("src", markerImg.replace("station5.png","station1.png"));//지도 마커
				}
			};
		});
		
		$(listSelector).click(function(){//리스트 클릭시 이벤트
			selectIndex = $(listSelector).index(this); //클릭한 인덱스 기억
			var markerImg = $(markerSelector+selectIndex).find("img").attr("src");
			if(!$(this).hasClass('paginate_wrap') && !$(this).hasClass('btn_multi') && !$(this).hasClass('btn_multi_new') && !$(this).hasClass('cannot_find')) {//페이징, 다중노선 li 제외
				for(var i=0;i<=10;i++){//기존 선택 마커 이미지 복구
					$(markerSelector+i).find("img").attr("src", markerImg.replace("station5.png","station1.png"));//지도 마커
				}
				$(markerSelector+selectIndex).find("img").attr("src", markerImg.replace("station1.png","station5.png"));//지도 마커
			}
		});
	}else{
		$(listSelector).hover(function(){
			thisIndex = $(listSelector).index(this);
			var thisImg = $(this).find('.ico img').attr("src");
			var markerImg = $(markerSelector+thisIndex).find("img").attr("src");
			if(!$(this).hasClass('paginate_wrap') && !$(this).hasClass('cannot_find')) {//페이징 li 제외
				$(this).find('.ico img').attr("src", thisImg.replace(".png","_on.png"));
				$(markerSelector+thisIndex).find("img").attr("src", markerImg.replace(".png","_on.png"));
			}
		}, function(){
			var thisImg = $(this).find('.ico img').attr("src");
			var markerImg = $(markerSelector+thisIndex).find("img").attr("src");
			if(!$(this).hasClass('paginate_wrap') && !$(this).hasClass('cannot_find')) {//페이징 li 제외
				$(this).find('.ico img').attr("src", thisImg.replace("_on.png",".png"));
				$(markerSelector+thisIndex).find("img").attr("src", markerImg.replace("_on.png",".png"));
			};
		});
	}
}

function makePaging(pageDiv, totalCount, countPerPage, page_num, tab){
	var pagingObj = new Paging(pageDiv, totalCount, 10, page_num, tab);
    if(pageDiv) pageDiv.innerHTML = pagingObj.getPageString();
}


var routeId_c = '';
var routeNm_c = '';
var siFlag_c = '';
var routeTp_c = '';
function getRouteDetail(routeId, routeNm, siFlag, routeTp) {
	
	// 통합검색  버스선택시 새로고침을 위한 전역변수 입력
	routeId_c = routeId;
	routeNm_c = routeNm;
	siFlag_c = siFlag;
	routeTp_c = routeTp;
	// 끝
	
	//버스마커 있을 시
	if(upRealBusRouteMarkerLayer.markers.length != 0) upRealBusRouteMarkerLayer.clearMarkers();
	if(downRealBusRouteMarkerLayer.markers.length != 0) downRealBusRouteMarkerLayer.clearMarkers();
	if(upRealBusRouteLowMarkerLayer.markers.length != 0) upRealBusRouteLowMarkerLayer.clearMarkers();
	
	
	//버스 마커 숨김
	if(routeMarkerLayer.markers.length != 0) routeMarkerLayer.setVisibility(false);
	
	//다중노선 초기화
	resetMultiRoute();
	
	//열려있는 툴팁 있을 시 툴팁 닫기
	if(crPopup) tooltipClose();
	
	route_name = routeNm;
	route_id = routeId;
	si_flag = siFlag;
	route_tp = routeTp;
	
	var url = "/gbis2014/schBusAPI.action";
	var data = 'cmd=searchMapLineJson';
	data += '&routeId='+routeId;
	
	$.ajax({
		type: "post",
		contentType: "application/x-www-form-urlencoded;charset=UTF-8",
		dataType: "json",
		url: url,
		data: data,
		success: getRouteLineSuccess,
		error: ajaxError,
		beforeSend: ajaxBeforeSend
	});
	
	url = "/gbis2014/schBusAPI.action";
	data = 'cmd=searchRouteJson';
	data += '&routeId='+routeId;
	
	$.ajax({
		type: "post",
		contentType: "application/x-www-form-urlencoded;charset=UTF-8",
		dataType: "json",
		url: url,
		data: data,
		success: getRouteSuccess,
		error: ajaxError
	});
}
var routeNm;
var routeEstimate = [];
var routeSep = "";
var turnSequence = "";
function getRouteSuccess(data) {
	//var timeA = new Date();
	//console.log("시작 : "+timeA);
	routeStationIdArr.length = 0; //검색결과 노선상세 정류소ID 초기화
	
	if(data.success){
		
		
		
		jQuery("#busLoading").hide();
		$(".mapsch_after2").show();
		//$(".mapct_right").css("width", "calc(100% - 760px)"); 
		$(".mapct_left2").show();
		
		var resultEsti = data.result.estimateTime;
		routeSep = data.result.separation[0].sepYN;
		routeEstimate = resultEsti;
		var resultRealTime = data.result.realTime;
		var resultGgRoute = data.result.gg.route;
		var resultGgRoute2 = data.result.gg.route2;
		var resultGgMiddlePnt = data.result.gg.middlePnt;
		var resultGgUp = data.result.gg.up;
		var resultGgDown = data.result.gg.down;
		
		var busTotalCount = resultRealTime.busTotalCount;
		var busCount = resultRealTime.count;
		var ggUpCnt = resultGgUp.count;
		var ggDownCnt = resultGgDown.count;
		
		//상행 리스트 개수 전역 변수 저장
		upListCnt = ggUpCnt;
		
		var bus_info = "";
		var list_realtime = "";
		var list_route_upline = "";
		var list_route_downline = "";
		
		//기반정보 결과
		var stStaNm = "";
		if(resultGgRoute.stStaNm != undefined && resultGgRoute.stStaNm != ''){
			stStaNm = resultGgRoute.stStaNm;
		}
//		if(resultGgUp.list.length > 0 && resultGgUp.list[0].stationTp=='6'){
//			stStaNm = resultGgUp.list[1].stationNm;
//			if(resultGgUp.list[1].stationTp=='6'){
//				stStaNm = resultGgUp.list[2].stationNm;
//			}
//		}

		var lastStaNm = "";
		if(resultGgRoute.lastStaNm != undefined && resultGgRoute.lastStaNm != ''){
			lastStaNm = resultGgRoute.lastStaNm;
		}
		
		var routeId = (resultGgRoute.routeId == undefined || resultGgRoute.routeId == '') ? '' : resultGgRoute.routeId;
		var isRemainSeat = false;
		if(routeId == "249000002"){ // 판타G버스 (자율주행버스) 노선타입 13번 but 빈자리수 표출 하드코딩
			isRemainSeat = true;
		}
		var routeTypeCd = data.result.gg.routeTypeCd;
		if(routeTypeCd==11 || routeTypeCd==12 || routeTypeCd==14 || routeTypeCd==16  || routeTypeCd==21){
			// M6405,M6410,7790급,7800급,3200,3300,1008전,9401,9403,9404,9408,9701,9703,9707,9709,9714,9401공,9714공,9709공차,9711A
			var exRouteIds = "165000215,216000044,200000228,200000229,218000005,219000025,233000129,100100389,100100390,100100391,100100392,100100397,100100398,100100400,100100402,100100406,100100559,100100560,100100577,100100607";
			
			if(exRouteIds.indexOf(routeId)<0){
				isRemainSeat = true;
			}
		}
		
		var maxHead = (resultGgRoute.maxHead == undefined || resultGgRoute.maxHead == '') ? '' : resultGgRoute.maxHead;
		var minHead = (resultGgRoute.minHead == undefined || resultGgRoute.minHead == '') ? '' : resultGgRoute.minHead;
		var companyTel = (resultGgRoute.companyTel == undefined || resultGgRoute.companyTel == '') ? '-' : resultGgRoute.companyTel;
		var adminNm = (resultGgRoute.adminNm == undefined || resultGgRoute.adminNm == '') ? '' : resultGgRoute.adminNm;
		var companyNm = (resultGgRoute.companyNm == undefined || resultGgRoute.companyNm == '') ? '' : resultGgRoute.companyNm;
		routeNm = (resultGgRoute.routeNm == undefined || resultGgRoute.routeNm == '') ? '' : resultGgRoute.routeNm;
		var garageTel = (resultGgRoute.garageTel == undefined || resultGgRoute.garageTel == '') ? '' : resultGgRoute.garageTel;
		var garageNm = (resultGgRoute.garageNm == undefined || resultGgRoute.garageNm == '') ? '' : resultGgRoute.garageNm;
		var turnSeq = (resultGgRoute.turnSeq == undefined || resultGgRoute.turnSeq == '') ? '' : resultGgRoute.turnSeq;
		turnSequence = turnSeq;
		
		var upFirstTime = (resultGgRoute.upFirstTime == undefined || resultGgRoute.upFirstTime == '') ? '' : resultGgRoute.upFirstTime;
		var upLastTime = (resultGgRoute.upLastTime == undefined || resultGgRoute.upLastTime == '') ? '' : resultGgRoute.upLastTime;
		var downFirstTime = (resultGgRoute.downFirstTime == undefined || resultGgRoute.downFirstTime == '') ? '' : resultGgRoute.downFirstTime;
		var downLastTime = (resultGgRoute.downLastTime == undefined || resultGgRoute.downLastTime == '') ? '' : resultGgRoute.downLastTime;
		var peekAlloc = (resultGgRoute.peekAlloc == undefined || resultGgRoute.peekAlloc == '') ? '' : resultGgRoute.peekAlloc;		
		var npeekAlloc = (resultGgRoute.npeekAlloc == undefined || resultGgRoute.npeekAlloc == '') ? '' : resultGgRoute.npeekAlloc;
		var nightAlloc =  (resultGgRoute.nightAlloc == undefined || resultGgRoute.nightAlloc == '') ? '' : resultGgRoute.nightAlloc;
		
		
		var upFirstTime2 = (resultGgRoute.upFirstTime2 == undefined || resultGgRoute.upFirstTime2 == '') ? '' : resultGgRoute.upFirstTime2;
		var upLastTime2 = (resultGgRoute.upLastTime2 == undefined || resultGgRoute.upLastTime2 == '') ? '' : resultGgRoute.upLastTime2;
		var downFirstTime2 = (resultGgRoute.downFirstTime2 == undefined || resultGgRoute.downFirstTime2 == '') ? '' : resultGgRoute.downFirstTime2;
		var downLastTime2 = (resultGgRoute.downLastTime2 == undefined || resultGgRoute.downLastTime2 == '') ? '' : resultGgRoute.downLastTime2;
		var peekAlloc2 = (resultGgRoute.peekAlloc2 == undefined || resultGgRoute.peekAlloc2 == '') ? '' : resultGgRoute.peekAlloc2;
		var npeekAlloc2 = (resultGgRoute.npeekAlloc2 == undefined || resultGgRoute.npeekAlloc2 == '') ? '' : resultGgRoute.npeekAlloc2;
		var nightAlloc2 =  (resultGgRoute.nightAlloc2 == undefined || resultGgRoute.nightAlloc2 == '') ? '' : resultGgRoute.nightAlloc2;
		
		var upFirstTime3 = (resultGgRoute.upFirstTime3 == undefined || resultGgRoute.upFirstTime3 == '') ? '' : resultGgRoute.upFirstTime3;
		var upLastTime3 = (resultGgRoute.upLastTime3 == undefined || resultGgRoute.upLastTime3 == '') ? '' : resultGgRoute.upLastTime3;
		var downFirstTime3 = (resultGgRoute.downFirstTime3 == undefined || resultGgRoute.downFirstTime3 == '') ? '' : resultGgRoute.downFirstTime3;
		var downLastTime3 = (resultGgRoute.downLastTime3 == undefined || resultGgRoute.downLastTime3 == '') ? '' : resultGgRoute.downLastTime3;
		var peekAlloc3 = (resultGgRoute.peekAlloc3 == undefined || resultGgRoute.peekAlloc3 == '') ? '' : resultGgRoute.peekAlloc3;
		var npeekAlloc3 = (resultGgRoute.npeekAlloc3 == undefined || resultGgRoute.npeekAlloc3 == '') ? '' : resultGgRoute.npeekAlloc3;
		var nightAlloc3 =  (resultGgRoute.nightAlloc3 == undefined || resultGgRoute.nightAlloc3 == '') ? '' : resultGgRoute.nightAlloc3;
		
		var upFirstTime4_ = (resultGgRoute.upFirstTime4 == undefined || resultGgRoute.upFirstTime4 == '') ? '' : resultGgRoute.upFirstTime4;
		var upLastTime4_ = (resultGgRoute.upLastTime4 == undefined || resultGgRoute.upLastTime4 == '') ? '' : resultGgRoute.upLastTime4;
		var downFirstTime4_ = (resultGgRoute.downFirstTime4 == undefined || resultGgRoute.downFirstTime4 == '') ? '' : resultGgRoute.downFirstTime4;
		var downLastTime4_ = (resultGgRoute.downLastTime4 == undefined || resultGgRoute.downLastTime4 == '') ? '' : resultGgRoute.downLastTime4;
		var peekAlloc4_ = (resultGgRoute.peekAlloc4 == undefined || resultGgRoute.peekAlloc4 == '') ? '' : resultGgRoute.peekAlloc4;
		var npeekAlloc4_ = (resultGgRoute.npeekAlloc4 == undefined || resultGgRoute.npeekAlloc4 == '') ? '' : resultGgRoute.npeekAlloc4;
		var nightAlloc4_ =  (resultGgRoute.nightAlloc4 == undefined || resultGgRoute.nightAlloc4 == '') ? '' : resultGgRoute.nightAlloc4;
		
		
		var upFirstTime4 = (resultGgRoute.upFirstTime4 == undefined || resultGgRoute.upFirstTime4 == '') ? '' : resultGgRoute.upFirstTime4;
		var upLastTime4 = (resultGgRoute.upLastTime4 == undefined || resultGgRoute.upLastTime4 == '') ? '' : resultGgRoute.upLastTime4;
		var downFirstTime4 = (resultGgRoute.downFirstTime4 == undefined || resultGgRoute.downFirstTime4 == '') ? '' : resultGgRoute.downFirstTime4;
		var downLastTime4 = (resultGgRoute.downLastTime4 == undefined || resultGgRoute.downLastTime4 == '') ? '' : resultGgRoute.downLastTime4;
		var peekAlloc4 = (resultGgRoute.peekAlloc4 == undefined || resultGgRoute.peekAlloc4 == '') ? '' : resultGgRoute.peekAlloc4;
		var npeekAlloc4 = (resultGgRoute.npeekAlloc4 == undefined || resultGgRoute.npeekAlloc4 == '') ? '' : resultGgRoute.npeekAlloc4;
		var nightAlloc4 =  (resultGgRoute.nightAlloc4 == undefined || resultGgRoute.nightAlloc4 == '') ? '' : resultGgRoute.nightAlloc4;
		

		
		// 마을 시외 공항 버스 주중 oper_week = 1 /주말 oper_week = 3  으로 기반 정보가 들어오므로 커스터마이징 
		if(routeTypeCd == 30 || routeTypeCd == 41 || routeTypeCd == 42 || routeTypeCd == 43 || routeTypeCd == 51 || routeTypeCd == 52 || routeTypeCd == 53){
			
			upFirstTime2   =  upFirstTime4_;
			upLastTime2    =  upLastTime4_;
			downFirstTime2 =  downFirstTime4_;
			downLastTime2  =  downLastTime4_;
			peekAlloc2     =  peekAlloc4_;
			npeekAlloc2    =  npeekAlloc4_;
			nightAlloc2    =  nightAlloc4_;

			upFirstTime4   =  upFirstTime4_;
			upLastTime4    =  upLastTime4_;
			downFirstTime4 =  downFirstTime4_;
			downLastTime4  =  downLastTime4_;
			peekAlloc4     =  peekAlloc4_;
			npeekAlloc4    =  npeekAlloc4_;
			nightAlloc4    =  nightAlloc4_;

			upFirstTime3   =  "";
			upLastTime3    =  "";
			downFirstTime3 =  "";
			downLastTime3  =  "";
			peekAlloc3     =  "";
			npeekAlloc3    =  "";
			nightAlloc3    =  "";
		}
			
		var edStaNm = "";
		var edStaNm2 = "";
		if(resultGgRoute.edStaNm != undefined && resultGgRoute.edStaNm != ''){
			edStaNm = resultGgRoute.edStaNm;
			edStaNm2 = resultGgRoute.edStaNm;
		}
		
		
		//실시간 버스 위치
		var realTimePos = [];
		if(resultRealTime.list.length > 0){
			$.each(resultRealTime.list,function(i){
				var busXList = resultRealTime.list[i].busXList;
				var toStationId = resultRealTime.list[i].toStationId;
				var busPosition = resultRealTime.list[i].busPosition;
				var endBusYn = resultRealTime.list[i].endBusYn;
				var toStationSeq = resultRealTime.list[i].toStationSeq;
				var busNo = resultRealTime.list[i].busNo;
				var fromStationSeq = resultRealTime.list[i].fromStationSeq;
				var busYList = resultRealTime.list[i].busYList;
				var busDirList = resultRealTime.list[i].busDirList; //U:상행 D:하행
				var fromStationId = resultRealTime.list[i].fromStationId;
				var lowBusYn = resultRealTime.list[i].lowBusYn;
				var lowPlate = resultRealTime.list[i].lowPlate;
				var vehType = resultRealTime.list[i].vehType; // veh_type : 2층버스 type=4
				var cdmaNo = resultRealTime.list[i].cdmaNo; 
				var busSapceList = resultRealTime.list[i].busSapceList;
				// 이현웅 버스 노선 중 중복되는 버스 flag 추가
				var duplFlag = resultRealTime.list[i].duplFlag;
				var density = resultRealTime.list[i].density; // 혼잡도
				var seatNow = resultRealTime.list[i].seat; // seat빈자리
				var remainSeatCnt1 = "";
				
				realTimePos[i]=[];
				realTimePos[i][0] = toStationId;
				realTimePos[i][1] = fromStationId;
				realTimePos[i][2] = busPosition;
				realTimePos[i][4] = busDirList;
				realTimePos[i][5] = parseInt(busXList);
				realTimePos[i][6] = parseInt(busYList);
				realTimePos[i][7] = lowBusYn;
				realTimePos[i][8] = busNo;
				realTimePos[i][9] = vehType;
				realTimePos[i][10] = lowPlate;
				//realTimePos[i][11] = cdmaNo;
				
				list_realtime = "";
				
				/**정류소 리스트 버스아이콘 생성**/
				list_realtime += '<div class="bus_posi_view" style="top:';
				if(busPosition == '2'){
					list_realtime += '43px';
				}else if(busPosition == '1'){
					list_realtime += '12px';
				}
				list_realtime += ';">';
				
				list_realtime += '<span class="name">'+busNo+'</span>';
				
				
				// 좌측 노선도 차량아이콘 스마트폰과 통일 DKY
				
				switch (routeTypeCd) {
					case '13' :
					case '15' :
					case '23' :  
						if(duplFlag == "Y") {
							list_realtime += '<span class="icon green_double"></span>';
						}else{
							if(lowBusYn== "Y"){
								list_realtime += '<span class="icon green_low"></span>';
							}else if(lowPlate=='2'){
								list_realtime += '<span class="icon green_second"></span>';
							}else if(lowPlate=='7'){
								list_realtime += '<span class="icon green_trolley"></span>';
							}else if(lowPlate=='5'){
								list_realtime += '<span class="icon green_jeonse"></span>';
							}else{
								list_realtime += '<span class="icon green"></span>';
							}
						}
						break;
					case '11' :
					case '14' :
					case '16' :
					case '21' :
						if(duplFlag == "Y") {
							list_realtime += '<span class="icon red_double"></span>';
						}else{
							if(lowBusYn== "Y"){
								list_realtime += '<span class="icon red_low"></span>';
							}else if(lowPlate=='2'){
								list_realtime += '<span class="icon red_second"></span>';
							}else if(lowPlate=='7'){
								list_realtime += '<span class="icon red_trolley"></span>';
							}else if(lowPlate=='5'){
								list_realtime += '<span class="icon red_jeonse"></span>';
							}else{
								list_realtime += '<span class="icon red"></span>';
							}
						}
						break;
					case '12' :
						if(duplFlag == "Y") {
							list_realtime += '<span class="icon sky_double"></span>';
						}else{
							if(lowBusYn== "Y"){
								list_realtime += '<span class="icon sky_low"></span>';
							}else if(lowPlate=='2'){
								list_realtime += '<span class="icon sky_second"></span>';
							}else if(lowPlate=='7'){
								list_realtime += '<span class="icon sky_trolley"></span>';
							}else if(lowPlate=='5'){
								list_realtime += '<span class="icon sky_jeonse"></span>';
							}else{
								list_realtime += '<span class="icon sky"></span>';
							}
						}
						break;
					case '30' :
						if(duplFlag == "Y") {
							list_realtime += '<span class="icon yellow_double"></span>';
						}else{
							if(lowBusYn== "Y"){
								list_realtime += '<span class="icon yellow_low"></span>';
							}else if(lowPlate=='2'){
								list_realtime += '<span class="icon yellow_second"></span>';	
							}else if(lowPlate=='7'){
								list_realtime += '<span class="icon yellow_trolley"></span>';
							}else if(lowPlate=='5'){
								list_realtime += '<span class="icon yellow_jeonse"></span>';
							}else{
								list_realtime += '<span class="icon yellow"></span>';
							}
						}
						break;	
						
					case '41' :
					case '42' :
					case '43' :
						if(duplFlag == "Y") {
							list_realtime += '<span class="icon purple_double"></span>';
						}else{
							if(lowBusYn== "Y"){
								list_realtime += '<span class="icon purple_low"></span>';
							}else if(lowPlate=='2'){
								list_realtime += '<span class="icon purple_second"></span>';	
							}else if(lowPlate=='7'){
								list_realtime += '<span class="icon purple_trolley"></span>';
							}else if(lowPlate=='5'){
								list_realtime += '<span class="icon purple_jeonse"></span>';
							}else{
								list_realtime += '<span class="icon purple"></span>';
							}
						}
						break;		
					
					case '51' :
					case '52' :
					case '53' :
						if(duplFlag == "Y") {
							list_realtime += '<span class="icon gray_double"></span>';
						}else{
							if(lowBusYn== "Y"){
								list_realtime += '<span class="icon gray_low"></span>';
							}else if(lowPlate=='2'){
								list_realtime += '<span class="icon gray_second"></span>';	
							}else if(lowPlate=='7'){
								list_realtime += '<span class="icon gray_trolley"></span>';
							}else if(lowPlate=='5'){
								list_realtime += '<span class="icon gray_jeonse"></span>';
							}else{
								list_realtime += '<span class="icon gray"></span>';
							}
						}
						break;		
					
					default :
						list_realtime += '<span class="icon green"></span>';
				}
				

				if(isRemainSeat){
					// if(busSapceList){
					// 	if(busSapceList.length > 0){
					// 		$.each(busSapceList,function(i){
					// 			remainSeatCnt1 = busSapceList[i].remainSeatCnt1;
					// 		});
					// 	}
					// 	//빈자리 정보가 있을때만
					// 	if(remainSeatCnt1 != "-1" && remainSeatCnt1 != "" && remainSeatCnt1 != null && remainSeatCnt1 != undefined){
					// 		if(lowPlate=='6' && (nowtime2 > 640 && nowtime1 < 9)) {
					// 			list_realtime += '<span class="num below">예약</span>';
					// 		} else{
					// 			list_realtime += '<span class="num below">'+remainSeatCnt1+'석</span>';
					// 		}
								
					// 	}
					// }

					if(seatNow != "-1" && seatNow != "" && seatNow != null && seatNow != undefined){
						if(lowPlate=='6' && (nowtime2 > 640 && nowtime1 < 9)) {
							list_realtime += '<span class="num below">예약</span>';
						} else{
							list_realtime += '<span class="num below">'+seatNow+'석</span>';
						}
					}	

				} else {
					var isDensity = false;
					if(routeTypeCd==13 || routeTypeCd==15 || routeTypeCd==22 || routeTypeCd==23 ){ // 13, 15, 21, 22, 23
						var isDensityIds = "  200000069,200000049,200000146,200000024,200000070,200000239,200000172,200000092,200000013,200000231,200000048,200000197,200000208,200000031,200000240,200000241,200000051,200000147,200000067,200000016,200000020,200000199,200000101,233000011,233000012,233000007,200000028,200000060,200000010,200000008,200000037,200000053,200000043,200000040,200000148,200000185,200000055,200000202,200000074,200000183,200000076,200000012,200000152,200000093,200000201,200000182,200000106,200000099,200000085,200000077,200000237,200000042,200000236,200000157,200000196,200000039,200000166,200000211,200000088,200000064,200000238,200000234,200000078,200000206,200000056,200000058,200000129,200000134,200000066,200000061,200000032,200000034,200000065,200000133,200000261,200000014,200000018,200000022,200000122,200000045,200000097,200000095,200000090,200000239,200000268,200000103,200000029,200000054,200000186,200000025,200000023,200000107,200000144,233000087,200000266 ";
				 		if(adminNm!='서울특별시' && adminNm!='인천광역시'){
							isDensity= true;
				 		}
					}
					
					if(isDensity){
						
						if(density==1){
							list_realtime += '<span class="num below">여유</span>';
						} else if (density==2){
							list_realtime += '<span class="num below">보통</span>';
						} else if (density==3){
							list_realtime += '<span class="num below">혼잡</span>';							
						} else if(density==4){
							list_realtime += '<span class="num below">매우<br>혼잡</span>';
						}
					}else{
						list_realtime += '<span class="trasnparent"> </span>';
					}
				}
				
				list_realtime += '</div>';
				
				realTimePos[i][3] = list_realtime;
				/**--좌측 리스트 버스아이콘 생성--**/
			});
		}
		
		var className = "";
		var iconImg = "";
		var iconTag = '<h3 id="route_detail_'+routeId+'"><a href="#none" style="cursor:default;">#area<span class="box" style="font-family:\'S-Core\';background:#background;color:#color;">#text</span> <span class="num below" style="font-family:\'S-Core\';">#route</span></a></h3>';
		
		
	    
		
		
		//노선번호 색상
		/*
			Route_tp = 11, 21, 14  --> red(직행)
			Route_tp = 12  --> blue
			Route_tp = 30  --> yellow
			Route_tp = 41, 42, 43  --> violet(시외)
			Route_tp = 51, 52, 53  --> grey (공항)
			나머지 --> green
		*/
		if(routeTypeCd == 11 || routeTypeCd == 21 || routeTypeCd == 14 || routeTypeCd == 16){
			className = "num_red";
		}else if(routeTypeCd == 12){
			className = "num_blue";
		}else if(routeTypeCd == 30){
			className = "num_yellow";
		}else if(routeTypeCd == 41 || routeTypeCd == 42 || routeTypeCd == 43){
			className = "num_purple";
		}else if(routeTypeCd == 51 || routeTypeCd == 52 || routeTypeCd == 53){
			className = "num_gray";
		}else{
			className = "num_green";
		}
		

		if(si_flag == 1){ //서울
			if(routeTypeCd == 51 || routeTypeCd == 52 || routeTypeCd == 53){
				iconImg += iconTag.replace("#area",'<span class="box" style="font-family:\'S-Core\';background:#558ed5;color:#fff;">서울</span> ').replace("#background","#6d6d6d").replace("#color","#fff").replace("#text","공항").replace("#route",routeNm);
			}else if(routeTypeCd == 41 || routeTypeCd == 42 || routeTypeCd == 43){
				iconImg += iconTag.replace("#area",'<span class="box" style="font-family:\'S-Core\';background:#558ed5;color:#fff;">서울</span> ').replace("#background","#8400ff").replace("#color","#fff").replace("#text","시외").replace("#route",routeNm);
			}else if(routeTypeCd == 11 || routeTypeCd == 21 || routeTypeCd == 16){
				iconImg += iconTag.replace("#area",'<span class="box" style="font-family:\'S-Core\';background:#558ed5;color:#fff;">서울</span> ').replace("#background","#ff0000").replace("#color","#fff").replace("#text","직좌").replace("#route",routeNm);
			}else if(routeTypeCd == 14){
				iconImg += iconTag.replace("#area",'<span class="box" style="font-family:\'S-Core\';background:#558ed5;color:#fff;">서울</span> ').replace("#background","#ff0000").replace("#color","#fff").replace("#text","광역").replace("#route",routeNm);	
			}else if(routeTypeCd == 12 ){
				iconImg += iconTag.replace("#area",'<span class="box" style="font-family:\'S-Core\';background:#558ed5;color:#fff;">서울</span> ').replace("#background","#0000ff").replace("#color","#fff").replace("#text","좌석").replace("#route",routeNm);
			}else if(routeTypeCd == 30){
				iconImg += iconTag.replace("#area",'<span class="box" style="font-family:\'S-Core\';background:#558ed5;color:#fff;">서울</span> ').replace("#background","#efe600").replace("#color","#000").replace("#text","마을").replace("#route",routeNm);
			}else{
				iconImg += iconTag.replace("#area",'<span class="box" style="font-family:\'S-Core\';background:#558ed5;color:#fff;">서울</span> ').replace("#background","#0b7240").replace("#color","#fff").replace("#text","일반").replace("#route",routeNm);
			}
		}else if(si_flag == 3){ //인천
			if(routeTypeCd == 51 || routeTypeCd == 52 || routeTypeCd == 53){
				iconImg += iconTag.replace("#area",'<span class="box" style="font-family:\'S-Core\';background:#0b7204;color:#fff;">인천</span> ').replace("#background","#6d6d6d").replace("#color","#fff").replace("#text","공항").replace("#route",routeNm);
			}else if(routeTypeCd == 41 || routeTypeCd == 42 || routeTypeCd == 43){
				iconImg += iconTag.replace("#area",'<span class="box" style="font-family:\'S-Core\';background:#0b7204;color:#fff;">인천</span> ').replace("#background","#8400ff").replace("#color","#fff").replace("#text","시외").replace("#route",routeNm);
			}else if(routeTypeCd == 11 || routeTypeCd == 21 || routeTypeCd == 16){
				iconImg += iconTag.replace("#area",'<span class="box" style="font-family:\'S-Core\';background:#0b7204;color:#fff;">인천</span> ').replace("#background","#ff0000").replace("#color","#fff").replace("#text","직좌").replace("#route",routeNm);
			}else if(routeTypeCd == 14){
				iconImg += iconTag.replace("#area",'<span class="box" style="font-family:\'S-Core\';background:#0b7204;color:#fff;">인천</span> ').replace("#background","#ff0000").replace("#color","#fff").replace("#text","광역").replace("#route",routeNm);	
			}else if(routeTypeCd == 12 ){
				iconImg += iconTag.replace("#area",'<span class="box" style="font-family:\'S-Core\';background:#0b7204;color:#fff;">인천</span> ').replace("#background","#0000ff").replace("#color","#fff").replace("#text","좌석").replace("#route",routeNm);
			}else if(routeTypeCd == 30){
				iconImg += iconTag.replace("#area",'<span class="box" style="font-family:\'S-Core\';background:#0b7204;color:#fff;">인천</span> ').replace("#background","#efe600").replace("#color","#000").replace("#text","마을").replace("#route",routeNm);
			}else{
				iconImg += iconTag.replace("#area",'<span class="box" style="font-family:\'S-Core\';background:#0b7204;color:#fff;">인천</span> ').replace("#background","#0b7240").replace("#color","#fff").replace("#text","일반").replace("#route",routeNm);
			}
		}else{//경기도
			if(routeTypeCd == 51 || routeTypeCd == 52 || routeTypeCd == 53){
				iconImg = '<img src="/gbis2014/images/ico/bus_type/4.png" alt="공항" />';
				iconImg = iconTag.replace("#area","").replace("#background","#6d6d6d").replace("#color","#fff").replace("#text","공항").replace("#route",routeNm);
			}else if(routeTypeCd == 41 || routeTypeCd == 42 || routeTypeCd == 43){
				iconImg = iconTag.replace("#area","").replace("#background","#8400ff").replace("#color","#fff").replace("#text","시외").replace("#route",routeNm);
			}else if(routeTypeCd == 30  ){
				iconImg = iconTag.replace("#area","").replace("#background","#efe600").replace("#color","#000").replace("#text","마을").replace("#route",routeNm);
			}else if(routeTypeCd == 11 || routeTypeCd == 21 || routeTypeCd == 16){
				iconImg = iconTag.replace("#area","").replace("#background","#ff0000").replace("#color","#fff").replace("#text","직좌").replace("#route",routeNm);
			}else if(routeTypeCd == 14){
				iconImg = iconTag.replace("#area","").replace("#background","#ff0000").replace("#color","#fff").replace("#text","광역").replace("#route",routeNm);	
			}else if(routeTypeCd == 12 ){	
				iconImg = iconTag.replace("#area","").replace("#background","#0000ff").replace("#color","#fff").replace("#text","좌석").replace("#route",routeNm);
			}else{
				iconImg += iconTag.replace("#area","").replace("#background","#0b7240").replace("#color","#fff").replace("#text","일반").replace("#route",routeNm);
			}
		}
		
		bus_info += '<div class="rtb_top">';
		bus_info += iconImg;
		bus_info += '<a href="javascript:routeBtnClose();focusBacktoRouteList('+routeId+');" class="btn_close">닫기</a>';
		bus_info += '</div>';
		bus_info += '<div class="rtb_table">';
		bus_info += '	<table class="list_sty02 tdwid">';
		bus_info += '		<caption>실시간버스위치 시간표</caption>';
		bus_info += '		<colgroup>';
		bus_info += '			<col width="60px">';
		bus_info += '			<col width="auto">';
		bus_info += '			<col width="auto">';
		bus_info += '			<col width="auto">';
		bus_info += '		</colgroup>';
		bus_info += '		<tbody>';
		bus_info += '			<tr>';
		bus_info += '				<th colspan="1">     </th>';
		bus_info += '				<th colspan="1">     배차간격</th>';
		bus_info += '				<th colspan="1">     기점</th>';
		bus_info += '				<th colspan="1">     종점</th>';
		bus_info += '			</tr>';
		
		
		// 반디1, 반디1-1, 반디2, 반디3, 반디4 심야배차 표출
		var bandis = ["204000149","204000150","204000152","204000178","204000179"];
		
		bus_info += '			<tr>';
		bus_info += '				<td> 평 일 </td>';
		
		if(bandis.indexOf(routeId)>=0){
			bus_info += '			<td> '+nightAlloc+'분 </td>';
		}else{
			if(peekAlloc == 0 && npeekAlloc == 0){
				bus_info += '			<td> 정보없음 </td>';
			}else if(peekAlloc && npeekAlloc){
				bus_info += '			<td> '+peekAlloc+'~'+npeekAlloc+'분 </td>';
			}else if(peekAlloc && !npeekAlloc){
				bus_info += '			<td> '+peekAlloc+'분 </td>';
			}else{
				bus_info += '			<td> 정보없음 </td>';
			}
		}
			
		if(upFirstTime && upLastTime){
			bus_info += '			<td> '+upFirstTime+'~'+upLastTime+'</td>';
		}else if(upFirstTime && !upLastTime){
			bus_info += '			<td> '+upFirstTime+'</td>';
		}else if(!upFirstTime && upLastTime){
			bus_info += '			<td>'+upLastTime+'</td>';
		}else{
			bus_info += '			<td> 정보없음 </td>';
		}
		if(downFirstTime && downLastTime){
			bus_info += '			<td> '+downFirstTime+'~'+downLastTime+'</td>';
		}else if(downFirstTime && !downLastTime){
			bus_info += '			<td> '+downFirstTime+'</td>';
		}else if(!downFirstTime && downLastTime){
			bus_info += '			<td> '+downLastTime+'</td>';
		}else{
			bus_info += '			<td> 정보없음 </td>';
		}
		bus_info += '			</tr>';

		
		
		
		bus_info += '			<tr>';
		bus_info += '				<td> 토요일 </td>';
		if(bandis.indexOf(routeId)>=0){
			bus_info += '			<td> '+nightAlloc2+'분 </td>';
		}else{
			if(peekAlloc2 == 0 && npeekAlloc2 == 0){
				bus_info += '			<td> 정보없음 </td>';
			}else if(peekAlloc2 && npeekAlloc2){
				bus_info += '			<td> '+peekAlloc2+'~'+npeekAlloc2+'분 </td>';
			}else if(peekAlloc2 && !npeekAlloc2){
				bus_info += '			<td> '+peekAlloc2+'분 </td>';
			}else{
				bus_info += '			<td> 정보없음 </td>';
			}
		}
		
		if(upFirstTime2 && upLastTime2){
			bus_info += '			<td> '+upFirstTime2+'~'+upLastTime2+'</td>';
		}else if(upFirstTime2 && !upLastTime2){
			bus_info += '			<td> '+upFirstTime2+'</td>';
		}else if(!upFirstTime2 && upLastTime2){
			bus_info += '			<td>'+upLastTime2+'</td>';
		}else{
			bus_info += '			<td> 정보없음 </td>';
		}
		if(downFirstTime2 && downLastTime2){
			bus_info += '			<td> '+downFirstTime2+'~'+downLastTime2+'</td>';
		}else if(downFirstTime2 && !downLastTime2){
			bus_info += '			<td> '+downFirstTime+'</td>';
		}else if(!downFirstTime2 && downLastTime2){
			bus_info += '			<td> '+downLastTime2+'</td>';
		}else{
			bus_info += '			<td> 정보없음 </td>';
		}
		bus_info += '			</tr>';
		
		
		
		
		
		bus_info += '			<tr>';
		bus_info += '				<td> 일요일 </td>';
		if(bandis.indexOf(routeId)>=0){
			bus_info += '			<td> '+nightAlloc4+'분 </td>';
		}else{
			if(peekAlloc4 == 0 && npeekAlloc4 == 0){
				bus_info += '			<td> 정보없음 </td>';
			}else if(peekAlloc4 && npeekAlloc4){
				bus_info += '			<td> '+peekAlloc4+'~'+npeekAlloc4+'분 </td>';
			}else if(peekAlloc4 && !npeekAlloc4){
				bus_info += '			<td> '+peekAlloc4+'분 </td>';
			}else{
				bus_info += '			<td> 정보없음 </td>';
			}
		}
		
		if(upFirstTime4 && upLastTime4){
			bus_info += '			<td> '+upFirstTime4+'~'+upLastTime4+'</td>';
		}else if(upFirstTime4 && !upLastTime4){
			bus_info += '			<td> '+upFirstTime4+'</td>';
		}else if(!upFirstTime4 && upLastTime4){
			bus_info += '			<td>'+upLastTime4+'</td>';
		}else{
			bus_info += '			<td> 정보없음 </td>';
		}
		if(downFirstTime4 && downLastTime4){
			bus_info += '			<td> '+downFirstTime4+'~'+downLastTime4+'</td>';
		}else if(downFirstTime4 && !downLastTime4){
			bus_info += '			<td> '+downFirstTime4+'</td>';
		}else if(!downFirstTime4 && downLastTime4){
			bus_info += '			<td> '+downLastTime4+'</td>';
		}else{
			bus_info += '			<td> 정보없음 </td>';
		}
		bus_info += '			</tr>';
		
		
					
		
		bus_info += '			<tr>';
		bus_info += '				<td> 공휴일 </td>';
		if(bandis.indexOf(routeId)>=0){
			bus_info += '			<td> '+nightAlloc3+'분 </td>';
		}else{
			if(peekAlloc3 == 0 && npeekAlloc3 == 0){
				bus_info += '			<td> 정보없음 </td>';
			}else if(peekAlloc3 && npeekAlloc3){
				bus_info += '			<td> '+peekAlloc3+'~'+npeekAlloc3+'분 </td>';
			}else if(peekAlloc3 && !npeekAlloc3){
				bus_info += '			<td> '+peekAlloc3+'분 </td>';
			}else{
				bus_info += '			<td> 정보없음 </td>';
			}
		}
		
		if(upFirstTime3 && upLastTime3){
			bus_info += '			<td> '+upFirstTime3+'~'+upLastTime3+'</td>';
		}else if(upFirstTime3 && !upLastTime3){
			bus_info += '			<td> '+upFirstTime3+'</td>';
		}else if(!upFirstTime3 && upLastTime3){
			bus_info += '			<td>'+upLastTime3+'</td>';
		}else{
			bus_info += '			<td> 정보없음 </td>';
		}
		if(downFirstTime3 && downLastTime3){
			bus_info += '			<td> '+downFirstTime3+'~'+downLastTime3+'</td>';
		}else if(downFirstTime3 && !downLastTime3){
			bus_info += '			<td> '+downFirstTime3+'</td>';
		}else if(!downFirstTime3 && downLastTime3){
			bus_info += '			<td> '+downLastTime3+'</td>';
		}else{
			bus_info += '			<td> 정보없음 </td>';
		}
		bus_info += '			</tr>';
		
		
		bus_info += '		</tbody>';
		bus_info += '	</table>';
		bus_info += '	<p>※ 막차시간은 교통상황 및 수요에 따라 조정될 수 있음</p>';
		bus_info += '</div>';
		
		bus_info += '<div class="rtb_table" >';
		bus_info += '	<table class="list_sty02">';
		bus_info += '		<caption>배차간격, 본사, 차고지, 인면허기관 표</caption>';
		bus_info += '		<colgroup>';
		bus_info += '			<col width="30%">';
		bus_info += '			<col width="auto">';
		bus_info += '		</colgroup>';
		bus_info += '		<tbody>';

		bus_info += '			<tr>';
		bus_info += '				<th>기점</th>';
		bus_info += '				<td>';
		if(stStaNm != ""){
			bus_info += stStaNm;
		}else{
			bus_info += '정보없음';
		}
		bus_info += '				</td>';
		bus_info += '			</tr>';
		
		bus_info += '			<tr>';
		bus_info += '				<th>종점</th>';
		bus_info += '				<td>';
		if(edStaNm != ""){
			bus_info += edStaNm;
		}else{
			bus_info += '정보없음';
		}
		bus_info += '				</td>';
		bus_info += '			</tr>';
		
		bus_info += '			<tr>';
		bus_info += '				<th>본사</th>';
		bus_info += '				<td>';
		if(companyNm || companyTel){
			bus_info += companyNm+companyTel;
		}else{
			bus_info += '정보없음';
		}
		bus_info += '				</td>';
		bus_info += '			</tr>';
		bus_info += '			<tr>';
		bus_info += '				<th>차고지</th>';
		bus_info += '				<td>';
		if(garageNm || garageTel ){
			bus_info += garageNm+garageTel;
		}else{
			bus_info += '정보없음';
		}
		bus_info += '				</td>';
		bus_info += '			</tr>';
		bus_info += '			<tr>';
		bus_info += '				<th>인면허기관</th>';
		bus_info += '				<td>';
		if(adminNm){
			bus_info += adminNm;
		}else{
			bus_info += '정보없음';
		}
		bus_info += '				</td>';
		bus_info += '			</tr>';
		bus_info += '		</tbody>';
		bus_info += '	</table>';
		bus_info += '	<p class="count">현재 <span class="red">'+busCount+'</span>대 운행중</p>';
		bus_info += '	<div class="btn_refresh"><label for="routeInterval">정보갱신주기</label>';
		bus_info += '		<select id="routeInterval" onchange="changeRouteInterval(this.value)" title="정보갱신주기">';
		bus_info += '			<option value="60">60</option>';
		bus_info += '			<option value="120">120</option>';
		bus_info += '			<option value="180">180</option>';
		bus_info += '			<option value="240">240</option>';
		bus_info += '			<option value="300" selected="selected">300</option>';
		bus_info += '		</select> 초';
		bus_info += '	</div>';
		bus_info += '</div>';
		
		
		bus_info += '<div class="expect">';
		bus_info += '<h4>예상소요시간</h4>';
		bus_info += '<fieldset>';
		bus_info += '<div class="box start"><label for="departure">출발정류소</label><input type="text" id="departure" class="inp" readonly data-seq="" onclick="selectStation()"/><div id="esimate_refresh_start" title="새로고침" onclick="resetEstiStart();"></div></div>';
		bus_info += '<div class="box end"><label for="destination">도착정류소</label><input type="text" id="destination" class="inp" readonly data-seq="" onclick="selectStation()"/><div id="esimate_refresh_end" title="새로고침" onclick="resetEstiEnd();"></div></div>';
		bus_info += '</fieldset>';
		bus_info += '<div id="popup_selectStation"><sapn>정류소 아이콘을 선택해주세요</span></div>';
		
		
		
//		
		bus_info += '<p class="ac" id="tTimeData" style="display:none"><b class="fc_red01">' +'</b>km'+ ' <b class="fc_red01">' + '</b>시간 ' +  '분 소요예정입니다.</p>';
		bus_info += '<p class="txt" id="tTimeView">&#8251; 정류소 '+'<span class="tcr dblue"><i class="fa fa-angle-down"></i></span> <span class="tcr red"><i class="fa fa-angle-down"></i></span>'+'를 선택하시면 <strong>예상소요시간</strong>을 알려드립니다.</p>';
		bus_info += '</div>';	
		
		$('#bus_info').html(bus_info);
		$('#start').html(edStaNm2).attr('title', edStaNm2);
		$('#end').html(lastStaNm).attr('title', lastStaNm);

		
		
		//상행 정류소 리스트
		if(ggUpCnt > 0){
			$.each(resultGgUp.list,function(i){
				var upStationImg = "";
				var upStationNo = resultGgUp.list[i].stationNo;
				var upStationNo_ = resultGgUp.list[i].stationNo;
				var estiSeq = resultGgUp.list[i].estiSeq;
				var upCenterYn = resultGgUp.list[i].centerYn;
				var upStationImg = (upCenterYn == 'Y') ? "station3" : "station1";
				var upStationNm = resultGgUp.list[i].stationNm;
				var upTempStationNo = resultGgUp.list[i].stationNm.indexOf("(경유)");	
				var upTempStationNoMi = resultGgUp.list[i].stationNm.indexOf("(미정차)");
                var stationNmOrg = resultGgUp.list[i].stationNm;
				if(!(upTempStationNo<0)){
					upStationNm = upStationNm.replace("(경유)","(미정차)");
					stationNmOrg = upStationNm ;
				}
				var toolStationNm = resultGgUp.list[i].stationNm;
				upStationNm = (upStationNm.length > 15) ? upStationNm.substring(0,15)+'...' : upStationNm;
				toolStationNm  = (toolStationNm .length > 15) ? toolStationNm .substring(0,15)+'...' : toolStationNm;
				var upStationSeq = resultGgUp.list[i].stationSeq;
				var upGnm = resultGgUp.list[i].gnm;
				var upStationId = resultGgUp.list[i].stationId;
				var upMobileNoSi = resultGgUp.list[i].mobileNoSi;
				var upLon = resultGgUp.list[i].lon;
				var upLat = resultGgUp.list[i].lat;
		    	
				//서울,인천 번호 있을 시 서울,인천 번호로 표출
				if(upMobileNoSi) upStationNo = upMobileNoSi;
				
				//upMobileNoSi가 0일 경우 upStationNo_로 표출
				if(upMobileNoSi == "00000") upStationNo = upStationNo_;
				
				if(!(upTempStationNo<0) || !(upTempStationNoMi<0)) upStationNo = "";
				
				//검색결과 정류소ID 저장
				routeStationIdArr.push(upStationId);
				
                 // 경유 또는 미정차 정류소가 아닐 경우
				if(upTempStationNo<0 && upTempStationNoMi<0){
					list_route_upline += '<li><a id="uplist_route_station_'+i+'" href="#" title="'+stationNmOrg+'" onclick="javascript:getRouteMap(\''+i+'\',\''+upLon+'\',\''+upLat+'\',\'1\');focusRouteStationPopup_up('+i+')" title="'+upStationNm+'정류소 도착정보 지도위 팝업으로 표시">';
				}else{
					list_route_upline += '<li><a title="'+stationNmOrg+'">';
				}

				// 시군명
				if(i == resultGgUp.list.length -1){//회차점 일때
					list_route_upline += '<span class="posi_name box" style="background:#555555;">회차점</span>';
				}else{//회차점 아닐 때
					list_route_upline += '<span class="posi_name box" style="background:#0076b2;">'+upGnm.substring(0,3)+'</span>';
				}
				
				for(var k = 0; k <realTimePos.length; k++){
					if(realTimePos[k][4] == "U"){
						if(upStationId == realTimePos[k][1]){
							list_route_upline += realTimePos[k][3];
							//console.log("upfrom : "+realTimePos[k][8]);
						}
					}
				}
				
				
				list_route_upline += '<div class="bus_line_wrap">';



				if(upTempStationNo<0 && upTempStationNoMi<0){  // 경유 또는 미정차 정류소가 아닐 경우
					list_route_upline += '<h4 class="bus_stop">'+upStationNm+'</h4>';
				}else{
					list_route_upline += '<h4 class="bus_stop" style="color: #787676" title="'+stationNmOrg+'" >'+upStationNm+'</h4></a>';
				}
				// ---- 미정차일 경우 a태그 끝 ---- //

				list_route_upline += '<br><p class="bus_id dblue" alt="상행리스트">'+upStationNo+'</p>';
				list_route_upline += '</div></a>';
				
				if(i == resultGgUp.list.length -1){//회차점 일때   
					list_route_upline += '<div class="station-arrow"  onclick="estimateTime(event, \''+stationNmOrg+'\', \''+estiSeq+'\');"><span class="tline dblue"></span>';
					if(upTempStationNo<0){
						list_route_upline += '<span class="tcr dblue"  ><i class="fa fa-angle-down"></i></span></div>';
						list_route_upline += '</li>';
					}
				}else{//회차점 아닐 때
					if(upTempStationNo<0 && upTempStationNoMi<0){ // 경유 또는 미정차 정류소가 아닐 경우
						list_route_upline += '<div class="station-arrow"  onclick="estimateTime(event, \''+stationNmOrg+'\', \''+estiSeq+'\');"><span class="tline dblue"></span><span class="tcr dblue" ><i class="fa fa-angle-down"></i></span></div></li>';
					} else {
						list_route_upline += '<div class="station-arrow" style="cursor: default"><span class="tline dblue"></span></div></li>';
					}	
					
				}
				

				//지도 상행 정류소 마커 생성
				var up_size = new Tmap.Size(20, 20);
				var up_offset = new Tmap.Pixel(-(up_size.w / 2), -up_size.h);
				var up_iconHtml = new Tmap.IconHtml('<div class="icon_wa line routeStation'+i+'"><img src="/gbis2014/images/ico/common/'+upStationImg+'.png" /></div>',up_size,up_offset);
				var up_routeMarker = new Tmap.Marker(new Tmap.LonLat(upLon, upLat), up_iconHtml);
				
				// 마커 레이어 생성
				map.addLayer(upRouteMarkerLayer);
	
				// 마커 생성
				if(upTempStationNo<0){
					upRouteMarkerLayer.addMarker(up_routeMarker);
					upRouteMarkerLayer.div.style.zIndex = 500;
				}
				
				//팝업 생성
				/****************************************************************************************************
				 * Tmap.Popup.Anchored offset 처리 방식
				 * tl : popup.anchor.offset.x - popup.size.w / popup.anchor.offset.y - popup.size.h
				 * tr : popup.anchor.offset.x + popup.anchor.size.w /  popup.anchor.offset.y - popup.size.h
				 * bl : popup.anchor.offset.x - popup.size.w/ popup.anchor.offset.y + popup.anchor.size.h
				 * br : popup.anchor.offset.x + popup.anchor.size.w / popup.anchor.offset.y + popup.anchor.size.h
				 ****************************************************************************************************/
				
				upRouteStationObj[i] = up_routeMarker;
				var sizeW = 380;
				var alonlat = new Tmap.LonLat(upLon, upLat);
				var aSize = new Tmap.Size(10, 20);
				var aOffset = new Tmap.Pixel(-(up_size.w / 2), -up_size.h);
				var anchorObj = {
					size : aSize,
					offset : aOffset
				};
				var cSize = new Tmap.Size(sizeW, 400);
				//상행목록
				var label = '<div class="tooltip" id="pop_id_'+i+'"><!--상행정류소 도착정보 팝업-->';
				
				label += '<h1><a href="javascript:busStationView(\''+upStationId+'\',\''+stationNmOrg+'\');" title="'+stationNmOrg+' 정류소 통합검색 결과 새 창으로 보기">'+toolStationNm+' <span class="line">|</span> <span class="station_code" alt="upStationNo1">'+upStationNo+'</span><span class="crNm" style="display:none">'+upStationNm+'</span><span class="stationId" style="display:none">'+upStationId+'</span></a></h1>';
				label += '<div class="tooltip_content">';
				label += '<div class="after_bus">';
				label += '<h2>잠시후 도착버스 <span class="line">|</span></h2>';
				label += '<div id="scroller" class="scroller scroller_'+upStationId+'" style="position:relative;margin-left:100px;width:218px;height:31px">';
				label += '<div class="scroller_mask" style="width:210px;height:31px;">';
				label += '<ul class="station_bus_scroll_'+upStationId+'">';
				label += '</ul>';
				label += '</div>';
				label += '<ul class="scroller_nav" style="width: 238px;">';
				label += '<li></li>';
				// label += '<a tabindex="0" title="잠시후 도착버스 더보기"  style="width: 15px; height: 15px; right: 0px; top: 8px; background-image: url(/gbis2014/images/location/bg_tooltip.png); background-position: -20px 0px; background-repeat: no-repeat;"></a>';
				label += '</ul>';
				label += '</div>';
				label += '</div>';
				label += '<div class="station_bus_list">';
				label += '<ul class="station_bus_list_'+upStationId+'">';
				label += '</ul>';
				label += '</div>';
				label += '</div>';
				label += '<div class="tooltip_btn">';
				label += '<button type="button" onclick="btnStartFlag()" class="w_btn start"><span>출발</span></button>\n';
				label += '<button type="button" onclick="btnEndFlag()" class="w_btn end"><span>도착</span></button>';
				label += '</div>';
				label += '<a class="close" title="정류소 도착정보 창 닫기"  href="javascript:tooltipClose();focusBacktoRouteStationList_up('+i+');"><i class="fa fa-times" aria-hidden="true"></i></a>';
				label += '<div class="tooltip_arrow"></div>';
				label += '</div>';
				
				up_routeMarker.popup = new Tmap.Popup.Anchored("customLabel", alonlat, cSize, label, anchorObj, false);
				up_routeMarker.popup.relativePosition = 'tr';
	
				up_routeMarker.popup.updateRelativePosition();
				up_routeMarker.popup.calculateRelativePosition = function(px) {
					return up_routeMarker.popup.relativePosition;
				};
				up_routeMarker.popup.panMapIfOutOfView = false;
				up_routeMarker.popup.keepInMap = false;
				
				//팝업 스타일링 부분
				up_routeMarker.popup.contentDiv.style.overflow = "hidden";
				up_routeMarker.popup.contentDiv.style.padding = "0px 0px 30px 0px";
				up_routeMarker.popup.setBackgroundColor("transparent");
				/*
				map.addPopup(up_routeMarker.popup);
				var pContentDivW = jQuery(up_routeMarker.popup.contentDiv).find('div').width();
				up_routeMarker.popup.anchor.offset.x = up_routeMarker.popup.anchor.offset.x - (pContentDivW / 2);
				up_routeMarker.popup.hide();
				*/
				$(up_routeMarker.icon.imageDiv).find('div').css('cursor', 'pointer'); //마커 오버 시 스타일
				up_routeMarker.events.register('click', upRouteStationObj[i], onMarkerClick);
				up_routeMarker.events.register('mouseover', upRouteStationObj[i], onMouseMarker);
				up_routeMarker.events.register('mouseout', upRouteStationObj[i], outMouseMarker);
				up_routeMarker.popup.events.register('mouseover',up_routeMarker, onMousePopup);
				up_routeMarker.popup.events.register('mouseout',up_routeMarker, outMousePopup);
				
				
				
				// 실시간 차량아이콘 지도위 표출 (스마트앱과 아이콘 통일) DKY
				
				//var busIconOnMap = '<span></span>' ;
				for(var k = 0; k <realTimePos.length; k++){
					if(realTimePos[k][4] == "U"){
						var up_bus_size = new Tmap.Size(30, 33);
						var up_bus_offset = new Tmap.Pixel(-(up_bus_size.w / 2), -up_bus_size.h);
						var busIconOnMap ;

						switch(routeTypeCd) {
							case '13':
							case '15':
							case '23':
								busIconOnMap = 'vehicle green';
								break;
							case '11':	
							case '14' :
							case '16' :
							case '21' :
								busIconOnMap = 'vehicle red';
								break;
							case '12' :
								busIconOnMap = 'vehicle sky';
								break;
							case '30' :
								busIconOnMap = 'vehicle yellow';
								break;
							case '41' :
							case '42' :
							case '43' :
								busIconOnMap = 'vehicle purple';
								break;
							case '51' :
							case '52' :
							case '53' :
								busIconOnMap = 'vehicle gray';
								break;
							default :
								busIconOnMap = 'vehicle navy';
						}
						var up_bus_iconHtml = new Tmap.IconHtml('<div class="upRealtimeBus'+k+'"><span class="'+busIconOnMap+'"></span></div>',up_bus_size,up_bus_offset);
						var up_bus_routeMarker = new Tmap.Marker(new Tmap.LonLat(realTimePos[k][5],realTimePos[k][6]), up_bus_iconHtml);
						
						if(realTimePos[k][7] != 'Y'){
							map.addLayer(upRealBusRouteMarkerLayer);
							upRealBusRouteMarkerLayer.addMarker(up_bus_routeMarker);
						}else{
							map.addLayer(upRealBusRouteLowMarkerLayer);
							upRealBusRouteLowMarkerLayer.addMarker(up_bus_routeMarker);
						}
					}
				}
	    	});
			upRouteMarkerLayer.setVisibility(false);
		}
		
		//하행 정류소 리스트
		if(ggDownCnt > 0){
			$.each(resultGgDown.list,function(i){
				var downStationNo = resultGgDown.list[i].stationNo;
				var downStationNo_ = resultGgDown.list[i].stationNo;
				var estiSeq = resultGgDown.list[i].estiSeq;
				var downCenterYn = resultGgDown.list[i].centerYn;
				var downStationImg = (downCenterYn == 'Y') ? "station4" : "station2";
				var downStationNm = resultGgDown.list[i].stationNm;
				var downTempStationNo = resultGgDown.list[i].stationNm.indexOf("(경유)");
				var downTempStationNoMi = resultGgDown.list[i].stationNm.indexOf("(미정차)");
				var stationNmOrg = resultGgDown.list[i].stationNm;
				if(!(downTempStationNo<0)){
					downStationNm = downStationNm.replace("(경유)","(미정차)");
					stationNmOrg = downStationNm;
				}
				var toolStationNm = resultGgDown.list[i].stationNm;
				toolStationNm  = (toolStationNm .length > 15) ? toolStationNm .substring(0,15)+'...' : toolStationNm;
				downStationNm = (downStationNm.length > 15) ? downStationNm.substring(0,15)+'...' : downStationNm;
				var downStationSeq = resultGgDown.list[i].stationSeq;
				var downGnm = resultGgDown.list[i].gnm;
				var downStationId = resultGgDown.list[i].stationId;
				var downMobileNoSi = resultGgDown.list[i].mobileNoSi;
				var downLon = resultGgDown.list[i].lon;
				var downLat = resultGgDown.list[i].lat;
				
				
				//서울,인천 번호 있을 시 서울,인천 번호로 표출
				if(downMobileNoSi) downStationNo = downMobileNoSi;
				
				//downMobileNoSi가 0일 경우 처리
				if(downMobileNoSi == "00000") downStationNo = downStationNo_;
								
				if(!(downTempStationNo<0) || !(downTempStationNoMi<0)) downStationNo ="";

				//검색결과 정류소ID 저장
				routeStationIdArr.push(downStationId);
				
				// 경유 또는 미정차 정류소가 아닐 경우
				if(downTempStationNo<0 && downTempStationNoMi<0){
					list_route_downline += '<li><a  id="downlist_route_station_'+i+'" href="#" title="'+stationNmOrg+'" onclick="javascript:getRouteMap(\''+i+'\',\''+downLon+'\',\''+downLat+'\',\'2\');focusRouteStationPopup_down('+i+')" >';
				}else{
					list_route_downline += '<li><a id="downlist_route_station_'+i+'" title="'+stationNmOrg+'">';
				}
				
				// 시군명
				list_route_downline += '<span class="posi_name box" style="background:#ed3015;">'+downGnm.substring(0,3)+'</span>';
				
				for(var k = 0; k <realTimePos.length; k++){
					if(realTimePos[k][4] == "D"){
						if(downStationId == realTimePos[k][1]){
							list_route_downline += realTimePos[k][3];
						}
					}
				}

				
				list_route_downline += '<div class="bus_line_wrap">';

				if(downTempStationNo<0 && downTempStationNoMi<0){  // 경유 또는 미정차 정류소가 아닐 경우
					list_route_downline += '<h4 class="bus_stop">'+downStationNm+'</h4>';
				}else{
					list_route_downline += '<h4 class="bus_stop" style="color: #787676">'+downStationNm+'</h4></a>';
				}
				// ---- 미정차일 경우 a태그 끝 ---- //

				list_route_downline += '<br><p class="bus_id red" alt="하행리스트">'+downStationNo+'</p>';
				list_route_downline += '</div></a>';



				// 하행에는 회차점 없음
				if(downTempStationNo<0 && downTempStationNoMi<0){ // 경유 또는 미정차 정류소가 아닐 경우
					list_route_downline += '<div class="station-arrow"  onclick="estimateTime(event, \''+stationNmOrg+'\', \''+estiSeq+'\');"><span class="tline red"></span><span class="tcr red" ><i class="fa fa-angle-down"></i></span></div></li>';
				}else{
					list_route_downline += '<div class="station-arrow" style="cursor: default"><span class="tline red"></span></div></li>';
				}



				//지도 하행 정류소 마커 생성
				var down_size = new Tmap.Size(20, 20);
				var down_offset = new Tmap.Pixel(-(down_size.w / 2), -down_size.h);
				var down_iconHtml = new Tmap.IconHtml('<div class="icon_wa dot routeStation'+i+'"><img src="/gbis2014/images/ico/common/'+downStationImg+'.png" /></div>',down_size,down_offset);
				var down_RouteMarker = new Tmap.Marker(new Tmap.LonLat(downLon, downLat), down_iconHtml);
				
				// 마커 레이어 생성
				map.addLayer(downRouteMarkerLayer);
	
				// 마커 생성
				if(downTempStationNo<0){
					downRouteMarkerLayer.addMarker(down_RouteMarker);
					downRouteMarkerLayer.div.style.zIndex = 500;
				}
				
				//팝업 생성
				/****************************************************************************************************
				 * Tmap.Popup.Anchored offset 처리 방식
				 * tl : popup.anchor.offset.x - popup.size.w / popup.anchor.offset.y - popup.size.h
				 * tr : popup.anchor.offset.x + popup.anchor.size.w /  popup.anchor.offset.y - popup.size.h
				 * bl : popup.anchor.offset.x - popup.size.w/ popup.anchor.offset.y + popup.anchor.size.h
				 * br : popup.anchor.offset.x + popup.anchor.size.w / popup.anchor.offset.y + popup.anchor.size.h
				 ****************************************************************************************************/
				
				downRouteStationObj[i] = down_RouteMarker;
				var sizeW = 380;
				var alonlat = new Tmap.LonLat(downLon, downLat);
				var aSize = new Tmap.Size(10, 20);
				var aOffset = new Tmap.Pixel(-(down_size.w / 2), -down_size.h);
				var anchorObj = {
					size : aSize,
					offset : aOffset
				};
				var cSize = new Tmap.Size(sizeW, 400);
				//하행목록
				var label = '<div class="tooltip" id="pop_id_down_'+i+'" ><!--하행정류소 도착정보 팝업-->';
				
				label += '<h1><a href="javascript:busStationView(\''+downStationId+'\',\''+stationNmOrg+'\');" title="'+stationNmOrg+' 정류소 통합검색 결과 새 창으로 보기">'+toolStationNm+' <span class="line">|</span> <span class="station_code" alt="downStationNo">'+downStationNo+'</span><span class="crNm" style="display:none">'+downStationNm+'</span><span class="stationId" style="display:none">'+downStationId+'</span></a></h1>';
				label += '<div class="tooltip_content">';
				label += '<div class="after_bus">';
				label += '<h2>잠시후 도착버스 <span class="line">|</span></h2>';
				label += '<div id="scroller" class="scroller scroller_'+downStationId+'" style="position:relative;margin-left:100px;width:218px;height:31px">';
				label += '<div class="scroller_mask" style="width:210px;height:31px;">';
				label += '<ul class="station_bus_scroll_'+downStationId+'">';
				label += '</ul>';
				label += '</div>';
				label += '<ul class="scroller_nav" style="width: 238px;">';
				label += '<li></li>';
				// label += '<a tabindex="0" title="잠시후 도착버스 더보기"  style="width: 15px; height: 15px; right: 0px; top: 8px; background-image: url(/gbis2014/images/location/bg_tooltip.png); background-position: -20px 0px; background-repeat: no-repeat;"></a>';
				label += '</ul>';
				label += '</div>';
				label += '</div>';
				label += '<div class="station_bus_list">';
				label += '<ul class="station_bus_list_'+downStationId+'">';
				label += '</ul>';
				label += '</div>';
				label += '</div>';
				label += '<div class="tooltip_btn">';
				label += '<button type="button" onclick="btnStartFlag()" class="w_btn start"><span>출발</span></button>\n';
				label += '<button type="button" onclick="btnEndFlag()" class="w_btn end"><span>도착</span></button>';
				label += '</div>';
				label += '<a class="close" title="정류소 도착정보 창 닫기"  href="javascript:tooltipClose();focusBacktoRouteStationList_down('+i+');"><i class="fa fa-times" aria-hidden="true"></i></a>';
				label += '<div class="tooltip_arrow"></div>';
				label += '</div>';
				
				down_RouteMarker.popup = new Tmap.Popup.Anchored("customLabel", alonlat, cSize, label, anchorObj, false);
				down_RouteMarker.popup.relativePosition = 'tr';
	
				down_RouteMarker.popup.updateRelativePosition();
				down_RouteMarker.popup.calculateRelativePosition = function(px) {
					return down_RouteMarker.popup.relativePosition;
				};
				down_RouteMarker.popup.panMapIfOutOfView = false;
				down_RouteMarker.popup.keepInMap = false;
				
				//팝업 스타일링 부분
				down_RouteMarker.popup.contentDiv.style.overflow = "hidden";
				down_RouteMarker.popup.contentDiv.style.padding = "0px 0px 30px 0px";
				down_RouteMarker.popup.setBackgroundColor("transparent");
				/*
				map.addPopup(down_RouteMarker.popup);
				var pContentDivW = jQuery(down_RouteMarker.popup.contentDiv).find('div').width();
				down_RouteMarker.popup.anchor.offset.x = down_RouteMarker.popup.anchor.offset.x - (pContentDivW / 2);
				down_RouteMarker.popup.hide();
				*/
				$(down_RouteMarker.icon.imageDiv).find('div').css('cursor', 'pointer'); //마커 오버 시 스타일
				down_RouteMarker.events.register('click', downRouteStationObj[i], onMarkerClick);
				down_RouteMarker.events.register('mouseover', downRouteStationObj[i], onMouseMarker);
				down_RouteMarker.events.register('mouseout', downRouteStationObj[i], outMouseMarker);
				down_RouteMarker.popup.events.register('mouseover',down_RouteMarker, onMousePopup);
				down_RouteMarker.popup.events.register('mouseout',down_RouteMarker, outMousePopup);
				
				
				// 실시간 차량아이콘 지도위 표출 하행 (스마트앱과 아이콘 통일) DKY 
				
				for(var k = 0; k <realTimePos.length; k++){
					if(realTimePos[k][4] == "D"){
						var up_bus_size = new Tmap.Size(30, 33);
						var up_bus_offset = new Tmap.Pixel(-(up_bus_size.w / 2), -up_bus_size.h);
						var busIconOnMap ;

						switch(routeTypeCd) {
							case '13':
							case '15':
							case '23':
								busIconOnMap = 'vehicle green';
								break;
							case '11':	
							case '14' :
							case '16' :
							case '21' :
								busIconOnMap = 'vehicle red';
								break;
							case '12' :
								busIconOnMap = 'vehicle sky';
								break;
							case '30' :
								busIconOnMap = 'vehicle yellow';
								break;
							case '41' :
							case '42' :
							case '43' :
								busIconOnMap = 'vehicle purple';
								break;
							case '51' :
							case '52' :
							case '53' :
								busIconOnMap = 'vehicle gray';
								break;
							default :
								busIconOnMap = 'vehicle navy';
						}
						var up_bus_iconHtml = new Tmap.IconHtml('<div class="upRealtimeBus'+k+'"><span class="'+busIconOnMap+'"></span></div>',up_bus_size,up_bus_offset);
						var up_bus_routeMarker = new Tmap.Marker(new Tmap.LonLat(realTimePos[k][5],realTimePos[k][6]), up_bus_iconHtml);
						
						if(realTimePos[k][7] != 'Y'){
							map.addLayer(upRealBusRouteMarkerLayer);
							upRealBusRouteMarkerLayer.addMarker(up_bus_routeMarker);
						}else{
							map.addLayer(upRealBusRouteLowMarkerLayer);
							upRealBusRouteLowMarkerLayer.addMarker(up_bus_routeMarker);
						}
					}
				}
				
	    	});
			downRouteMarkerLayer.setVisibility(false);

			$('#end').parent().show();
			$('.schbus_rtb_bt ul.schtab li:eq(0)').css('width', '50%');
		} else {
			$('#end').parent().hide();
			$('.schbus_rtb_bt ul.schtab li:eq(0)').css('width', '100%');
		}
		
		$('#resultUpline ol').html(list_route_upline + list_route_downline);
		$('#resultUpline ol li:first-child .posi_name').html('기점');
		$('#resultUpline ol li:last-child .posi_name').addClass('starting_point').html('종점');
		

		//기본 상행라인 표출
		updownStatus = "up";
		$("#resultUpline").show();
		$("#resultDownline").hide();
		
		
		
		
		//열려있는 툴팁 있을 시 툴팁 닫기
		if(crPopup) tooltipClose();
		
		//하행라인 벡터, 마커 표출
		if(down_line_layer != null) down_line_layer.setVisibility(true);
		if(downRouteMarkerLayer.markers.length != 0) downRouteMarkerLayer.setVisibility(true);
		if(downRealBusRouteMarkerLayer.markers.length != 0) downRealBusRouteMarkerLayer.setVisibility(true);
		if(downRealBusRouteLowMarkerLayer.markers.length != 0) downRealBusRouteLowMarkerLayer.setVisibility(true);
		
		//상행라인 벡터, 마커 표출
		if(up_line_layer != null) up_line_layer.setVisibility(true);
		if(upRouteMarkerLayer.markers.length != 0) upRouteMarkerLayer.setVisibility(true);
		if(upRealBusRouteMarkerLayer.markers.length != 0) upRealBusRouteMarkerLayer.setVisibility(true);
		if(upRealBusRouteLowMarkerLayer.markers.length != 0) upRealBusRouteLowMarkerLayer.setVisibility(true);
		
		//줌레벨에 따른 정류소 마커표출
		moveZoom();
		
		//노선상세 타이머 실행
		if($('.mapsch_after2').css("display") == "block"){ //실시간버스맵이 보여지고 있을때만
			runDataRefreshRoute();
		}
		
		$("#routeInterval").val(refreshRouteInterval).attr("selected", "selected");
		
	}else{
		alert("조회 실패");
	}
}

function getRouteLineSuccess(data){
	
	if(data.success){
		$( "#loading" ).hide();
		
		var resultGgUpline = data.result.gg.upLine;
		var ggUplineCnt = resultGgUpline.count;
		
		var resultGgDownline = data.result.gg.downLine;
		var ggDownlineCnt = resultGgDownline.count;
		
		//지도 상행 벡터 생성
		var upPointList = [];
		if(ggUplineCnt > 0){
			$.each(resultGgUpline.list,function(i){
				//baepro 20150318 added
				var upLineType = resultGgUpline.list[i].type;
				//baepro 20150318 added
				if(upLineType!='2'){
				var upLineLinkId = resultGgUpline.list[i].linkId;
				var upLineSeq = resultGgUpline.list[i].seq;
				var upLineLon = resultGgUpline.list[i].lon;
				var upLineLat = resultGgUpline.list[i].lat;
				
				
				upPointList.push(new Tmap.Geometry.Point(upLineLon, upLineLat));
				}
			});
			
			var up_lineString = new Tmap.Geometry.LineString(upPointList);
			var up_style_bold = {strokeWidth: 5, strokeColor:"#0000FF"}; //라인스타일
			var up_mLineFeature = new Tmap.Feature.Vector(up_lineString, null, up_style_bold);
			map.addLayers([up_line_layer]);
			up_line_layer.addFeatures([up_mLineFeature]);
			up_line_layer.div.style.zIndex = 340;
			up_line_layer.setVisibility(true);
		}
		
		//지도 하행 벡터 생성
		var downPointList = [];
		if(ggDownlineCnt > 0){
			$.each(resultGgDownline.list,function(i){
				//baepro 20150318 added
				var downLineType = resultGgDownline.list[i].type;
				//baepro 20150318 added
				if(downLineType!='2'){
				var downLineLinkId = resultGgDownline.list[i].linkId;
				var downLineSeq = resultGgDownline.list[i].seq;
				var downLineLon = resultGgDownline.list[i].lon;
				var downLineLat = resultGgDownline.list[i].lat;
				
				downPointList.push(new Tmap.Geometry.Point(downLineLon, downLineLat));
				}
			});
			
			var down_lineString = new Tmap.Geometry.LineString(downPointList);
			var down_style_bold = {strokeWidth: 5, strokeColor:"#FF0000"}; //라인스타일
			var down_mLineFeature = new Tmap.Feature.Vector(down_lineString, null, down_style_bold);
			map.addLayers([down_line_layer]);
			down_line_layer.addFeatures([down_mLineFeature]);
			down_line_layer.div.style.zIndex = 340;
			down_line_layer.setVisibility(true);
		}
		
		map.zoomToExtent(up_line_layer.getDataExtent());
	}else{
		$( "#loading" ).hide();
		alert("조회 실패");
	}
}

function getSubwayDetail(subwayName, subwayLine){
	window.open( "schBus.action?cmd=getSubwayDetail&subwayName="+escape(encodeURIComponent(subwayName))+"&subwayLine="+escape(encodeURIComponent(subwayLine))+"+&subInfo=", "_blank", "height=570,width=720,menubar=0,resizable=0,scrollbars=0,status=0,titlebar=0,toolbar=0" );
}

function getSubwayDetailRoute(subwayName, subwayLine){
	window.open( "schBus.action?cmd=getSubwayDetail&subwayName="+escape(encodeURIComponent(subwayName))+"&subwayLine="+escape(encodeURIComponent(subwayLine))+"&subInfo=subInfo", "_blank", "height=570,width=720,menubar=0,resizable=0,scrollbars=0,status=0,titlebar=0,toolbar=0" );
}

function onMarkerClick(evt) {
	
	if (chkNum == 1) {
		
		//팝업 생성
		map.addPopup(this.popup);
		var pContentDivW = jQuery(this.popup.contentDiv).find('div').width();
		this.popup.anchor.offset.x = -10 - (pContentDivW / 2);
		
		this.popup.panMapIfOutOfView = true;
		this.popup.show();
		
		crPopup = this.popup;
		crLon = crPopup.lonlat.lon;
		crLat = crPopup.lonlat.lat;
		routeName = jQuery(crPopup.contentDiv).find('.crNm').text();

		chkNum = 2;
	} else {
		detailLineClose(); //다중노선  스크립트창 닫기
		map.removePopup(crPopup); //열려있던 팝업 닫기
		map.controls[0].activate();
		
		//팝업 생성
		map.addPopup(this.popup);
		var pContentDivW = jQuery(this.popup.contentDiv).find('div').width();
		this.popup.anchor.offset.x = -10 - (pContentDivW / 2);
		
		this.popup.panMapIfOutOfView = true;
		this.popup.show();
		
		crPopup = this.popup;
		crLon = crPopup.lonlat.lon;
		crLat = crPopup.lonlat.lat;
		routeName = jQuery(crPopup.contentDiv).find('.crNm').text();

	}
	
	localBusStation = false; //주변정류장인지 아닌지 구분
	var makerClass = $(this.icon.imageDiv).find('div').attr('class');
	
	//도착정보 호출
	if(makerClass.indexOf("routeStation") != -1){//노선상세 정류장 조회시
		//route_station_id = $(this.popup.contentDiv).find('.routeStationId').text();
		//route_id = $(this.popup.contentDiv).find('.routeId').text();
		station_id = $(this.popup.contentDiv).find('.stationId').text();
		var url = "/gbis2014/schBusAPI.action";
		var data = 'cmd=searchBusStationJson';
		data += '&stationId='+station_id;
		//data += '&routeId='+route_id;
		
		$.ajax({
			type: "post",
			contentType: "application/x-www-form-urlencoded;charset=UTF-8",
			dataType: "json",
			url: url,
			data: data,
			success: getStationRealtimeSuccess,
			error: ajaxError
		});
		
	}else if(makerClass.indexOf("station") != -1){ //통합검색 정류장 조회시
		station_id = $(this.popup.contentDiv).find('.stationId').text();
		var url = "/gbis2014/schBusAPI.action";
		var data = 'cmd=searchBusStationJson';
		data += '&stationId='+station_id;
		
		$.ajax({
			type: "post",
			contentType: "application/x-www-form-urlencoded;charset=UTF-8",
			dataType: "json",
			url: url,
			data: data,
			success: getStationRealtimeSuccess,
			error: ajaxError
		});
		
	}else if(makerClass.indexOf("localBus") != -1){ //주변 정류장 조회시
		localBusStation = true; //주변정류장인지 아닌지 구분
		station_id = $(this.popup.contentDiv).find('.stationId').text();
		var url = "/gbis2014/schBusAPI.action";
		var data = 'cmd=searchBusStationJson';
		data += '&stationId='+station_id;
		
		$.ajax({
			type: "post",
			contentType: "application/x-www-form-urlencoded;charset=UTF-8",
			dataType: "json",
			url: url,
			data: data,
			success: getStationRealtimeSuccess,
			error: ajaxError
		});
		
	}
}

function getStationRealtimeSuccess(data){
	if(data.success){
		var result = data.result;
		var count = result.count;
		var stationNm = result.stationNm;
		var stationId = result.stationId;
		var busArrivalList = result.busArrivalList;
		var busArrivalInfo = result.busArrivalInfo;
		var busStationInfo = result.busStationInfo;

		var stationRealtime = "";
		var stationRealtimeScroll = "";
		
		var routeStat = false; //정류소 해당노선 유무
		var arrivalInfoStat = false; //도착예정목록에 노선정보가 있는지 유무
		
		
		//실시간 버스 초기화
		$('.station_bus_scroll_'+stationId).html("");
		$('.station_bus_list_'+stationId).html("");
		
		if(busStationInfo.length > 0){
			
			// 선택되어진 해당 노선 먼저 표출
			$.each(busStationInfo,function(i){
				
				var stationRouteId = busStationInfo[i].routeId;
				var stationRouteName = busStationInfo[i].routeName;
				var stationRouteDestName = busStationInfo[i].routeDestName;
				var stationUpdownNum = busStationInfo[i].updownNum;
				var stationStaOrder = busStationInfo[i].staOrder;
				var stationRegionName = busStationInfo[i].regionName;
				
				//노선 상세에서 정류장 상세 보기 시 해당 노선 먼저 표출
				if(route_name == stationRouteName && updown_status == stationUpdownNum){
					
					routeStat = false; //정류소 해당노선 유무 초기화
					
					$.each(busArrivalInfo,function(i){
						
						var routeId = busArrivalInfo[i].routeId;
						var routeTypeCd = busArrivalInfo[i].routeTypeCd;
						var routeName = busArrivalInfo[i].routeName;
						var routeDestName = busArrivalInfo[i].routeDestName;
						var flag = busArrivalInfo[i].flag;
						var plateNo1 = busArrivalInfo[i].plateNo1;
						var predictTime1 = busArrivalInfo[i].predictTime1;
						var locationNo1 = busArrivalInfo[i].locationNo1;
						var remainSeatCnt1 = busArrivalInfo[i].remainSeatCnt1;
						var delayYn1 = busArrivalInfo[i].delayYn1;
						var plateNo2 = busArrivalInfo[i].plateNo2;
						var predictTime2 = busArrivalInfo[i].predictTime2;
						var locationNo2 = busArrivalInfo[i].locationNo2;
						var remainSeatCnt2 = busArrivalInfo[i].remainSeatCnt2;
						var delayYn2 = busArrivalInfo[i].delayYn2;
						var crowded1 = busArrivalInfo[i].crowded1;
						var crowded2 = busArrivalInfo[i].crowded2;
						var siFlag = 0;
						var staOrder = busArrivalInfo[i].staOrder;
						var runBusFlag = busArrivalInfo[i].runBusFlag;
						
						var lowPlate1 = busArrivalInfo[i].lowPlate1;
						var lowPlate2 = busArrivalInfo[i].lowPlate2;
						
						var plateType1 = busArrivalInfo[i].plateType1;
						var plateType2 = busArrivalInfo[i].plateType2;
						
						var density1 = busArrivalInfo[i].density1;
						var density2 = busArrivalInfo[i].density2;
						
						var className = "";
						var iconImg = "";
			            
			            //노선번호 색상
						/*
						Route_tp = 11, 21, 14  --> red(직행)
						Route_tp = 12  --> blue
						Route_tp = 30  --> yellow
						Route_tp = 41, 42, 43  --> violet(시외)
						Route_tp = 51, 52, 53  --> grey (공항)
						나머지 --> green
						 */
						if(routeTypeCd == 11 || routeTypeCd == 21 || routeTypeCd == 14 || routeTypeCd == 16){
							className = "num_red";
						}else if(routeTypeCd == 12){
							className = "num_blue";
						}else if(routeTypeCd == 30  ){
							className = "num_yellow";
						}else if(routeTypeCd == 41 || routeTypeCd == 42 || routeTypeCd == 43){
							className = "num_purple";
						}else if(routeTypeCd == 51 || routeTypeCd == 52 || routeTypeCd == 53){
							className = "num_gray";
						}else{
							className = "num_green";
						}
					
						//노선 아이콘
						/*
						SI_FLAG = 1 --> 서울
							Route_tp = 51,52, 53  --> 공항버스(seoul.gif, airport.gif)
							Route_tp = 41, 42, 43  --> 시외버스(seoul.gif, si.gif)
							Route_tp = 나머지 --> seoul.gif
						SI_FLAG = 3 --> 인천
							Route_tp = 51,52, 53  --> 공항버스(inchon.gif airport.gif)
							Route_tp = 41, 42, 43  --> 시외버스(inchon.gif, si.gif)
							Route_tp = 나머지 --> inchon.gif
						SI_FLAG = 나머지 --> 경기도
							Route_tp = 51,52, 53  --> 공항버스(airport.gif)
							Route_tp = 41, 42, 43  --> 시외버스(si.gif)
							Route_tp = 나머지 --> 이미지 없음
						 */
						if(stationRegionName.indexOf('서울')>=0){ //서울
							if(routeTypeCd == 51 || routeTypeCd == 52 || routeTypeCd == 53){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/4.png" alt="공항" />';
							}else if(routeTypeCd == 41 || routeTypeCd == 42 || routeTypeCd == 43){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/3.png" alt="시외" />';
							}else if(routeTypeCd == 11 || routeTypeCd == 21 || routeTypeCd == 16){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/7_1.png" alt="직좌" />';
							}else if(routeTypeCd == 14){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/7.png" alt="광역" />';	
							}else if(routeTypeCd == 12 ){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/5_1.png" alt="좌석" />';
							}else if(routeTypeCd == 30){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/9_7.png" alt="마을" />';	
							}else{
//								iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />';
								iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/6_1.png" alt="일반" />';
							}
						}else if(stationRegionName.indexOf('인천')>=0){ //인천
							if(routeTypeCd == 51 || routeTypeCd == 52 || routeTypeCd == 53){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/4.png" alt="공항" />';
							}else if(routeTypeCd == 41 || routeTypeCd == 42 || routeTypeCd == 43){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/3.png" alt="시외" />';
							}else if(routeTypeCd == 11 || routeTypeCd == 21 || routeTypeCd == 16){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/7_1.png" alt="직좌" />';
							}else if(routeTypeCd == 14){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/7.png" alt="광역" />';	
							}else if(routeTypeCd == 12 ){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/5_1.png" alt="좌석" />';
							}else if(routeTypeCd == 30){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/9_7.png" alt="마을" />';	
							}else{
//								iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />';
								iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/6_1.png" alt="일반" />';
							}
						}else{//경기도
							if(routeTypeCd == 51 || routeTypeCd == 52 || routeTypeCd == 53){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/4.png" alt="공항" />';
							}else if(routeTypeCd == 41 || routeTypeCd == 42 || routeTypeCd == 43){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/3.png" alt="시외" />';
							}else if(routeTypeCd == 11 || routeTypeCd == 21 || routeTypeCd == 16){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/7_1.png" alt="직좌" />';
							}else if(routeTypeCd == 14){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/7.png" alt="광역" />';	
							}else if(routeTypeCd == 12 ){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/5_1.png" alt="좌석" />';
							}else if(routeTypeCd == 30  ){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/9_7.png" alt="마을" />';
							}else{
//								iconImg = '';
								iconImg = '<img src="/gbis2014/images/ico/bus_type/6_1.png" alt="일반" />';
							}
						}
						
						if(stationRouteId == routeId && staOrder == stationStaOrder && updown_status == stationUpdownNum){
							//baepro_isRemainSeat(2)
							var isRemainSeat = false;
							//alert(routeTypeCd);
							if(routeId == "249000002"){ // 판타G버스 (자율주행버스) 노선타입 13번 but 빈자리수 표출 하드코딩
								isRemainSeat = true;
							}
							if(routeTypeCd==11 || routeTypeCd==12 || routeTypeCd==14 || routeTypeCd==16){
								// M6405,M6410,7790급,7800급,3200,3300,1008전,9401,9403,9404,9408,9701,9703,9707,9709,9714,9401공,9714공,9709공차,9711A
								var exRouteIds = "165000215,216000044,200000228,200000229,218000005,219000025,233000129,100100389,100100390,100100391,100100392,100100397,100100398,100100400,100100402,100100406,100100559,100100560,100100577,100100607";
								
								if(exRouteIds.indexOf(routeId)<0){
									isRemainSeat = true;
								}
							}
							
							var isDensity = false;
							
							var isDensity = false;
							if(routeTypeCd==13 || routeTypeCd==15 || routeTypeCd==21 || routeTypeCd==22 || routeTypeCd==23 ){ // 13, 15, 21, 22, 23
								//var isDensityIds = " 200000069,200000049,200000146,200000024,200000070,200000239,200000172,200000092,200000013,200000231,200000048,200000197,200000208,200000031,200000240,200000241,200000051,200000147,200000067,200000016,200000020,200000199,200000101,233000011,233000012,233000007,200000028,200000060,200000010,200000008,200000037,200000053,200000043,200000040,200000148,200000185,200000055,200000202,200000074,200000183,200000076,200000012,200000152,200000093,200000201,200000182,200000106,200000099,200000085,200000077,200000237,200000042,200000236,200000157,200000196,200000039,200000166,200000211,200000088,200000064,200000238,200000234,200000078,200000206,200000056,200000058,200000129,200000134,200000066,200000061,200000032,200000034,200000065,200000133,200000261,200000014,200000018,200000022,200000122,200000045,200000097,200000095,200000090,,200000239,200000268,200000103,200000029,200000054,200000186,200000025,200000023,200000107,200000144,233000087,200000266 ";
						 		if(stationRegionName!=null && stationRegionName.indexOf("서울")<0 && stationRegionName.indexOf("인천")<0 ){
									isDensity= true;
						 		}
						 		// 혼잡도 제공하지 않고 빈자리제공하는 노선 (예, 판타G )
						 		var exDensityIds = "249000002";
						 		if(exDensityIds.indexOf(routeId)>=0){
						 			isDensity = false;
								}
							}
							
							routeStat = true; //정류소 해당노선 있음

							stationRealtime += '<li>';
							stationRealtime += '<div class="s_bus_num">'+iconImg+'<a title="새 창으로 보기" href="javascript:busInfoView(\''+routeName+'\',\''+routeId+'\',\''+routeTypeCd+'\')"><strong class="'+className+'">'+routeName+'</strong></a><br />';
							if(stationRouteDestName.length > 13){
								stationRealtime += stationRouteDestName.substring(0,10)+ '.. 방면';
							}else{
								stationRealtime += stationRouteDestName+ ' 방면';
							}
							stationRealtime += '</div>';
							
							if(flag == 'STOP'){
								stationRealtime += '<div class="s_bus_time">1번째 : 운행종료<br />';
							}else if(flag == 'WAIT'){
								stationRealtime += '<div class="s_bus_time">1번째 : 회차점 대기중<br />';
							}else if(delayYn1 == "Y"){
								stationRealtime += '<div class="s_bus_time">1번째 : 회차점 대기중<br />';
							}else if(plateNo1 == "" && predictTime1 == ""){
								stationRealtime += '<div class="s_bus_time">1번째 : 도착예정정보 없음<br />';
							}else{
								if(predictTime1 == "0"){
									stationRealtime += '<div class="s_bus_time">1번째 : 약 <strong>1</strong>분 후 ('+locationNo1+'번째전)<br />';
									
											//if(routeName.indexOf('M') != -1){
											if(lowPlate1 == '6' && (nowtime2 > 640 && nowtime1 < 9)){
												stationRealtime += ' 예약버스';
											} else {
												if(isRemainSeat){
													if(remainSeatCnt1 != "-1" && remainSeatCnt1 != "" && remainSeatCnt1 != null && remainSeatCnt1 != undefined){
														stationRealtime += '빈자리 : <strong>'+remainSeatCnt1+'</strong>석 ';
													}else{
														stationRealtime += '빈자리 : 정보없음';
													}
												}
											}
											
											if(isDensity){
												if(density1 == 1){
													stationRealtime += '차내혼잡상태:<span class=\"color-density1\">여유</span>';
												}else if(density1 == 2){
													stationRealtime += '차내혼잡상태:<span class=\"color-density2\">보통</span>'; 
												}else if(density1 == 3){
													stationRealtime += '차내혼잡상태:<span class=\"color-density3\">혼잡</span>';
												}else if(density1 == 4){
													stationRealtime += '차내혼잡상태:<span class=\"color-density4\">매우혼잡</span>';
												}
											}
											
											if(lowPlate1 == '1'){
												if(isDensity) stationRealtime += ','; 
												stationRealtime += '  저상버스<br/>';
											}else if(lowPlate1 == '7'){
												if(isDensity) stationRealtime += ','; 
												stationRealtime += '  트롤리<br/>';
											}else if(lowPlate1 == '5'){
												if(isRemainSeat) stationRealtime += ','; 
												stationRealtime += '  전세버스<br/>';
											}else if(lowPlate1 == '2'){
												if(isRemainSeat) stationRealtime += ','; 
												stationRealtime += '  2층버스<br/>';
											} else {
//												if(plateType1 == '4'){
//													if(isRemainSeat) stationRealtime += ',';
//													stationRealtime += ' 2층버스<br/>';
//												} else {
													if(isRemainSeat){
														stationRealtime += '<br/>';
													} else if(isDensity && density1<5 && density1>0 ){
														stationRealtime += '<br/>';								
													}
//												}
											}
											
								}else{
									stationRealtime += '<div class="s_bus_time">1번째 : <strong>'+predictTime1+'</strong>분 후 ('+locationNo1+'번째전)<br />';
									
											//if(routeName.indexOf('M') != -1){
										if(lowPlate1 == '6' && (nowtime2 > 640 && nowtime1 < 9)){
											stationRealtime += ' 예약버스';
										} else {
											if(isRemainSeat){
												if(remainSeatCnt1 != "-1" && remainSeatCnt1 != "" && remainSeatCnt1 != null && remainSeatCnt1 != undefined){
													stationRealtime += '빈자리 : <strong>'+remainSeatCnt1+'</strong>석';
												}else{
													stationRealtime += '빈자리 : 정보없음';
												}
											}
										}
											
										if(isDensity){
											if(density1 == 1){
												stationRealtime += '차내혼잡상태:<span class=\"color-density1\">여유</span>';
											}else if(density1 == 2){
												stationRealtime += '차내혼잡상태:<span class=\"color-density2\">보통</span>'; 
											}else if(density1 == 3){
												stationRealtime += '차내혼잡상태:<span class=\"color-density3\">혼잡</span>';
											}else if(density1 == 4){
												stationRealtime += '차내혼잡상태:<span class=\"color-density4\">매우혼잡</span>';
											}
										}
										
										if(lowPlate1 == '1'){
											if(isDensity) stationRealtime += ',';
											stationRealtime += '  저상버스<br/>';
										}else if(lowPlate1 == '7'){
											if(isDensity) stationRealtime += ',';
											stationRealtime += '  트롤리<br/>';
										}else if(lowPlate1 == '5'){
											if(isRemainSeat) stationRealtime += ','; 
											stationRealtime += '  전세버스<br/>';	
										}else if(lowPlate1 == '2'){
											if(isRemainSeat) stationRealtime += ',';
											stationRealtime += ' 2층버스<br/>';
										} else {
//											if(plateType1 == '4'){
//												if(isRemainSeat) stationRealtime += ',';
//												stationRealtime += ' 2층버스<br/>';
//											} else {
												if(isRemainSeat){
													stationRealtime += '<br/>';
												} else if(isDensity && density1<5 && density1>0 ){
													stationRealtime += '<br/>';															
												}
//											}
										}
								}
							}
							
							if(flag == 'STOP'){
								
							}else if(flag == 'WAIT'){
								
							}else if(delayYn1 == "Y"){
								
							}else if(plateNo2 == ""){
								stationRealtime += '2번째 : 도착예정정보 없음<br />';
//							}else if(crowded1 != crowded2){
//								stationRealtime += '2번째 : 회차점 대기중<br />';
							}else{
								if(predictTime2 == "0"){
									stationRealtime += '2번째 : 약 <strong>1</strong>분 후 ('+locationNo2+'번째전)<br />';
									
									if(lowPlate2 == '6' && (nowtime2 > 640 && nowtime1 < 9)){
										stationRealtime += ' 예약버스';	
									} else {
										if(isRemainSeat){
											if(remainSeatCnt2 != "-1" && remainSeatCnt2 != "" && remainSeatCnt2 != null && remainSeatCnt2 != undefined){
												stationRealtime += '빈자리 : <strong>'+remainSeatCnt2+'</strong>석 ';
											}else{
												stationRealtime += '빈자리 : 정보없음';
											}
										}
										
									}
											
									if(isDensity){
										if(density2 == 1){
											stationRealtime += '차내혼잡상태:<span class=\"color-density1\">여유</span>';
										}else if(density2 == 2){
											stationRealtime += '차내혼잡상태:<span class=\"color-density2\">보통</span>'; 
										}else if(density2 == 3){
											stationRealtime += '차내혼잡상태:<span class=\"color-density3\">혼잡</span>';
										}else if(density2 == 4){
											stationRealtime += '차내혼잡상태:<span class=\"color-density4\">매우혼잡</span>';
										}
									}
									
									if(lowPlate2 == '1'){
										if(isDensity) stationRealtime += ',';
										stationRealtime += '  저상버스<br/>';
									}else if(lowPlate2 == '7'){
										if(isDensity) stationRealtime += ','; 
										stationRealtime += '  트롤리<br/>';
									}else if(lowPlate2 == '5'){
										if(isRemainSeat) stationRealtime += ','; 
										stationRealtime += '  전세버스<br/>';	
									}else if(lowPlate2 == '2'){
										if(isRemainSeat) stationRealtime += ',';
										stationRealtime += ' 2층버스<br/>';
									} else {
//										if(plateType2 == '4'){
//											if(isRemainSeat) stationRealtime += ',';
//											stationRealtime += ' 2층버스<br/>';
//										} else {
											if(isRemainSeat){
												stationRealtime += '<br/>';
											} else if(isDensity && density2<5 && density2>0 ){
												stationRealtime += '<br/>';	
											}
//										}
									}
								}else{
									stationRealtime += '2번째 : <strong>'+predictTime2+'</strong>분 후 ('+locationNo2+'번째전)<br />';
									
									if(lowPlate2 == '6' && (nowtime2 > 640 && nowtime1 < 9)){
										stationRealtime += ' 예약버스';
									} else {
										if(isRemainSeat){
											if(remainSeatCnt2 != "-1" && remainSeatCnt2 != "" && remainSeatCnt2 != null && remainSeatCnt2 != undefined){
												stationRealtime += '빈자리 : <strong>'+remainSeatCnt2+'</strong>석 ';
											}else{
												stationRealtime += '빈자리 : 정보없음';
											}
										}
									}
											
									if(isDensity){
										if(density2 == 1){
											stationRealtime += '차내혼잡상태:<span class=\"color-density1\">여유</span>';
										}else if(density2 == 2){
											stationRealtime += '차내혼잡상태:<span class=\"color-density2\">보통</span>'; 
										}else if(density2 == 3){
											stationRealtime += '차내혼잡상태:<span class=\"color-density3\">혼잡</span>';
										}else if(density2 == 4){
											stationRealtime += '차내혼잡상태:<span class=\"color-density4\">매우혼잡</span>';
										}
									}
									
									if(lowPlate2 == '1'){
										if(isDensity) stationRealtime += ',';
										stationRealtime += '  저상버스<br/>';
									}else if(lowPlate2 == '7'){
										if(isDensity) stationRealtime += ',';
										stationRealtime += '  트롤리<br/>';
									}else if(lowPlate2 == '5'){
										if(isRemainSeat) stationRealtime += ','; 
										stationRealtime += '  전세버스<br/>';
									}else if(lowPlate2 == '2'){
										if(isRemainSeat) stationRealtime += ',';
										stationRealtime += ' 2층버스<br/>';
									} else {
//										if(plateType2 == '4'){
//											if(isRemainSeat) stationRealtime += ',';
//											stationRealtime += ' 2층버스<br/>';
//										} else {
											if(isRemainSeat){
												stationRealtime += '<br/>';
											} else if(isDensity && density2<5 && density2>0 ){
												stationRealtime += '<br/>';	
											}
//										}
									}
								}
							}
							
							stationRealtime += '</div>';
							stationRealtime += '</li>';
							
							if(predictTime1 != "" && predictTime1 < 4) {
								stationRealtimeScroll += '<li style="width:43px">'+routeName+'</li>';
							}
						}
						
					});
				}
			});
			
			// 정류소에 해당 노선 도착정보 없었을 경우 
			if(!routeStat && route_name && !localBusStation){	
				$.each(busStationInfo,function(i){
					
					var stationRouteId = busStationInfo[i].routeId;
					var stationRouteName = busStationInfo[i].routeName;
					var stationStaOrder = busStationInfo[i].staOrder;
					var stationUpdownNum = busStationInfo[i].updownNum;
					var stationRouteDestName = busStationInfo[i].routeDestName;
					var routeTypeCd = busStationInfo[i].routeTypeCd;
					var siFlag = 0;
					var stationRegionName = busStationInfo[i].regionName;
					
					if(stationRouteName==route_name && stationUpdownNum == updown_status){
						
						if(routeTypeCd == 11 || routeTypeCd == 21 || routeTypeCd == 14 || routeTypeCd == 16){
							className = "num_red";
						}else if(routeTypeCd == 12){
							className = "num_blue";
						}else if(routeTypeCd == 30  ){
							className = "num_yellow";
						}else if(routeTypeCd == 41 || routeTypeCd == 42 || routeTypeCd == 43){
							className = "num_purple";
						}else if(routeTypeCd == 51 || routeTypeCd == 52 || routeTypeCd == 53){
							className = "num_gray";
						}else{
							className = "num_green";
						}
						
						if(siFlag == 1){ //서울
							if(routeTypeCd == 51 || routeTypeCd == 52 || routeTypeCd == 53){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/4.png" alt="공항" />';
							}else if(routeTypeCd == 41 || routeTypeCd == 42 || routeTypeCd == 43){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/3.png" alt="시외" />';
							}else if(routeTypeCd == 11 || routeTypeCd == 21 || routeTypeCd == 16){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/7_1.png" alt="직좌" />';
							}else if(routeTypeCd == 14){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/7.png" alt="광역" />';	
							}else if(routeTypeCd == 12 ){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/5_1.png" alt="좌석" />';
							}else if(routeTypeCd == 30){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/9_7.png" alt="마을" />';	
							}else{
//								iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />';
								iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/6_1.png" alt="일반" />';
							}
						}else if(siFlag == 3){ //인천
							if(routeTypeCd == 51 || routeTypeCd == 52 || routeTypeCd == 53){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/4.png" alt="공항" />';
							}else if(routeTypeCd == 41 || routeTypeCd == 42 || routeTypeCd == 43){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/3.png" alt="시외" />';
							}else if(routeTypeCd == 11 || routeTypeCd == 21 || routeTypeCd == 16){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/7_1.png" alt="직좌" />';
							}else if(routeTypeCd == 14){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/7.png" alt="광역" />';	
							}else if(routeTypeCd == 12 ){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/5_1.png" alt="좌석" />';
							}else if(routeTypeCd == 30){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/9_7.png" alt="마을" />';	
							}else{
//								iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />';
								iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/6_1.png" alt="일반" />';
							}
						}else{//경기도
							if(routeTypeCd == 51 || routeTypeCd == 52 || routeTypeCd == 53){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/4.png" alt="공항" />';
							}else if(routeTypeCd == 41 || routeTypeCd == 42 || routeTypeCd == 43){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/3.png" alt="시외" />';
							}else if(routeTypeCd == 11 || routeTypeCd == 21 || routeTypeCd == 16){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/7_1.png" alt="직좌" />';
							}else if(routeTypeCd == 14){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/7.png" alt="광역" />';	
							}else if(routeTypeCd == 12 ){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/5_1.png" alt="좌석" />';
							}else if(routeTypeCd == 30  ){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/9_7.png" alt="마을" />';
							}else{
//								iconImg = '';
								iconImg = '<img src="/gbis2014/images/ico/bus_type/6_1.png" alt="일반" />';
							}
						}
				
						stationRealtime += '<li>';
						stationRealtime += '<div class="s_bus_num">'+iconImg+'<strong class="'+className+'">'+route_name+'</strong><br />';
						if(stationRouteDestName.length > 10){
							stationRealtime += stationRouteDestName.substring(0,9)+ ' 방면';
						}else{
							stationRealtime += stationRouteDestName+ ' 방면';
						}
						stationRealtime += '</div>';
						stationRealtime += '<div class="s_bus_time">1번째 : 도착예정정보 없음<br />';
						stationRealtime += '2번째 : 도착예정정보 없음<br />';
						stationRealtime += '</div>';
						stationRealtime += '</li>';
						routeStat = true;
					}
				});
				if(updown_status != undefined && updown_status != null && updown_status != "" && !routeStat && route_name && !localBusStation ){
					stationRealtime += '<li>';
					stationRealtime += '<div class="s_bus_num"><strong class="">'+route_name+'</strong><br /></div>';
					stationRealtime += '<div class="s_bus_time">1번째 : 도착예정정보 없음<br />';
					stationRealtime += '2번째 : 도착예정정보 없음<br />';
					stationRealtime += '</div>';
					stationRealtime += '</li>';
				}
			}
			
			// 해당 정류소 기타 노선 표출 : 노선 이름 다른 노선들 + 동일 노선이지만 up down flag 다른 노선 (중복노선 정류소 처리) 
			$.each(busStationInfo,function(i){
				
				var stationRouteId = busStationInfo[i].routeId;
				var stationRouteName = busStationInfo[i].routeName;
				var stationRouteDestName = busStationInfo[i].routeDestName;
				var stationStaOrder = busStationInfo[i].staOrder;
				var stationUpdownNum = busStationInfo[i].updownNum;
				var stationRegionName = busStationInfo[i].regionName;
				
				//노선명 없을 시 일반 정류소 표출
				if(route_name != stationRouteName){
					
					arrivalInfoStat = false; //도착예정목록에 노선정보가 있는지 유무 초기화
					
					$.each(busArrivalInfo,function(i){
						
						var routeId = busArrivalInfo[i].routeId;
						var routeTypeCd = busArrivalInfo[i].routeTypeCd;
						var routeName = busArrivalInfo[i].routeName;
						var routeDestName = busArrivalInfo[i].routeDestName;
						var flag = busArrivalInfo[i].flag;
						var plateNo1 = busArrivalInfo[i].plateNo1;
						var predictTime1 = busArrivalInfo[i].predictTime1;
						var locationNo1 = busArrivalInfo[i].locationNo1;
						var remainSeatCnt1 = busArrivalInfo[i].remainSeatCnt1;
						var delayYn1 = busArrivalInfo[i].delayYn1;
						var plateNo2 = busArrivalInfo[i].plateNo2;
						var predictTime2 = busArrivalInfo[i].predictTime2;
						var locationNo2 = busArrivalInfo[i].locationNo2;
						var remainSeatCnt2 = busArrivalInfo[i].remainSeatCnt2;
						var delayYn2 = busArrivalInfo[i].delayYn2;
						var crowded1 = busArrivalInfo[i].crowded1;
						var crowded2 = busArrivalInfo[i].crowded2;
						var siFlag = 0;
						var staOrder = busArrivalInfo[i].staOrder;
						var runBusFlag = busArrivalInfo[i].runBusFlag;
						
						var lowPlate1 = busArrivalInfo[i].lowPlate1;
						var lowPlate2 = busArrivalInfo[i].lowPlate2;
						
						var plateType1 = busArrivalInfo[i].plateType1;
						var plateType2 = busArrivalInfo[i].plateType2;
						
						var className = "";
						var iconImg = "";
						
						var density1 = busArrivalInfo[i].density1;
						var density2 = busArrivalInfo[i].density2;
						
						//baepro_isRemainSeat(3)
						var isRemainSeat = false;
						//alert(routeTypeCd);
						if(routeId == "249000002"){ // 판타G버스 (자율주행버스) 노선타입 13번 but 빈자리수 표출 하드코딩
							isRemainSeat = true;
						}
						if(routeTypeCd==11 || routeTypeCd==12 || routeTypeCd==14 || routeTypeCd==16){
							// M6405,M6410,7790급,7800급,3200,3300,1008전,9401,9403,9404,9408,9701,9703,9707,9709,9714,9401공,9714공,9709공차,9711A
							var exRouteIds = "165000215,216000044,200000228,200000229,218000005,219000025,233000129,100100389,100100390,100100391,100100392,100100397,100100398,100100400,100100402,100100406,100100559,100100560,100100577,100100607";
							
							if(exRouteIds.indexOf(routeId)<0){
								isRemainSeat = true;
							}
						}
						
						var isDensity = false;
						
						var isDensity = false;
//						if(routeTypeCd==13 || routeTypeCd==15 || routeTypeCd==21 || routeTypeCd==22 || routeTypeCd==23 ){ // 13, 15, 21, 22, 23
//							var isDensityIds = " 200000069,200000049,200000146,200000024,200000070,200000239,200000172,200000092,200000013,200000231,200000048,200000197,200000208,200000031,200000240,200000241,200000051,200000147,200000067,200000016,200000020,200000199,200000101,233000011,233000012,233000007,200000028,200000060,200000010,200000008,200000037,200000053,200000043,200000040,200000148,200000185,200000055,200000202,200000074,200000183,200000076,200000012,200000152,200000093,200000201,200000182,200000106,200000099,200000085,200000077,200000237,200000042,200000236,200000157,200000196,200000039,200000166,200000211,200000088,200000064,200000238,200000234,200000078,200000206,200000056,200000058,200000129,200000134,200000066,200000061,200000032,200000034,200000065,200000133,200000261,200000014,200000018,200000022,200000122,200000045,200000097,200000095,200000090,200000239,200000268,200000103,200000029,200000054,200000186,200000025,200000023,200000107,200000144,233000087,200000266 ";
//					 		if(stationRegionName.indexOf("서울")<0 && stationRegionName.indexOf("인천")<0 ){
//								isDensity= true;
//					 		}
//							
//						}
						
						if(routeTypeCd==13 || routeTypeCd==15 || routeTypeCd==21 || routeTypeCd==22 || routeTypeCd==23 ){ // 13, 15, 21, 22, 23
							//var isDensityIds = " 200000069,200000049,200000146,200000024,200000070,200000239,200000172,200000092,200000013,200000231,200000048,200000197,200000208,200000031,200000240,200000241,200000051,200000147,200000067,200000016,200000020,200000199,200000101,233000011,233000012,233000007,200000028,200000060,200000010,200000008,200000037,200000053,200000043,200000040,200000148,200000185,200000055,200000202,200000074,200000183,200000076,200000012,200000152,200000093,200000201,200000182,200000106,200000099,200000085,200000077,200000237,200000042,200000236,200000157,200000196,200000039,200000166,200000211,200000088,200000064,200000238,200000234,200000078,200000206,200000056,200000058,200000129,200000134,200000066,200000061,200000032,200000034,200000065,200000133,200000261,200000014,200000018,200000022,200000122,200000045,200000097,200000095,200000090,,200000239,200000268,200000103,200000029,200000054,200000186,200000025,200000023,200000107,200000144,233000087,200000266 ";
					 		if(stationRegionName!=null && stationRegionName.indexOf("서울")<0 && stationRegionName.indexOf("인천")<0 ){
								isDensity= true;
					 		}
					 		// 혼잡도 제공하지 않고 빈자리제공하는 노선 (예, 판타G )
					 		var exDensityIds = "249000002";
					 		if(exDensityIds.indexOf(routeId)>=0){
					 			isDensity = false;
							}
						}
			            
			            //노선번호 색상
						/*
						Route_tp = 11, 21, 14  --> red(직행)
						Route_tp = 12  --> blue
						Route_tp = 30  --> yellow
						Route_tp = 41, 42, 43  --> violet(시외)
						Route_tp = 51, 52, 53  --> grey (공항)
						나머지 --> green
						 */
						if(routeTypeCd == 11 || routeTypeCd == 21 || routeTypeCd == 14 || routeTypeCd == 16){
							className = "num_red";
						}else if(routeTypeCd == 12){
							className = "num_blue";
						}else if(routeTypeCd == 30){
							className = "num_yellow";
						}else if(routeTypeCd == 41 || routeTypeCd == 42 || routeTypeCd == 43){
							className = "num_purple";
						}else if(routeTypeCd == 51 || routeTypeCd == 52 || routeTypeCd == 53){
							className = "num_gray";
						}else{
							className = "num_green";
						}
					
						//노선 아이콘
						/*
						SI_FLAG = 1 --> 서울
							Route_tp = 51,52, 53  --> 공항버스(seoul.gif, airport.gif)
							Route_tp = 41, 42, 43  --> 시외버스(seoul.gif, si.gif)
							Route_tp = 나머지 --> seoul.gif
						SI_FLAG = 3 --> 인천
							Route_tp = 51,52, 53  --> 공항버스(inchon.gif airport.gif)
							Route_tp = 41, 42, 43  --> 시외버스(inchon.gif, si.gif)
							Route_tp = 나머지 --> inchon.gif
						SI_FLAG = 나머지 --> 경기도
							Route_tp = 51,52, 53  --> 공항버스(airport.gif)
							Route_tp = 41, 42, 43  --> 시외버스(si.gif)
							Route_tp = 나머지 --> 이미지 없음
						 */
						if(siFlag == 1){ //서울
							if(routeTypeCd == 51 || routeTypeCd == 52 || routeTypeCd == 53){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/4.png" alt="공항" />';
							}else if(routeTypeCd == 41 || routeTypeCd == 42 || routeTypeCd == 43){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/3.png" alt="시외" />';
							}else if(routeTypeCd == 11 || routeTypeCd == 21 || routeTypeCd == 16){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/7_1.png" alt="직좌" />';
							}else if(routeTypeCd == 14){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/7.png" alt="광역" />';	
							}else if(routeTypeCd == 12 ){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/5_1.png" alt="좌석" />';
							}else if(routeTypeCd == 30){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/9_7.png" alt="마을" />';		
							}else{
//								iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />';
								iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/6_1.png" alt="일반" />';
							}
						}else if(siFlag == 3){ //인천
							if(routeTypeCd == 51 || routeTypeCd == 52 || routeTypeCd == 53){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/4.png" alt="공항" />';
							}else if(routeTypeCd == 41 || routeTypeCd == 42 || routeTypeCd == 43){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/3.png" alt="시외" />';
							}else if(routeTypeCd == 11 || routeTypeCd == 21 || routeTypeCd == 16){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/7_1.png" alt="직좌" />';
							}else if(routeTypeCd == 14){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/7.png" alt="광역" />';	
							}else if(routeTypeCd == 12 ){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/5_1.png" alt="좌석" />';
							}else if(routeTypeCd == 30){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/9_7.png" alt="마을" />';	
							}else{
//								iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />';
								iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/6_1.png" alt="일반" />';
							}
						}else{//경기도
							if(routeTypeCd == 51 || routeTypeCd == 52 || routeTypeCd == 53){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/4.png" alt="공항" />';
							}else if(routeTypeCd == 41 || routeTypeCd == 42 || routeTypeCd == 43){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/3.png" alt="시외" />';
							}else if(routeTypeCd == 30  ){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/9_7.png" alt="마을" />';
							}else if(routeTypeCd == 11 || routeTypeCd == 21 || routeTypeCd == 16){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/7_1.png" alt="직좌" />';
							}else if(routeTypeCd == 14){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/7.png" alt="광역" />';	
							}else if(routeTypeCd == 12 ){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/5_1.png" alt="좌석" />';
							}else{
//								iconImg = '';
								iconImg = '<img src="/gbis2014/images/ico/bus_type/6_1.png" alt="일반" />';
							}
						}
						
						if(stationRouteId == routeId && staOrder==stationStaOrder){
							
							arrivalInfoStat = true; //도착예정목록에 노선정보 있음
							
							stationRealtime += '<li>';

							stationRealtime += '<div class="s_bus_num">'+iconImg+'<a title="새 창으로 보기" href="javascript:busInfoView(\''+routeName+'\',\''+routeId+'\',\''+routeTypeCd+'\')"><strong class="'+className+'">'+routeName+'</strong></a><br />';
							if(stationRouteDestName.length > 13){
								stationRealtime += stationRouteDestName.substring(0,10)+ '.. 방면';
							}else{
								stationRealtime += stationRouteDestName+ ' 방면';
							}
							stationRealtime += '</div>';
							
							if(flag == 'STOP'){
								stationRealtime += '<div class="s_bus_time">1번째 : 운행종료<br />';
							}else if(flag == 'WAIT'){
								stationRealtime += '<div class="s_bus_time">1번째 : 회차점 대기중<br />';
							}else if(delayYn1 == "Y"){
								stationRealtime += '<div class="s_bus_time">1번째 : 회차점 대기중<br />';
							}else if(plateNo1 == "" && predictTime1 == ""){
								stationRealtime += '<div class="s_bus_time">1번째 : 도착예정정보 없음<br />';
							}else{
								if(predictTime1 == "0"){
									stationRealtime += '<div class="s_bus_time">1번째 : 약 <strong>1</strong>분 후 ('+locationNo1+'번째전)<br />';
									
									if(lowPlate1 == '6' && (nowtime2 > 640 && nowtime1 < 9)){
										stationRealtime += ' 예약버스';
									} else {
										if(isRemainSeat){
											if(remainSeatCnt1 != "-1" && remainSeatCnt1 != "" && remainSeatCnt1 != null && remainSeatCnt1 != undefined){
												stationRealtime += '빈자리 : <strong>'+remainSeatCnt1+'</strong>석';
											}else{
												stationRealtime += '빈자리 : 정보없음';
											}
										}										
									}
									if(isDensity){
										if(density1 == 1){
											stationRealtime += '차내혼잡상태:<span class=\"color-density1\">여유</span>';
										}else if(density1 == 2){
											stationRealtime += '차내혼잡상태:<span class=\"color-density2\">보통</span>'; 
										}else if(density1 == 3){
											stationRealtime += '차내혼잡상태:<span class=\"color-density3\">혼잡</span>';
										}else if(density1 == 4){
											stationRealtime += '차내혼잡상태:<span class=\"color-density4\">매우혼잡</span>';
										}
									}
									
									if(lowPlate1 == '1'){
										if(isDensity) stationRealtime += ',';
										stationRealtime += '  저상버스<br/>';
									}else if(lowPlate1 == '7'){
										if(isDensity) stationRealtime += ',';
										stationRealtime += '  트롤리<br/>';
									}else if(lowPlate1 == '5'){
										if(isRemainSeat) stationRealtime += ','; 
										stationRealtime += '  전세버스<br/>';
									}else if(lowPlate1 == '2'){
										if(isRemainSeat) stationRealtime += ',';
										stationRealtime += ' 2층버스<br/>';
									} else {
//										if(plateType1 == '4'){
//											if(isRemainSeat) stationRealtime += ',';
//											stationRealtime += ' 2층버스<br/>';
//										} else {
											if(isRemainSeat){
												stationRealtime += '<br/>';
											} else if(isDensity && density1<5 && density1>0 ){
												stationRealtime += '<br/>';	
											}
//										}
									}
								}else{
									stationRealtime += '<div class="s_bus_time">1번째 : <strong>'+predictTime1+'</strong>분 후 ('+locationNo1+'번째전)<br />';
									
									if(lowPlate1 == '6' && (nowtime2 > 640 && nowtime1 < 9)){
										stationRealtime += ' 예약버스';
									} else {
										if(isRemainSeat){
											if(remainSeatCnt1 != "-1" && remainSeatCnt1 != "" && remainSeatCnt1 != null && remainSeatCnt1 != undefined){
												stationRealtime += '빈자리 : <strong>'+remainSeatCnt1+'</strong>석';
											}else{
												stationRealtime += '빈자리 : 정보없음';
											}
										}
									}
									
									if(isDensity){
										if(density1 == 1){
											stationRealtime += '차내혼잡상태:<span class=\"color-density1\">여유</span>';
										}else if(density1 == 2){
											stationRealtime += '차내혼잡상태:<span class=\"color-density2\">보통</span>'; 
										}else if(density1 == 3){
											stationRealtime += '차내혼잡상태:<span class=\"color-density3\">혼잡</span>';
										}else if(density1 == 4){
											stationRealtime += '차내혼잡상태:<span class=\"color-density4\">매우혼잡</span>';
										}
									}
									
									if(lowPlate1 == '1'){
										if(isDensity) stationRealtime += ',';
										stationRealtime += '  저상버스<br/>';
									}else if(lowPlate1 == '7'){
										if(isDensity) stationRealtime += ',';
										stationRealtime += '  트롤리<br/>';
									}else if(lowPlate1 == '5'){
										if(isRemainSeat) stationRealtime += ','; 
										stationRealtime += '  전세버스<br/>';
									}else if(lowPlate1 == '2'){
										if(isRemainSeat) stationRealtime += ',';
										stationRealtime += ' 2층버스<br/>';
									} else {
//										if(plateType1 == '4'){
//											if(isRemainSeat) stationRealtime += ',';
//											stationRealtime += ' 2층버스<br/>';
//										} else {
											if(isRemainSeat){
												stationRealtime += '<br/>';
											} else if(isDensity && density1<5 && density1>0 ){
												stationRealtime += '<br/>';	
											}
//										}
									}
								}
							}
							
							if(flag == 'STOP'){
								
							}else if(flag == 'WAIT'){
								
							}else if(delayYn1 == "Y"){
								
							}else if(plateNo2 == ""){
								stationRealtime += '2번째 : 도착예정정보 없음<br />';
//							}else if(crowded1 != crowded2){
//								stationRealtime += '2번째 : 회차점 대기중<br />';
							}else{
								if(predictTime2 == "0"){
									stationRealtime += '2번째 : 약 <strong>1</strong>분 후 ('+locationNo2+'번째전)<br />';
									
									if(lowPlate2 == '6' && (nowtime2 > 640 && nowtime1 < 9)){
										stationRealtime += ' 예약버스';
									} else {
										if(isRemainSeat){
											if(remainSeatCnt2 != "-1" && remainSeatCnt2 != "" && remainSeatCnt2 != null && remainSeatCnt2 != undefined){
												stationRealtime += '빈자리 : <strong>'+remainSeatCnt2+'</strong>석';
											}else{
												stationRealtime += '빈자리 : 정보없음';
											}
										}										
									}
									if(isDensity){
										if(density2 == 1){
											stationRealtime += '차내혼잡상태:<span class=\"color-density1\">여유</span>';
										}else if(density2 == 2){
											stationRealtime += '차내혼잡상태:<span class=\"color-density2\">보통</span>'; 
										}else if(density2 == 3){
											stationRealtime += '차내혼잡상태:<span class=\"color-density3\">혼잡</span>';
										}else if(density2 == 4){
											stationRealtime += '차내혼잡상태:<span class=\"color-density4\">매우혼잡</span>';
										}
									}
									
									if(lowPlate2 == '1'){
										if(isDensity) stationRealtime += ',';
										stationRealtime += '  저상버스<br/>';
									} else if(lowPlate2 == '7'){
										if(isDensity) stationRealtime += ',';
										stationRealtime += '  트롤리<br/>';
									}else if(lowPlate2 == '5'){
										if(isRemainSeat) stationRealtime += ','; 
										stationRealtime += '  전세버스<br/>';
									}else if(lowPlate2 == '2'){
										if(isRemainSeat) stationRealtime += ',';
										stationRealtime += ' 2층버스)<br/>';
									}else {
//										if(plateType2 == '4'){
//											if(isRemainSeat) stationRealtime += ',';
//											stationRealtime += ' 2층버스)<br/>';
//										} else {
											if(isRemainSeat){
												stationRealtime += '<br/>';
											} else if(isDensity && density2<5 && density2>0 ){
												stationRealtime += '<br/>';	
											}
//										}
									}
								}else{
									stationRealtime += '2번째 : <strong>'+predictTime2+'</strong>분 후 ('+locationNo2+'번째전)<br />';
									
									if(lowPlate2 == '6' && (nowtime2 > 640 && nowtime1 < 9)){
										stationRealtime += ' 예약버스';
									} else {
										if(isRemainSeat){
											if(remainSeatCnt2 != "-1" && remainSeatCnt2 != "" && remainSeatCnt2 != null && remainSeatCnt2 != undefined){
												stationRealtime += '빈자리 : <strong>'+remainSeatCnt2+'</strong>석';
											}else{
												stationRealtime += '빈자리 : 정보없음';
											}
										}
									}
									if(isDensity){
										if(density2 == 1){
											stationRealtime += '차내혼잡상태:<span class=\"color-density1\">여유</span>';
										}else if(density2 == 2){
											stationRealtime += '차내혼잡상태:<span class=\"color-density2\">보통</span>'; 
										}else if(density2 == 3){
											stationRealtime += '차내혼잡상태:<span class=\"color-density3\">혼잡</span>';
										}else if(density2 == 4){
											stationRealtime += '차내혼잡상태:<span class=\"color-density4\">매우혼잡</span>';
										}
									}
									if(lowPlate2 == '1'){
										if(isDensity) stationRealtime += ',';
										stationRealtime += '  저상버스<br/>';
									}else if(lowPlate2 == '7'){
										if(isDensity) stationRealtime += ',';
										stationRealtime += '  트롤리<br/>';
									}else if(lowPlate2 == '5'){
										if(isRemainSeat) stationRealtime += ','; 
										stationRealtime += '  전세버스<br/>';
									}else if(lowPlate2 == '2'){
										if(isRemainSeat) stationRealtime += ',';
										stationRealtime += ' 2층버스<br/>';
									} else {
//										if(plateType2 == '4'){
//											if(isRemainSeat) stationRealtime += ',';
//											stationRealtime += ' 2층버스<br/>';
//										} else {
											if(isRemainSeat){
												stationRealtime += '<br/>';
											} else if(isDensity && density2<5 && density2>0 ){
												stationRealtime += '<br/>';	
											}
//										}
									}
								}
							}
							
							stationRealtime += '</div>';
							stationRealtime += '</li>';
							
							if(predictTime1 != "" && predictTime1 < 4) {
								stationRealtimeScroll += '<li style="width:43px">'+routeName+'</li>';
							}
						}
					});
					
					//도착예정목록에 해당노선 없을 시  busInfoView()추가
					if(!arrivalInfoStat){
						
						var routeTypeCd = busStationInfo[i].routeTypeCd;
						var siFlag = 0
						
						if(routeTypeCd == 11 || routeTypeCd == 21 || routeTypeCd == 14 || routeTypeCd == 16){
							className = "num_red";
						}else if(routeTypeCd == 12){
							className = "num_blue";
						}else if(routeTypeCd == 30){
							className = "num_yellow";
						}else if(routeTypeCd == 41 || routeTypeCd == 42 || routeTypeCd == 43){
							className = "num_purple";
						}else if(routeTypeCd == 51 || routeTypeCd == 52 || routeTypeCd == 53){
							className = "num_gray";
						}else{
							className = "num_green";
						}
					
						//노선 아이콘
						/*
						SI_FLAG = 1 --> 서울
							Route_tp = 51,52, 53  --> 공항버스(seoul.gif, airport.gif)
							Route_tp = 41, 42, 43  --> 시외버스(seoul.gif, si.gif)
							Route_tp = 나머지 --> seoul.gif
						SI_FLAG = 3 --> 인천
							Route_tp = 51,52, 53  --> 공항버스(inchon.gif airport.gif)
							Route_tp = 41, 42, 43  --> 시외버스(inchon.gif, si.gif)
							Route_tp = 나머지 --> inchon.gif
						SI_FLAG = 나머지 --> 경기도
							Route_tp = 51,52, 53  --> 공항버스(airport.gif)
							Route_tp = 41, 42, 43  --> 시외버스(si.gif)
							Route_tp = 나머지 --> 이미지 없음
						 */
						if(siFlag == 1){ //서울
							if(routeTypeCd == 51 || routeTypeCd == 52 || routeTypeCd == 53){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/4.png" alt="공항" />';
							}else if(routeTypeCd == 41 || routeTypeCd == 42 || routeTypeCd == 43){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/3.png" alt="시외" />';
							}else if(routeTypeCd == 11 || routeTypeCd == 21 || routeTypeCd == 16){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/7_1.png" alt="직좌" />';
							}else if(routeTypeCd == 14){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/7.png" alt="광역" />';	
							}else if(routeTypeCd == 12 ){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/5_1.png" alt="좌석" />';
							}else if(routeTypeCd == 30){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/9_7.png" alt="마을" />';		
							}else{
//								iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />';
								iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/6_1.png" alt="일반" />';
							}
						}else if(siFlag == 3){ //인천
							if(routeTypeCd == 51 || routeTypeCd == 52 || routeTypeCd == 53){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/4.png" alt="공항" />';
							}else if(routeTypeCd == 41 || routeTypeCd == 42 || routeTypeCd == 43){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/3.png" alt="시외" />';
							}else if(routeTypeCd == 11 || routeTypeCd == 21 || routeTypeCd == 16){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/7_1.png" alt="직좌" />';
							}else if(routeTypeCd == 14){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/7.png" alt="광역" />';	
							}else if(routeTypeCd == 12 ){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/5_1.png" alt="좌석" />';
							}else if(routeTypeCd == 30){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/9_7.png" alt="마을" />';	
							}else{
//								iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />';
								iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/6_1.png" alt="일반" />';
							}
						}else{//경기도
							if(routeTypeCd == 51 || routeTypeCd == 52 || routeTypeCd == 53){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/4.png" alt="공항" />';
							}else if(routeTypeCd == 41 || routeTypeCd == 42 || routeTypeCd == 43){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/3.png" alt="시외" />';
							}else if(routeTypeCd == 30  ){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/9_7.png" alt="마을" />';
							}else if(routeTypeCd == 11 || routeTypeCd == 21 || routeTypeCd == 16){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/7_1.png" alt="직좌" />';
							}else if(routeTypeCd == 14){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/7.png" alt="광역" />';	
							}else if(routeTypeCd == 12 ){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/5_1.png" alt="좌석" />';
							}else{
//								iconImg = '';
								iconImg = '<img src="/gbis2014/images/ico/bus_type/6_1.png" alt="일반" />';
							}
						}
						
						stationRealtime += '<li>';
						stationRealtime += '<div class="s_bus_num">'+iconImg+'<a title="새 창으로 보기" href="javascript:busInfoView(\''+stationRouteName+'\', \''+stationRouteId+'\')"><strong class="'+className+'">'+stationRouteName+'</strong></a><br />';
						if(stationRouteDestName.length > 13){
							stationRealtime += stationRouteDestName.substring(0,10)+ '.. 방면';
						}else{
							stationRealtime += stationRouteDestName+ ' 방면';
						}
						stationRealtime += '</div>';
						
						stationRealtime += '<div class="s_bus_time">1번째 : 도착예정정보 없음<br />';
						stationRealtime += '2번째 : 도착예정정보 없음<br />';
						stationRealtime += '</div>';
						stationRealtime += '</li>';
					}
				} else if (route_name == stationRouteName && updown_status != stationUpdownNum){
					
					arrivalInfoStat = false; //도착예정목록에 노선정보가 있는지 유무 초기화
					
					$.each(busArrivalInfo,function(i){
						
						var routeId = busArrivalInfo[i].routeId;
						var routeTypeCd = busArrivalInfo[i].routeTypeCd;
						var routeName = busArrivalInfo[i].routeName;
						var routeDestName = busArrivalInfo[i].routeDestName;
						var flag = busArrivalInfo[i].flag;
						var plateNo1 = busArrivalInfo[i].plateNo1;
						var predictTime1 = busArrivalInfo[i].predictTime1;
						var locationNo1 = busArrivalInfo[i].locationNo1;
						var remainSeatCnt1 = busArrivalInfo[i].remainSeatCnt1;
						var delayYn1 = busArrivalInfo[i].delayYn1;
						var plateNo2 = busArrivalInfo[i].plateNo2;
						var predictTime2 = busArrivalInfo[i].predictTime2;
						var locationNo2 = busArrivalInfo[i].locationNo2;
						var remainSeatCnt2 = busArrivalInfo[i].remainSeatCnt2;
						var delayYn2 = busArrivalInfo[i].delayYn2;
						var crowded1 = busArrivalInfo[i].crowded1;
						var crowded2 = busArrivalInfo[i].crowded2;
						var siFlag = 0;
						var staOrder = busArrivalInfo[i].staOrder;
						var runBusFlag = busArrivalInfo[i].runBusFlag;
						
						var lowPlate1 = busArrivalInfo[i].lowPlate1;
						var lowPlate2 = busArrivalInfo[i].lowPlate2;
						
						var plateType1 = busArrivalInfo[i].plateType1;
						var plateType2 = busArrivalInfo[i].plateType2;
						
						var className = "";
						var iconImg = "";
						
						var density1 = busArrivalInfo[i].density1;
						var density2 = busArrivalInfo[i].density2;
						
						//baepro_isRemainSeat(3)
						var isRemainSeat = false;
						//alert(routeTypeCd);
						if(routeId == "249000002"){ // 판타G버스 (자율주행버스) 노선타입 13번 but 빈자리수 표출 하드코딩
							isRemainSeat = true;
						}
						if(routeTypeCd==11 || routeTypeCd==12 || routeTypeCd==14 || routeTypeCd==16){
							// M6405,M6410,7790급,7800급,3200,3300,1008전,9401,9403,9404,9408,9701,9703,9707,9709,9714,9401공,9714공,9709공차,9711A
							var exRouteIds = "165000215,216000044,200000228,200000229,218000005,219000025,233000129,100100389,100100390,100100391,100100392,100100397,100100398,100100400,100100402,100100406,100100559,100100560,100100577,100100607";
							
							if(exRouteIds.indexOf(routeId)<0){
								isRemainSeat = true;
							}
						}
						var isDensity = false;
						
						var isDensity = false;
//						if(routeTypeCd==13 || routeTypeCd==15 || routeTypeCd==21 || routeTypeCd==22 || routeTypeCd==23 ){ // 13, 15, 21, 22, 23
//							var isDensityIds = " 200000069,200000049,200000146,200000024,200000070,200000239,200000172,200000092,200000013,200000231,200000048,200000197,200000208,200000031,200000240,200000241,200000051,200000147,200000067,200000016,200000020,200000199,200000101,233000011,233000012,233000007,200000028,200000060,200000010,200000008,200000037,200000053,200000043,200000040,200000148,200000185,200000055,200000202,200000074,200000183,200000076,200000012,200000152,200000093,200000201,200000182,200000106,200000099,200000085,200000077,200000237,200000042,200000236,200000157,200000196,200000039,200000166,200000211,200000088,200000064,200000238,200000234,200000078,200000206,200000056,200000058,200000129,200000134,200000066,200000061,200000032,200000034,200000065,200000133,200000261,200000014,200000018,200000022,200000122,200000045,200000097,200000095,200000090,200000239,200000268,200000103,200000029,200000054,200000186,200000025,200000023,200000107,200000144,233000087,200000266 ";
//					 		if(stationRegionName.indexOf("서울")<0 && stationRegionName.indexOf("인천")<0 ){
//								isDensity= true;
//					 		}
//							
//						}
						if(routeTypeCd==13 || routeTypeCd==15 || routeTypeCd==21 || routeTypeCd==22 || routeTypeCd==23 ){ // 13, 15, 21, 22, 23
							//var isDensityIds = " 200000069,200000049,200000146,200000024,200000070,200000239,200000172,200000092,200000013,200000231,200000048,200000197,200000208,200000031,200000240,200000241,200000051,200000147,200000067,200000016,200000020,200000199,200000101,233000011,233000012,233000007,200000028,200000060,200000010,200000008,200000037,200000053,200000043,200000040,200000148,200000185,200000055,200000202,200000074,200000183,200000076,200000012,200000152,200000093,200000201,200000182,200000106,200000099,200000085,200000077,200000237,200000042,200000236,200000157,200000196,200000039,200000166,200000211,200000088,200000064,200000238,200000234,200000078,200000206,200000056,200000058,200000129,200000134,200000066,200000061,200000032,200000034,200000065,200000133,200000261,200000014,200000018,200000022,200000122,200000045,200000097,200000095,200000090,,200000239,200000268,200000103,200000029,200000054,200000186,200000025,200000023,200000107,200000144,233000087,200000266 ";
					 		if(stationRegionName!=null && stationRegionName.indexOf("서울")<0 && stationRegionName.indexOf("인천")<0 ){
								isDensity= true;
					 		}
					 		// 혼잡도 제공하지 않고 빈자리제공하는 노선 (예, 판타G )
					 		var exDensityIds = "249000002";
					 		if(exDensityIds.indexOf(routeId)>=0){
					 			isDensity = false;
							}
						}
			            
			            //노선번호 색상
						/*
						Route_tp = 11, 21, 14  --> red(직행)
						Route_tp = 12  --> blue
						Route_tp = 30  --> yellow
						Route_tp = 41, 42, 43  --> violet(시외)
						Route_tp = 51, 52, 53  --> grey (공항)
						나머지 --> green
						 */
						if(routeTypeCd == 11 || routeTypeCd == 21 || routeTypeCd == 14 || routeTypeCd == 16){
							className = "num_red";
						}else if(routeTypeCd == 12){
							className = "num_blue";
						}else if(routeTypeCd == 30){
							className = "num_yellow";
						}else if(routeTypeCd == 41 || routeTypeCd == 42 || routeTypeCd == 43){
							className = "num_purple";
						}else if(routeTypeCd == 51 || routeTypeCd == 52 || routeTypeCd == 53){
							className = "num_gray";
						}else{
							className = "num_green";
						}
					
						//노선 아이콘
						/*
						SI_FLAG = 1 --> 서울
							Route_tp = 51,52, 53  --> 공항버스(seoul.gif, airport.gif)
							Route_tp = 41, 42, 43  --> 시외버스(seoul.gif, si.gif)
							Route_tp = 나머지 --> seoul.gif
						SI_FLAG = 3 --> 인천
							Route_tp = 51,52, 53  --> 공항버스(inchon.gif airport.gif)
							Route_tp = 41, 42, 43  --> 시외버스(inchon.gif, si.gif)
							Route_tp = 나머지 --> inchon.gif
						SI_FLAG = 나머지 --> 경기도
							Route_tp = 51,52, 53  --> 공항버스(airport.gif)
							Route_tp = 41, 42, 43  --> 시외버스(si.gif)
							Route_tp = 나머지 --> 이미지 없음
						 */
						if(siFlag == 1){ //서울
							if(routeTypeCd == 51 || routeTypeCd == 52 || routeTypeCd == 53){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/4.png" alt="공항" />';
							}else if(routeTypeCd == 41 || routeTypeCd == 42 || routeTypeCd == 43){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/3.png" alt="시외" />';
							}else if(routeTypeCd == 11 || routeTypeCd == 21 || routeTypeCd == 16){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/7_1.png" alt="직좌" />';
							}else if(routeTypeCd == 14){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/7.png" alt="광역" />';	
							}else if(routeTypeCd == 12 ){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/5_1.png" alt="좌석" />';
							}else if(routeTypeCd == 30){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/9_7.png" alt="마을" />';		
							}else{
//								iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />';
								iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/6_1.png" alt="일반" />';
							}
						}else if(siFlag == 3){ //인천
							if(routeTypeCd == 51 || routeTypeCd == 52 || routeTypeCd == 53){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/4.png" alt="공항" />';
							}else if(routeTypeCd == 41 || routeTypeCd == 42 || routeTypeCd == 43){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/3.png" alt="시외" />';
							}else if(routeTypeCd == 11 || routeTypeCd == 21 || routeTypeCd == 16){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/7_1.png" alt="직좌" />';
							}else if(routeTypeCd == 14){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/7.png" alt="광역" />';	
							}else if(routeTypeCd == 12 ){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/5_1.png" alt="좌석" />';
							}else if(routeTypeCd == 30){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/9_7.png" alt="마을" />';	
							}else{
//								iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />';
								iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/6_1.png" alt="일반" />';
							}
						}else{//경기도
							if(routeTypeCd == 51 || routeTypeCd == 52 || routeTypeCd == 53){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/4.png" alt="공항" />';
							}else if(routeTypeCd == 41 || routeTypeCd == 42 || routeTypeCd == 43){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/3.png" alt="시외" />';
							}else if(routeTypeCd == 30  ){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/9_7.png" alt="마을" />';
							}else if(routeTypeCd == 11 || routeTypeCd == 21 || routeTypeCd == 16){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/7_1.png" alt="직좌" />';
							}else if(routeTypeCd == 14){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/7.png" alt="광역" />';	
							}else if(routeTypeCd == 12 ){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/5_1.png" alt="좌석" />';
							}else{
//								iconImg = '';
								iconImg = '<img src="/gbis2014/images/ico/bus_type/6_1.png" alt="일반" />';
							}
						}
						
						//console.log("3."+stationRouteId+":"+routeId+":"+staOrder+":"+stationStaOrder+":"+updown_status+":"+stationUpdownNum);
						if(stationRouteId == routeId && staOrder==stationStaOrder){
							
							arrivalInfoStat = true; //도착예정목록에 노선정보 있음
							
							stationRealtime += '<li>';

							stationRealtime += '<div class="s_bus_num">'+iconImg+'<a title="새 창으로 보기" href="javascript:busInfoView(\''+routeName+'\',\''+routeId+'\',\''+routeTypeCd+'\')"><strong class="'+className+'">'+routeName+'</strong></a><br />';
							if(routeDestName.length > 13){
								stationRealtime += routeDestName.substring(0,10)+ '.. 방면';
							}else{
								stationRealtime += routeDestName+ ' 방면';
							}
							stationRealtime += '</div>';
							
							if(flag == 'STOP'){
								stationRealtime += '<div class="s_bus_time">1번째 : 운행종료<br />';
							}else if(flag == 'WAIT'){
								stationRealtime += '<div class="s_bus_time">1번째 : 회차점 대기중<br />';
							}else if(delayYn1 == "Y"){
								stationRealtime += '<div class="s_bus_time">1번째 : 회차점 대기중<br />';
							}else if(plateNo1 == "" && predictTime1 == ""){
								stationRealtime += '<div class="s_bus_time">1번째 : 도착예정정보 없음<br />';
							}else{
								if(predictTime1 == "0"){
									stationRealtime += '<div class="s_bus_time">1번째 : 약 <strong>1</strong>분 후 ('+locationNo1+'번째전)<br />';
									
									if(lowPlate1 == '6' && (nowtime2 > 640 && nowtime1 < 9)){
										stationRealtime += ' 예약버스';
									} else {
										if(isRemainSeat){
											if(remainSeatCnt1 != "-1" && remainSeatCnt1 != "" && remainSeatCnt1 != null && remainSeatCnt1 != undefined){
												stationRealtime += '빈자리 : <strong>'+remainSeatCnt1+'</strong>석';
											}else{
												stationRealtime += '빈자리 : 정보없음';
											}
										}
									}
									if(isDensity){
										if(density1 == 1){
											stationRealtime += '차내혼잡상태:<span class=\"color-density1\">여유</span>';
										}else if(density1 == 2){
											stationRealtime += '차내혼잡상태:<span class=\"color-density2\">보통</span>'; 
										}else if(density1 == 3){
											stationRealtime += '차내혼잡상태:<span class=\"color-density3\">혼잡</span>';
										}else if(density1 == 4){
											stationRealtime += '차내혼잡상태:<span class=\"color-density4\">매우혼잡</span>';
										}
									}
									
									if(lowPlate1 == '1'){
										if(isDensity) stationRealtime += ',';
										stationRealtime += '  저상버스<br/>';
									} else if(lowPlate1 == '7'){
										if(isDensity) stationRealtime += ',';
										stationRealtime += '  트롤리<br/>';
									}else if(lowPlate1 == '5'){
										if(isRemainSeat) stationRealtime += ','; 
										stationRealtime += '  전세버스<br/>';
									}else if(lowPlate1 == '2'){
										if(isRemainSeat) stationRealtime += ',';
										stationRealtime += ' 2층버스<br/>';
									}else {
//										if(plateType1 == '4'){
//											if(isRemainSeat) stationRealtime += ',';
//											stationRealtime += ' 2층버스<br/>';
//										} else {
											if(isRemainSeat){
												stationRealtime += '<br/>';
											} else if(isDensity && density1<5 && density1>0 ){
												stationRealtime += '<br/>';	
											}
//										}
									}
								}else{
									stationRealtime += '<div class="s_bus_time">1번째 : <strong>'+predictTime1+'</strong>분 후 ('+locationNo1+'번째전)<br />';
									if(lowPlate1 == '6' && (nowtime2 > 640 && nowtime1 < 9)){
										stationRealtime += ' 예약버스';
									} else {
										if(isRemainSeat){
											if(remainSeatCnt1 != "-1" && remainSeatCnt1 != "" && remainSeatCnt1 != null && remainSeatCnt1 != undefined){
												stationRealtime += '빈자리 : <strong>'+remainSeatCnt1+'</strong>석';
											}else{
												stationRealtime += '빈자리 : 정보없음';
											}
										}
									}
									
									if(isDensity){
										if(density1 == 1){
											stationRealtime += '차내혼잡상태:<span class=\"color-density1\">여유</span>';
										}else if(density1 == 2){
											stationRealtime += '차내혼잡상태:<span class=\"color-density2\">보통</span>'; 
										}else if(density1 == 3){
											stationRealtime += '차내혼잡상태:<span class=\"color-density3\">혼잡</span>';
										}else if(density1 == 4){
											stationRealtime += '차내혼잡상태:<span class=\"color-density4\">매우혼잡</span>';
										}
									}
									
									if(lowPlate1 == '1'){
										if(isDensity) stationRealtime += ',';
										stationRealtime += '  저상버스<br/>';
									} else if(lowPlate1 == '7'){
										if(isDensity) stationRealtime += ',';
										stationRealtime += '  트롤리<br/>';
									}else if(lowPlate1 == '5'){
										if(isRemainSeat) stationRealtime += ','; 
										stationRealtime += '  전세버스<br/>';
									}else if(lowPlate1 == '2'){
										if(isRemainSeat) stationRealtime += ',';
										stationRealtime += ' 2층버스<br/>';
									} else {
//										if(plateType1 == '4'){
//											if(isRemainSeat) stationRealtime += ',';
//											stationRealtime += ' 2층버스<br/>';
//										} else {
											if(isRemainSeat){
												stationRealtime += '<br/>';
											} else if(isDensity && density1<5 && density1>0 ){
												stationRealtime += '<br/>';	
											}
//										}
									}
								}
							}
							
							if(flag == 'STOP'){
								
							}else if(flag == 'WAIT'){
								
							}else if(delayYn1 == "Y"){
								
							}else if(plateNo2 == ""){
								stationRealtime += '2번째 : 도착예정정보 없음<br />';
//							}else if(crowded1 != crowded2){
//								stationRealtime += '2번째 : 회차점 대기중<br />';
							}else{
								if(predictTime2 == "0"){
									stationRealtime += '2번째 : 약 <strong>1</strong>분 후 ('+locationNo2+'번째전)<br />';
									
									if(lowPlate2 == '6' && (nowtime2 > 640 && nowtime1 < 9)){
										stationRealtime += ' 예약버스';
									} else {
										if(isRemainSeat){
											if(remainSeatCnt2 != "-1" && remainSeatCnt2 != "" && remainSeatCnt2 != null && remainSeatCnt2 != undefined){
												stationRealtime += '빈자리 : <strong>'+remainSeatCnt2+'</strong>석';
											}else{
												stationRealtime += '빈자리 : 정보없음';
											}
										}
									}
									if(isDensity){
										if(density2 == 1){
											stationRealtime += '차내혼잡상태:<span class=\"color-density1\">여유</span>';
										}else if(density2 == 2){
											stationRealtime += '차내혼잡상태:<span class=\"color-density2\">보통</span>'; 
										}else if(density2 == 3){
											stationRealtime += '차내혼잡상태:<span class=\"color-density3\">혼잡</span>';
										}else if(density2 == 4){
											stationRealtime += '차내혼잡상태:<span class=\"color-density4\">매우혼잡</span>';
										}
									}
									
									if(lowPlate2 == '1'){
										if(isDensity) stationRealtime += ',';									
										stationRealtime += '  저상버스<br/>';
									}else if(lowPlate2 == '7'){
										if(isDensity) stationRealtime += ',';									
										stationRealtime += '  트롤리<br/>';
									}else if(lowPlate2 == '5'){
										if(isRemainSeat) stationRealtime += ','; 
										stationRealtime += '  전세버스<br/>';
									}else if(lowPlate2 == '2'){
										if(isRemainSeat) stationRealtime += ',';
										stationRealtime += ' 2층버스<br/>';
									} else {
//										if(plateType2 == '4'){
//											if(isRemainSeat) stationRealtime += ',';
//											stationRealtime += ' 2층버스<br/>';
//										} else {
											if(isRemainSeat){
												stationRealtime += '<br/>';
											} else if(isDensity && density2<5 && density2>0 ){
												stationRealtime += '<br/>';	
											}
//										}
									}
								}else{
									stationRealtime += '2번째 : <strong>'+predictTime2+'</strong>분 후 ('+locationNo2+'번째전)<br />';
									
									if(lowPlate2 == '6' && (nowtime2 > 640 && nowtime1 < 9)){
										stationRealtime += ' 예약버스';
									} else {
										if(isRemainSeat){
											if(remainSeatCnt2 != "-1" && remainSeatCnt2 != "" && remainSeatCnt2 != null && remainSeatCnt2 != undefined){
												stationRealtime += '빈자리 : <strong>'+remainSeatCnt2+'</strong>석';
											}else{
												stationRealtime += '빈자리 : 정보없음';
											}
										}
									}
									if(isDensity){
										if(density2 == 1){
											stationRealtime += '차내혼잡상태:<span class=\"color-density1\">여유</span>';
										}else if(density2 == 2){
											stationRealtime += '차내혼잡상태:<span class=\"color-density2\">보통</span>'; 
										}else if(density2 == 3){
											stationRealtime += '차내혼잡상태:<span class=\"color-density3\">혼잡</span>';
										}else if(density2 == 4){
											stationRealtime += '차내혼잡상태:<span class=\"color-density4\">매우혼잡</span>';
										}
									}
									
									if(lowPlate2 == '1'){
										if(isDensity) stationRealtime += ',';
										stationRealtime += '  저상버스<br/>';
									} else if(lowPlate2 == '7'){
										if(isDensity) stationRealtime += ',';
										stationRealtime += '  트롤리<br/>';
									}else if(lowPlate2 == '5'){
										if(isRemainSeat) stationRealtime += ','; 
										stationRealtime += '  전세버스<br/>';
									}else if(lowPlate2 == '2'){
										if(isRemainSeat) stationRealtime += ',';
										stationRealtime += ' 2층버스<br/>';
									}else {
//										if(plateType2 == '4'){
//											if(isRemainSeat) stationRealtime += ',';
//											stationRealtime += ' 2층버스<br/>';
//										} else {
											if(isRemainSeat){
												stationRealtime += '<br/>';
											} else if(isDensity && density2<5 && density2>0 ){
												stationRealtime += '<br/>';	
											}
//										}
									}
								}
							}
							
							stationRealtime += '</div>';
							stationRealtime += '</li>';
							
							if(predictTime1 != "" && predictTime1 < 4) {
								stationRealtimeScroll += '<li style="width:43px">'+routeName+'</li>';
							}
						}
					});
					
					//도착예정목록에 해당노선 없을 시  busInfoView()추가
					if(!arrivalInfoStat){
						
						var routeTypeCd = busStationInfo[i].routeTypeCd;
						var siFlag = 0
						
						if(routeTypeCd == 11 || routeTypeCd == 21 || routeTypeCd == 14 || routeTypeCd == 16){
							className = "num_red";
						}else if(routeTypeCd == 12){
							className = "num_blue";
						}else if(routeTypeCd == 30){
							className = "num_yellow";
						}else if(routeTypeCd == 41 || routeTypeCd == 42 || routeTypeCd == 43){
							className = "num_purple";
						}else if(routeTypeCd == 51 || routeTypeCd == 52 || routeTypeCd == 53){
							className = "num_gray";
						}else{
							className = "num_green";
						}
					
						//노선 아이콘
						/*
						SI_FLAG = 1 --> 서울
							Route_tp = 51,52, 53  --> 공항버스(seoul.gif, airport.gif)
							Route_tp = 41, 42, 43  --> 시외버스(seoul.gif, si.gif)
							Route_tp = 나머지 --> seoul.gif
						SI_FLAG = 3 --> 인천
							Route_tp = 51,52, 53  --> 공항버스(inchon.gif airport.gif)
							Route_tp = 41, 42, 43  --> 시외버스(inchon.gif, si.gif)
							Route_tp = 나머지 --> inchon.gif
						SI_FLAG = 나머지 --> 경기도
							Route_tp = 51,52, 53  --> 공항버스(airport.gif)
							Route_tp = 41, 42, 43  --> 시외버스(si.gif)
							Route_tp = 나머지 --> 이미지 없음
						 */
						if(siFlag == 1){ //서울
							if(routeTypeCd == 51 || routeTypeCd == 52 || routeTypeCd == 53){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/4.png" alt="공항" />';
							}else if(routeTypeCd == 41 || routeTypeCd == 42 || routeTypeCd == 43){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/3.png" alt="시외" />';
							}else if(routeTypeCd == 11 || routeTypeCd == 21 || routeTypeCd == 16){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/7_1.png" alt="직좌" />';
							}else if(routeTypeCd == 14){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/7.png" alt="광역" />';	
							}else if(routeTypeCd == 12 ){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/5_1.png" alt="좌석" />';
							}else if(routeTypeCd == 30){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/9_7.png" alt="마을" />';		
							}else{
//								iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />';
								iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/6_1.png" alt="일반" />';
							}
						}else if(siFlag == 3){ //인천
							if(routeTypeCd == 51 || routeTypeCd == 52 || routeTypeCd == 53){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/4.png" alt="공항" />';
							}else if(routeTypeCd == 41 || routeTypeCd == 42 || routeTypeCd == 43){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/3.png" alt="시외" />';
							}else if(routeTypeCd == 11 || routeTypeCd == 21 || routeTypeCd == 16){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/7_1.png" alt="직좌" />';
							}else if(routeTypeCd == 14){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/7.png" alt="광역" />';	
							}else if(routeTypeCd == 12 ){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/5_1.png" alt="좌석" />';
							}else if(routeTypeCd == 30){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/9_7.png" alt="마을" />';	
							}else{
//								iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />';
								iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/6_1.png" alt="일반" />';
							}
						}else{//경기도
							if(routeTypeCd == 51 || routeTypeCd == 52 || routeTypeCd == 53){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/4.png" alt="공항" />';
							}else if(routeTypeCd == 41 || routeTypeCd == 42 || routeTypeCd == 43){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/3.png" alt="시외" />';
							}else if(routeTypeCd == 30  ){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/9_7.png" alt="마을" />';
							}else if(routeTypeCd == 11 || routeTypeCd == 21 || routeTypeCd == 16){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/7_1.png" alt="직좌" />';
							}else if(routeTypeCd == 14){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/7.png" alt="광역" />';	
							}else if(routeTypeCd == 12 ){
								iconImg = '<img src="/gbis2014/images/ico/bus_type/5_1.png" alt="좌석" />';
							}else{
//								iconImg = '';
								iconImg = '<img src="/gbis2014/images/ico/bus_type/6_1.png" alt="일반" />';
							}
						}
						
						stationRealtime += '<li>';
						stationRealtime += '<div class="s_bus_num">'+iconImg+'<a title="새 창으로 보기" href="javascript:busInfoView(\''+stationRouteName+'\', \''+stationRouteId+'\')"><strong class="'+className+'">'+stationRouteName+'</strong></a><br />';
						if(stationRouteDestName.length > 13){
							stationRealtime += stationRouteDestName.substring(0,10)+ '.. 방면';
						}else{
							stationRealtime += stationRouteDestName+ ' 방면';
						}
						stationRealtime += '</div>';
						
						stationRealtime += '<div class="s_bus_time">1번째 : 도착예정정보 없음<br />';
						stationRealtime += '2번째 : 도착예정정보 없음<br />';
						stationRealtime += '</div>';
						stationRealtime += '</li>';
					}
				}
			});
			
			var drtYN = busStationInfo[0].drtYN;
			if(drtYN == 'Y'){
				stationRealtime += '<li>';
				stationRealtime += '<div class="s_bus_num"><strong>'+'파주DRT 정류소 '+'</strong><a title="" href="https://www.shucle.com" target="_blank">'+' 셔클 홈페이지'+'</strong></a><br />';
				stationRealtime += '</li>';
			}
			
			
		}else{
			
			//정류소에 해당노선 없을 시 
			if(!route_name){
				stationRealtime += '<li>';
				stationRealtime += '도착 예정 정보가 없습니다. ';
				stationRealtime += '</li>';
			}else{
				stationRealtime += '<li>';
				stationRealtime += '<div class="s_bus_num"><strong class="">'+route_name+'</strong><br /></div>';
				stationRealtime += '<div class="s_bus_time">1번째 : 도착예정정보 없음<br />';
				stationRealtime += '2번째 : 도착예정정보 없음<br />';
				stationRealtime += '</div>';
				stationRealtime += '</li>';
			}
		}
		
		$('.station_bus_scroll_'+stationId).html(stationRealtimeScroll);
		$('.station_bus_list_'+stationId).html(stationRealtime);
		
		//잠시후 도착버스 롤링
		// if(jQuery('.station_bus_scroll_'+stationId+' li').length > 4){ //정류장 버스개수가 5 이상일때
		// 	jQuery(".scroller_"+stationId).scroller({
		//         scroller_title_show: 'disable',
		//         scroller_time_interval: '2000',
		//         scroller_window_background_color: "white",
		//         scroller_window_padding: '0',
		//         scroller_border_size: '0',
		//         scroller_border_color: '#CCC',
		//         scroller_images_width: '43',
		//         scroller_images_height: '15',
		//         scroller_title_size: '12',
		//         scroller_title_color: '#555',
		//         scroller_show_count: '5',
		//         directory: '/gbis2014/images/location'
		// 	});
		// }else{
		// 	$('.station_bus_scroll_'+stationId).width(($('.station_bus_scroll_'+stationId+' li').length) * 43);
		// }
	    
		$('.station_bus_scroll_'+stationId).width(($('.station_bus_scroll_'+stationId+' li').length) * 43);
	}else{
		var stationRealtime = '';
		
		stationRealtime += '<li>';
		stationRealtime += '도착 예정 정보가 없습니다. ';
		stationRealtime += '</li>';
		
		$('.station_bus_list ul').html(stationRealtime);
	}
	
	updown_status ="";
	
	var popTop = Number($('#customLabel.tmPopup').css('top').replace('px','')) + 50;
	$('#customLabel.tmPopup').css('top', popTop+'px !important');
	
//!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
/*
	$(document).on("keydown", "#list_id_0", function(){ // on 이벤트로 변경
		$('#pop_id_0').css('display','block' ).attr('tabindex','0').focus();
	});

*/
}

//////////////////// WA 웹접근성 ////////////////////////

function focusSearchResult(){
    //var hitArea = '#beforeStartBtn';
    //var targetArea = '#roadSearchResult';
    console.log('the key is down inside the function ');
    $('#roadSearchResult').css('display','block' ).attr('tabindex','0').focus();
}


function focusRoutePopup(routeId){
	var targetPopup = '#list_route_'+routeId;
	var popId = '#route_detail_'+routeId;
	$(document).on("keydown", targetPopup , function(){ // on 이벤트로 변경
		$(popId).css('display','block' ).attr('tabindex','0').focus();
	});
}

function focusRouteStationPopup_up(i){
	var targetPopup = '#uplist_route_station_'+i;
	var popId = '#pop_id_'+i;
	$(document).on("keydown", targetPopup , function(){ // on 이벤트로 변경
		$(popId).css('display','block' ).attr('tabindex','0').focus();
	});
}

function focusRouteStationPopup_down(i){
	var targetPopup = '#downlist_route_station_'+i;
	var popId = '#pop_id_down_'+i;
	$(document).on("keydown", targetPopup , function(){ // on 이벤트로 변경
		$(popId).css('display','block' ).attr('tabindex','0').focus();
	});
}


function focusStationPopup(i){
	var targetPopup = '#list_station_'+i;
	var popId = '#pop_id_'+i;
	$(document).on("keydown", targetPopup , function(){ // on 이벤트로 변경
		$(popId).css('display','block' ).attr('tabindex','0').focus();
	});
}

function focusPlacePopup(i){
	var targetPopup = '#list_place_'+i;
	var popId = '#pop_id_'+i;
	$(document).on("keydown", targetPopup , function(){ // on 이벤트로 변경
		$(popId).css('display','block' ).attr('tabindex','0').focus();
	});
}
function focusSubwayPopup(i){
	var targetPopup = '#list_subway_'+i;
	var popId = '#pop_id_'+i;
	$(document).on("keydown", targetPopup , function(){ // on 이벤트로 변경
		$(popId).css('display','block' ).attr('tabindex','0').focus();
	});
}
function focusBusStationPopup(i){
	var targetPopup = '#list_busstation_'+i;
	var popId = '#pop_id_'+i;
	$(document).on("keydown", targetPopup , function(){ // on 이벤트로 변경
		$(popId).css('display','block' ).attr('tabindex','0').focus();
	});
}


function focusBacktoRouteList(routeId){
	var targetList = "#list_route_"+routeId;
	$(targetList).css('display','block' ).attr('tabindex','0').focus();
}

function focusBacktoRouteStationList_up(i){ //focusBackToRouteStationList_up
	var targetList = "#uplist_route_station_"+i; //"uplist_route_station_3"
	$(targetList).css('display','block' ).attr('tabindex','0').focus();
}
function focusBacktoRouteStationList_down(i){ //focusBackToRouteStationList_up
	var targetList = "#downlist_route_station_"+i; //"uplist_route_station_3"
	$(targetList).css('display','block' ).attr('tabindex','0').focus();
}

function focusBackToStationList(i){
	var targetList = "#list_station_"+i;
	$(targetList).css('display','block' ).attr('tabindex','0').focus();
}
function focusBackToPlaceList(i){
	var targetList = "#list_place_"+i;
	$(targetList).css('display','block' ).attr('tabindex','0').focus();
}
function focusBackToSubwayList(i){
	var targetList = "#list_subway_"+i;
	$(targetList).css('display','block' ).attr('tabindex','0').focus();
}
//function focusBackToBusStationList(i){
//	var targetList = "#list_busstation_"+i;
//	$(targetList).css('display','block' ).attr('tabindex','0').focus();
//}





//좌측 리스트 클릭 시
function getPoiMap(i,poiLon, poiLat) {
	map.setCenter(new Tmap.LonLat(poiLon, poiLat), 17);
	
	if(chkNum == 1){
		
		//팝업 생성
		map.addPopup(poiObj[i].popup);
		var pContentDivW = jQuery(poiObj[i].popup.contentDiv).find('div').width();
		poiObj[i].popup.anchor.offset.x = -10 - (pContentDivW / 2);
		
		poiObj[i].popup.panMapIfOutOfView = true;
		poiObj[i].popup.show();
		crPopup = poiObj[i].popup;
		crLon = crPopup.lonlat.lon;
		crLat = crPopup.lonlat.lat;
		routeName = jQuery(crPopup.contentDiv).find('.crNm').text();
		chkNum = 2;
	}else{
		map.removePopup(crPopup);
		
		//팝업 생성
		map.addPopup(poiObj[i].popup);
		var pContentDivW = jQuery(poiObj[i].popup.contentDiv).find('div').width();
		poiObj[i].popup.anchor.offset.x = -10 - (pContentDivW / 2);
		
		poiObj[i].popup.panMapIfOutOfView = true;
		poiObj[i].popup.show();
		crPopup = poiObj[i].popup;
		crLon = crPopup.lonlat.lon;
		crLat = crPopup.lonlat.lat;
		routeName = jQuery(crPopup.contentDiv).find('.crNm').text();
	}
	
	//경로탐색에서 리스트 클릭시
	if((selectSecFlag == 2) && startEndStatus){ //출발 마커
		listStartFlag();
	}else if((selectSecFlag == 2) && !startEndStatus){ //도착 마커
		listEndFlag();
	}
}
function getStationMap(i,stationLon, stationLat) {
	map.setCenter(new Tmap.LonLat(stationLon, stationLat), 17);
	
	if(chkNum == 1){
		
		//팝업 생성
		map.addPopup(stationObj[i].popup);
		var pContentDivW = jQuery(stationObj[i].popup.contentDiv).find('div').width();
		stationObj[i].popup.anchor.offset.x = -10 - (pContentDivW / 2);
		
		stationObj[i].popup.panMapIfOutOfView = true;
		stationObj[i].popup.show();
		crPopup = stationObj[i].popup;
		crLon = crPopup.lonlat.lon;
		crLat = crPopup.lonlat.lat;
		routeName = jQuery(crPopup.contentDiv).find('.crNm').text();
		chkNum = 2;
	}else{
		map.removePopup(crPopup);
		
		//팝업 생성
		map.addPopup(stationObj[i].popup);
		var pContentDivW = jQuery(stationObj[i].popup.contentDiv).find('div').width();
		stationObj[i].popup.anchor.offset.x = -10 - (pContentDivW / 2);
		
		stationObj[i].popup.panMapIfOutOfView = true;
		stationObj[i].popup.show();
		crPopup = stationObj[i].popup;
		crLon = crPopup.lonlat.lon;
		crLat = crPopup.lonlat.lat;
		routeName = jQuery(crPopup.contentDiv).find('.crNm').text();
	}
	
	//경로탐색에서 리스트 클릭시
	if((selectSecFlag == 2) && startEndStatus){ //출발 마커
		listStartFlag();
	}else if((selectSecFlag == 2) && !startEndStatus){ //도착 마커
		listEndFlag();
	}
	
	//도착정보 호출
	station_id = $(crPopup.contentDiv).find('.stationId').text();
	
	var url = "/gbis2014/schBusAPI.action";
	var data = 'cmd=searchBusStationJson';
	data += '&stationId='+station_id;
	
	$.ajax({
		type: "post",
		contentType: "application/x-www-form-urlencoded;charset=UTF-8",
		dataType: "json",
		url: url,
		data: data,
		success: getStationRealtimeSuccess,
		error: ajaxError
	});
	
	//주변정류소 보기 ON
	localBusStatus = false;
	busOnOff();
	searchAroundBusJson();
}

function getSubwayMap(i,subwayLon, subwayLat) {
	map.setCenter(new Tmap.LonLat(subwayLon, subwayLat), 17);
	
	if(chkNum == 1){
		
		//팝업 생성
		map.addPopup(subwayObj[i].popup);
		var pContentDivW = jQuery(subwayObj[i].popup.contentDiv).find('div').width();
		subwayObj[i].popup.anchor.offset.x = -10 - (pContentDivW / 2);
		
		subwayObj[i].popup.panMapIfOutOfView = true;
		subwayObj[i].popup.show();
		crPopup = subwayObj[i].popup;
		crLon = crPopup.lonlat.lon;
		crLat = crPopup.lonlat.lat;
		routeName = jQuery(crPopup.contentDiv).find('.crNm').text();
		chkNum = 2;
	}else{
		map.removePopup(crPopup);
		
		//팝업 생성
		map.addPopup(subwayObj[i].popup);
		var pContentDivW = jQuery(subwayObj[i].popup.contentDiv).find('div').width();
		subwayObj[i].popup.anchor.offset.x = -10 - (pContentDivW / 2);
		
		subwayObj[i].popup.panMapIfOutOfView = true;
		subwayObj[i].popup.show();
		crPopup = subwayObj[i].popup;
		crLon = crPopup.lonlat.lon;
		crLat = crPopup.lonlat.lat;
		routeName = jQuery(crPopup.contentDiv).find('.crNm').text();
	}
	
	//경로탐색에서 리스트 클릭시
	if((selectSecFlag == 2) && startEndStatus){ //출발 마커
		listStartFlag();
	}else if((selectSecFlag == 2) && !startEndStatus){ //도착 마커
		listEndFlag();
	}
}

function getRouteMap(i,routeLon, routeLat, status) {

	
	map.setCenter(new Tmap.LonLat(routeLon, routeLat), 17);
	updown_status = status;
	//상행
	if(status == 1){
		
		if(chkNum == 1){
			
			//팝업 생성
			map.addPopup(upRouteStationObj[i].popup);
			var pContentDivW = jQuery(upRouteStationObj[i].popup.contentDiv).find('div').width();
			upRouteStationObj[i].popup.anchor.offset.x = -10 - (pContentDivW / 2);
			
			upRouteStationObj[i].popup.panMapIfOutOfView = true;
			upRouteStationObj[i].popup.show();
			crPopup = upRouteStationObj[i].popup;
			crLon = crPopup.lonlat.lon;
			crLat = crPopup.lonlat.lat;
			routeName = jQuery(crPopup.contentDiv).find('.crNm').text();
			chkNum = 2;
		}else{
			map.removePopup(crPopup);
			
			//팝업 생성
			map.addPopup(upRouteStationObj[i].popup);
			var pContentDivW = jQuery(upRouteStationObj[i].popup.contentDiv).find('div').width();
			upRouteStationObj[i].popup.anchor.offset.x = -10 - (pContentDivW / 2);
			
			upRouteStationObj[i].popup.panMapIfOutOfView = true;
			upRouteStationObj[i].popup.show();
			crPopup = upRouteStationObj[i].popup;
			crLon = crPopup.lonlat.lon;
			crLat = crPopup.lonlat.lat;
			routeName = jQuery(crPopup.contentDiv).find('.crNm').text();
		}
		
	//하행
	}else if(status == 2){
		
		if(chkNum == 1){
			
			//팝업 생성
			map.addPopup(downRouteStationObj[i].popup);
			var pContentDivW = jQuery(downRouteStationObj[i].popup.contentDiv).find('div').width();
			downRouteStationObj[i].popup.anchor.offset.x = -10 - (pContentDivW / 2);
			
			downRouteStationObj[i].popup.panMapIfOutOfView = true;
			downRouteStationObj[i].popup.show();
			crPopup = downRouteStationObj[i].popup;
			crLon = crPopup.lonlat.lon;
			crLat = crPopup.lonlat.lat;
			routeName = jQuery(crPopup.contentDiv).find('.crNm').text();
			chkNum = 2;
		}else{
			map.removePopup(crPopup);
			
			//팝업 생성
			map.addPopup(downRouteStationObj[i].popup);
			var pContentDivW = jQuery(downRouteStationObj[i].popup.contentDiv).find('div').width();
			downRouteStationObj[i].popup.anchor.offset.x = -10 - (pContentDivW / 2);
			
			downRouteStationObj[i].popup.panMapIfOutOfView = true;
			downRouteStationObj[i].popup.show();
			crPopup = downRouteStationObj[i].popup;
			crLon = crPopup.lonlat.lon;
			crLat = crPopup.lonlat.lat;
			routeName = jQuery(crPopup.contentDiv).find('.crNm').text();
		}
	}
	
	
	
	//도착정보 호출
	//route_station_id = $(crPopup.contentDiv).find('.routeStationId').text();
	//route_id = $(crPopup.contentDiv).find('.routeId').text();
	station_id = $(crPopup.contentDiv).find('.stationId').text();
	var url = "/gbis2014/schBusAPI.action";
	var data = 'cmd=searchBusStationJson';
	data += '&stationId='+station_id;
	//data += '&routeId='+route_id;
	
	$.ajax({
		type: "post",
		contentType: "application/x-www-form-urlencoded;charset=UTF-8",
		dataType: "json",
		url: url,
		data: data,
		success: getStationRealtimeSuccess,
		error: ajaxError
	});
	
//	$('#focus_02').attr('tabindex','0').focus();
}

var multiRouteCnt;
var multiRouteCntTotal;
function getMultiRoute(){

	var chkBox = $(".list_bus li input:checkbox");
	var arrRouteId = [];
	var arrIndex = 0;
	multiRouteCnt = 0;
	
	if(chkBox.is(":checked")){ //체크된 노선이 있으면
		
		if($(".list_bus li input:checkbox:checked").length > 5){ // 6개 이상이면
			alert("다중노선보기는 5개까지만 조회 가능합니다");
		}else{
			
			for (var i = 0; i < 5; i++){
				//기존 다중노선 마커 삭제
				upRouteMarkerLayerArr[i].clearMarkers();
				downRouteMarkerLayerArr[i].clearMarkers();
				//기존 다중노선 경로 삭제
				if(up_line_layerArr[i] != null) up_line_layerArr[i].destroyFeatures();
				if(down_line_layerArr[i] != null) down_line_layerArr[i].destroyFeatures();
			}
			
			chkBox.each(function(i){
				if(this.checked){
					arrRouteId[arrIndex] = this.name;
					arrIndex++;
				}
			});
			multiRouteCntTotal = arrIndex;
			
			$.each(arrRouteId,function(i){
				
				var url = "/gbis2014/schBusAPI.action";
				var data = 'cmd=searchRouteJson';
				data += '&routeId='+arrRouteId[i];
				
				var myMessenger =new ResultToSuccess(i);
				$.ajax({
					type: "post",
					contentType: "application/x-www-form-urlencoded;charset=UTF-8",
					dataType: "json",
					async:false,
					url: url,
					data: data,
					success: function(data){
						myMessenger.sendToSuccess(data);
					},
					error: ajaxError,
					beforeSend: ajaxBeforeSend,
				    complete: ajaxComplete
				});
			});
		}
		
	}else{ //체크된 노선이 없으면
		alert("노선을 선택해 주세요");
	}
}


function getMultiRoute(){

	var chkBox = $(".list_bus li input:checkbox");
	var arrRouteId = [];
	var arrIndex = 0;
	multiRouteCnt = 0;
	
	if(chkBox.is(":checked")){ //체크된 노선이 있으면
		
		if($(".list_bus li input:checkbox:checked").length > 5){ // 6개 이상이면
			alert("다중노선보기는 5개까지만 조회 가능합니다");
		}else{
			
			for (var i = 0; i < 5; i++){
				//기존 다중노선 마커 삭제
				upRouteMarkerLayerArr[i].clearMarkers();
				downRouteMarkerLayerArr[i].clearMarkers();
				//기존 다중노선 경로 삭제
				if(up_line_layerArr[i] != null) up_line_layerArr[i].destroyFeatures();
				if(down_line_layerArr[i] != null) down_line_layerArr[i].destroyFeatures();
			}
			
			chkBox.each(function(i){
				if(this.checked){
					arrRouteId[arrIndex] = this.name;
					arrIndex++;
				}
			});
			multiRouteCntTotal = arrIndex;
			
			$.each(arrRouteId,function(i){
				
				var url = "/gbis2014/schBusAPI.action";
				var data = 'cmd=searchRouteJson';
				data += '&routeId='+arrRouteId[i];
				
				var myMessenger =new ResultToSuccess(i);
				$.ajax({
					type: "post",
					contentType: "application/x-www-form-urlencoded;charset=UTF-8",
					dataType: "json",
					async:false,
					url: url,
					data: data,
					success: function(data){
						myMessenger.sendToSuccess(data);
					},
					error: ajaxError,
					beforeSend: ajaxBeforeSend,
				    complete: ajaxComplete
				});
			});
		}
		
	}else{ //체크된 노선이 없으면
		alert("노선을 선택해 주세요");
	}
}

function getMultiRouteDraw(){

//	var chkBox = $(".list_bus li input:checkbox");
	resetSearch();
	var arrRouteId = $("#compareTray li");
	
	
//	console.log("A yo");
//	console.log(arrRouteId);
//	console.log(arrRouteId[0].id);
//	var arrRouteId = [];
//	var arrIndex = 0;
//	multiRouteCnt = 0;
	
	if(arrRouteId){ //체크된 노선이 있으면
		
		if(arrRouteId.length > 10){ // 6개 이상이면
		//	alert("노선도 비교는 10개까지만 조회 가능합니다");
		}else{
			
			for (var i = 0; i<arrRouteId.length; i++){
				//기존 다중노선 마커 삭제
				upRouteMarkerLayerArr[i].clearMarkers();
				downRouteMarkerLayerArr[i].clearMarkers();
				//기존 다중노선 경로 삭제
				if(up_line_layerArr[i] != null) up_line_layerArr[i].destroyFeatures();
				if(down_line_layerArr[i] != null) down_line_layerArr[i].destroyFeatures();
			}
			
//			chkBox.each(function(i){
//				if(this.checked){
//					arrRouteId[arrIndex] = this.name;
//					arrIndex++;
//				}
//			});
//			multiRouteCntTotal = arrIndex;
			
			multiLineCnt = 0;
			var myMessenger =new ResultToSuccess(i);
			
			$.each(arrRouteId,function(i){
				
				var url = "/gbis2014/schBusAPI.action";
				var data = 'cmd=searchRouteJson';
				data += '&routeId='+arrRouteId[i].id;
				
				$.ajax({
					type: "post",
					contentType: "application/x-www-form-urlencoded;charset=UTF-8",
					dataType: "json",
					async:false,
					url: url,
					data: data,
					success: function(data){
						myMessenger.sendToSuccess(data);
					},
					error: ajaxError,
					beforeSend: ajaxBeforeSend,
				    complete: ajaxComplete
				});
			});
		}
		
	}else{ //체크된 노선이 없으면
		alert("노선을 선택해 주세요");
	}
}


function ResultToSuccess(cnt){
	this.cnt = cnt;
	this.sendToSuccess = function(data){
		getMultiRouteSuccess(data, this.cnt);
	};
}

var multiRouteLineIdx;
var multiRouteNm;
var multiRegion;
function getMultiRouteSuccess(data, multiRouteIdx){
	
	multiRouteLineIdx = multiRouteIdx;
	
	if(data.success){
		
		var resultRealTime = data.result.realTime;
		//var resultGgUpline = data.result.gg.upLine;
		//var resultGgDownline = data.result.gg.downLine;
		var resultGgRoute = data.result.gg.route;
		var resultGgMiddlePnt = data.result.gg.middlePnt;
		var resultGgUp = data.result.gg.up;
		var resultGgDown = data.result.gg.down;
		
		var busTotalCount = resultRealTime.busTotalCount;
		var busCount = resultRealTime.count;
		//var ggUplineCnt = resultGgUpline.count;
		//var ggDownlineCnt = resultGgDownline.count;
		var ggUpCnt = resultGgUp.count;
		var ggDownCnt = resultGgDown.count;
		
		var bus_info = "";
		var list_realtime = "";
		var list_route_upline = "";
		var list_route_downline = "";
		
		//버스노선상세 검색결과
		var maxHead = resultGgRoute.maxHead;
		var downLastTime = resultGgRoute.downLastTime;
		var upFirstTime = resultGgRoute.upFirstTime;
		var stStaNm = (resultGgRoute.stStaNm.length > 5) ? resultGgRoute.stStaNm.substring(0,5)+'...' : resultGgRoute.stStaNm;
		var companyTel = resultGgRoute.companyTel;
		var routeId = resultGgRoute.routeId;
		var companyNm = resultGgRoute.companyNm;
		var routeNm = resultGgRoute.routeNm;
		multiRouteNm = routeNm;
		var region = resultGgRoute.region;
		multiRegion = region;
		var garageTel = resultGgRoute.garageTel;
		var downFirstTime = resultGgRoute.downFirstTime;
		var garageNm = resultGgRoute.garageNm;
		var turnSeq = resultGgRoute.turnSeq;
		var npeekAlloc = resultGgRoute.npeekAlloc;
		var edStaNm = (resultGgRoute.edStaNm.length > 5) ? resultGgRoute.edStaNm.substring(0,5)+'...' : resultGgRoute.edStaNm;
		var minHead = resultGgRoute.minHead;
		var upLastTime = resultGgRoute.upLastTime;
		var peekAlloc = resultGgRoute.peekAlloc;
		
		//상행 마커
		if(ggUpCnt > 0){
			$.each(resultGgUp.list,function(i){
				if(i != 0) return; //기점만 표출
					var upStationImg = "";
					var upStationNo = resultGgUp.list[i].stationNo;
					var upCenterYn = resultGgUp.list[i].centerYn;
					var upStationImg = (upCenterYn == 'Y') ? "station3" : "station1";
					var upStationNm = resultGgUp.list[i].stationNm;
					var upStationSeq = resultGgUp.list[i].stationSeq;
					var upGnm = resultGgUp.list[i].gnm;
					var upStationId = resultGgUp.list[i].stationId;
					var upMobileNoSi = resultGgUp.list[i].mobileNoSi;
					var upLon = resultGgUp.list[i].lon;
					var upLat = resultGgUp.list[i].lat;
			    	
					//지도 상행 정류소 마커 생성
					var up_size = new Tmap.Size(20, 20);
					var up_offset = new Tmap.Pixel(-(up_size.w / 2), -up_size.h);
					var up_iconHtml = new Tmap.IconHtml('<div class="icon_wa line routeStation'+i+'"><img src="/gbis2014/images/ico/common/'+upStationImg+'.png" /></div>',up_size,up_offset);
					var up_routeMarker = new Tmap.Marker(new Tmap.LonLat(upLon, upLat), up_iconHtml);
					
					
					// 마커 레이어 생성
					map.addLayer(upRouteMarkerLayerArr[multiRouteIdx]);
		
					// 마커 생성
					upRouteMarkerLayerArr[multiRouteIdx].addMarker(up_routeMarker);
					upRouteMarkerLayerArr[multiRouteIdx].div.style.zIndex = 500;
					
					//팝업 생성
					/****************************************************************************************************
					 * Tmap.Popup.Anchored offset 처리 방식
					 * tl : popup.anchor.offset.x - popup.size.w / popup.anchor.offset.y - popup.size.h
					 * tr : popup.anchor.offset.x + popup.anchor.size.w /  popup.anchor.offset.y - popup.size.h
					 * bl : popup.anchor.offset.x - popup.size.w/ popup.anchor.offset.y + popup.anchor.size.h
					 * br : popup.anchor.offset.x + popup.anchor.size.w / popup.anchor.offset.y + popup.anchor.size.h
					 ****************************************************************************************************/
			
					upRouteStationObjArr[multiRouteIdx][i] = up_routeMarker;
					var sizeW = 380;
					var alonlat = new Tmap.LonLat(upLon, upLat);
					var aSize = new Tmap.Size(10, 20);
					var aOffset = new Tmap.Pixel(-(up_size.w / 2), -up_size.h);
					var anchorObj = {
						size : aSize,
						offset : aOffset
					};
					/*
					var cSize = new Tmap.Size(sizeW, 215);
					var label = '<div class="tooltip">';
					label += '<a class="close" href="javascript:tooltipClose()">툴팁닫기</a>';
					label += '<h1>'+upStationNm+' <span class="line">|</span> <span class="station_code">'+upStationNo+'</span><span class="crNm" style="display:none">'+upStationNm+'</span>';
					label += '<span class="routeStationId" style="display:none">'+upStationId+'</span><span class="routeId" style="display:none">'+routeId+'</span></h1>';
					label += '<div class="tooltip_content">';
					label += '<div class="after_bus">';
					label += '<h2>해당 노선 도착예정정보</h2>';
					label += '</div>';
					label += '<div class="station_bus_list one">';
					label += '<ul class="route_station_bus_list_'+upStationId+' routeId_'+routeId+'" style="height:90px">';
					label += '</ul>';
					label += '</div>';
					label += '</div>';
					label += '<div class="tooltip_btn">';
					label += '<button type="button" onclick="btnStartFlag()" class="w_btn start"><span>출발</span></button>\n';
					label += '<button type="button" onclick="btnEndFlag()" class="w_btn end"><span>도착</span></button>';
					label += '</div>';
					label += '<div class="tooltip_arrow"></div>';
					label += '</div>';
					*/
					var cSize = new Tmap.Size(sizeW, 400);
					//상행마커
					var label = '<div class="tooltip"><!--상행마커-->';
					
					label += '<h1><a href="javascript:busStationView(\''+upStationId+'\',\''+upStationNm+'\');" title="같은 정류소명 통합검색 결과 새 창으로 보기">'+upStationNm+' <span class="line">|</span> <span class="station_code" alt="upStationNo2">'+upStationNo+'</span><span class="crNm" style="display:none">'+upStationNm+'</span><span class="stationId" style="display:none">'+upStationId+'</span></a></h1>';
					label += '<div class="tooltip_content">';
					label += '<div class="after_bus">';
					label += '<h2>잠시후 도착버스 <span class="line">|</span></h2>';
					label += '<div id="scroller" class="scroller scroller_'+upStationId+'" style="position:relative;margin-left:100px;width:218px;height:31px">';
					label += '<div class="scroller_mask" style="width:210px;height:31px;">';
					label += '<ul class="station_bus_scroll_'+upStationId+'">';
					label += '</ul>';
					label += '</div>';
					label += '<ul class="scroller_nav" style="width: 238px;">';
					label += '<li></li>';
					// label += '<a tabindex="0" title="잠시후 도착버스 더보기"  style="width: 15px; height: 15px; right: 0px; top: 8px; background-image: url(/gbis2014/images/location/bg_tooltip.png); background-position: -20px 0px; background-repeat: no-repeat;"></a>';
					label += '</ul>';
					label += '</div>';
					label += '</div>';
					label += '<div class="station_bus_list">';
					label += '<ul class="station_bus_list_'+upStationId+'">';
					label += '</ul>';
					label += '</div>';
					label += '</div>';
					label += '<div class="tooltip_btn">';
					label += '<button type="button" onclick="btnStartFlag()" class="w_btn start"><span>출발</span></button>\n';
					label += '<button type="button" onclick="btnEndFlag()" class="w_btn end"><span>도착</span></button>';
					label += '</div>';
					label += '<a class="close"  title="정류소 도착정보 창 닫기"  href="javascript:tooltipClose()"><i class="fa fa-times" aria-hidden="true"></i></a>';
					label += '<div class="tooltip_arrow"></div>';
					label += '</div>';
					
					up_routeMarker.popup = new Tmap.Popup.Anchored("customLabel", alonlat, cSize, label, anchorObj, false);
					up_routeMarker.popup.relativePosition = 'tr';
		
					up_routeMarker.popup.updateRelativePosition();
					up_routeMarker.popup.calculateRelativePosition = function(px) {
						return up_routeMarker.popup.relativePosition;
					};
					up_routeMarker.popup.panMapIfOutOfView = false; //팝업 지도 중앙에 표출
					up_routeMarker.popup.keepInMap = false;
					
					//팝업 스타일링 부분
					up_routeMarker.popup.contentDiv.style.overflow = "hidden";
					up_routeMarker.popup.contentDiv.style.padding = "0px 0px 30px 0px";
					up_routeMarker.popup.setBackgroundColor("transparent");
					/*
					map.addPopup(up_routeMarker.popup);
					var pContentDivW = jQuery(up_routeMarker.popup.contentDiv).find('div').width();
					up_routeMarker.popup.anchor.offset.x = up_routeMarker.popup.anchor.offset.x - (pContentDivW / 2);
					up_routeMarker.popup.hide();
					*/
					$(up_routeMarker.icon.imageDiv).find('div').css('cursor', 'pointer'); //마커 오버 시 스타일
					
					up_routeMarker.events.register('click', up_routeMarker, onMarkerClick);
					up_routeMarker.events.register('mouseover', up_routeMarker[i], onMouseMarker);
					up_routeMarker.events.register('mouseout', up_routeMarker[i], outMouseMarker);
					up_routeMarker.popup.events.register('mouseover',up_routeMarker, onMousePopup);
					up_routeMarker.popup.events.register('mouseout',up_routeMarker, outMousePopup);
					
					
					
	    	});
	
			
		}
		
		//하행 마커
		if(ggDownCnt > 0){
			$.each(resultGgDown.list,function(i){
				if(i != 0) return; //기점만 표출
					var downStationNo = resultGgDown.list[i].stationNo;
					var downCenterYn = resultGgDown.list[i].centerYn;
					var downStationImg = (downCenterYn == 'Y') ? "station4" : "station2";
					var downStationNm = resultGgDown.list[i].stationNm;
					var downStationSeq = resultGgDown.list[i].stationSeq;
					var downGnm = resultGgDown.list[i].gnm;
					var downStationId = resultGgDown.list[i].stationId;
					var downMobileNoSi = resultGgDown.list[i].mobileNoSi;
					var downLon = resultGgDown.list[i].lon;
					var downLat = resultGgDown.list[i].lat;
					
					//지도 하행 정류소 마커 생성
					var down_size = new Tmap.Size(20, 20);
					var down_offset = new Tmap.Pixel(-(down_size.w / 2), -down_size.h);
					var down_iconHtml = new Tmap.IconHtml('<div class="icon_wa dot routeStation'+i+'"><img src="/gbis2014/images/ico/common/'+downStationImg+'.png" /></div>',down_size,down_offset);
					var down_RouteMarker = new Tmap.Marker(new Tmap.LonLat(downLon, downLat), down_iconHtml);
					
					// 마커 레이어 생성
					map.addLayer(downRouteMarkerLayerArr[multiRouteIdx]);
		
					// 마커 생성
					downRouteMarkerLayerArr[multiRouteIdx].addMarker(down_RouteMarker);
					downRouteMarkerLayerArr[multiRouteIdx].div.style.zIndex = 500;
					
					//팝업 생성
					/****************************************************************************************************
					 * Tmap.Popup.Anchored offset 처리 방식
					 * tl : popup.anchor.offset.x - popup.size.w / popup.anchor.offset.y - popup.size.h
					 * tr : popup.anchor.offset.x + popup.anchor.size.w /  popup.anchor.offset.y - popup.size.h
					 * bl : popup.anchor.offset.x - popup.size.w/ popup.anchor.offset.y + popup.anchor.size.h
					 * br : popup.anchor.offset.x + popup.anchor.size.w / popup.anchor.offset.y + popup.anchor.size.h
					 ****************************************************************************************************/
					downRouteStationObjArr[multiRouteIdx][i] = down_RouteMarker;
					var sizeW = 380;
					var alonlat = new Tmap.LonLat(downLon, downLat);
					var aSize = new Tmap.Size(10, 20);
					var aOffset = new Tmap.Pixel(-(down_size.w / 2), -down_size.h);
					var anchorObj = {
						size : aSize,
						offset : aOffset
					};
					/*
					var cSize = new Tmap.Size(sizeW, 215);
					var label = '<div class="tooltip">';
					label += '<a class="close" href="javascript:tooltipClose()">툴팁닫기</a>';
					label += '<h1>'+downStationNm+' <span class="line">|</span> <span class="station_code">'+downStationNo+'</span><span class="crNm" style="display:none">'+downStationNm+'</span>';
					label += '<span class="routeStationId" style="display:none">'+downStationId+'</span><span class="routeId" style="display:none">'+routeId+'</span></h1>';
					label += '<div class="tooltip_content">';
					label += '<div class="after_bus">';
					label += '<h2>해당 노선 도착예정정보</h2>';
					label += '</div>';
					label += '<div class="station_bus_list one">';
					label += '<ul class="route_station_bus_list_'+downStationId+' routeId_'+routeId+'" style="height:90px">';
					label += '</ul>';
					label += '</div>';
					label += '</div>';
					label += '<div class="tooltip_btn">';
					label += '<button type="button" onclick="btnStartFlag()" class="w_btn start"><span>출발</span></button>\n';
					label += '<button type="button" onclick="btnEndFlag()" class="w_btn end"><span>도착</span></button>';
					label += '</div>';
					label += '<div class="tooltip_arrow"></div>';
					label += '</div>';
					*/
					var cSize = new Tmap.Size(sizeW, 400);
					//하행마커
					var label = '<div class="tooltip"><!--하행마커-->';
					
					label += '<h1><a href="javascript:busStationView(\''+downStationId+'\',\''+downStationNm+'\');" title="같은 정류소명 통합검색 결과 새 창으로 보기">'+downStationNm+' <span class="line">|</span> <span class="station_code" alt="downStationNo">'+downStationNo+'</span><span class="crNm" style="display:none">'+downStationNm+'</span><span class="stationId" style="display:none">'+downStationId+'</span></a></h1>';
					label += '<div class="tooltip_content">';
					label += '<div class="after_bus">';
					label += '<h2>잠시후 도착버스 <span class="line">|</span></h2>';
					label += '<div id="scroller" class="scroller scroller_'+downStationId+'" style="position:relative;margin-left:100px;width:218px;height:31px">';
					label += '<div class="scroller_mask" style="width:210px;height:31px;">';
					label += '<ul class="station_bus_scroll_'+downStationId+'">';
					label += '</ul>';
					label += '</div>';
					label += '<ul class="scroller_nav" style="width: 238px;">';
					label += '<li></li>';
					// label += '<a tabindex="0" title="잠시후 도착버스 더보기"  style="width: 15px; height: 15px; right: 0px; top: 8px; background-image: url(/gbis2014/images/location/bg_tooltip.png); background-position: -20px 0px; background-repeat: no-repeat;"></a>';
					label += '</ul>';
					label += '</div>';
					label += '</div>';
					label += '<div class="station_bus_list">';
					label += '<ul class="station_bus_list_'+downStationId+'">';
					label += '</ul>';
					label += '</div>';
					label += '</div>';
					label += '<div class="tooltip_btn">';
					label += '<button type="button" onclick="btnStartFlag()" class="w_btn start"><span>출발</span></button>\n';
					label += '<button type="button" onclick="btnEndFlag()" class="w_btn end"><span>도착</span></button>';
					label += '</div>';
					label += '<a class="close" title="정류소 도착정보 창 닫기"  href="javascript:tooltipClose()"><i class="fa fa-times" aria-hidden="true"></i></a>';
					label += '<div class="tooltip_arrow"></div>';
					label += '</div>';
					
					down_RouteMarker.popup = new Tmap.Popup.Anchored("customLabel", alonlat, cSize, label, anchorObj, false);
					down_RouteMarker.popup.relativePosition = 'tr';
		
					down_RouteMarker.popup.updateRelativePosition();
					down_RouteMarker.popup.calculateRelativePosition = function(px) {
						return down_RouteMarker.popup.relativePosition;
					};
					down_RouteMarker.popup.panMapIfOutOfView = false; //팝업 지도 중앙에 표출
					down_RouteMarker.popup.keepInMap = false;
					
					//팝업 스타일링 부분
					down_RouteMarker.popup.contentDiv.style.overflow = "hidden";
					down_RouteMarker.popup.contentDiv.style.padding = "0px 0px 30px 0px";
					down_RouteMarker.popup.setBackgroundColor("transparent");
					/*
					map.addPopup(down_RouteMarker.popup);
					var pContentDivW = jQuery(down_RouteMarker.popup.contentDiv).find('div').width();
					down_RouteMarker.popup.anchor.offset.x = down_RouteMarker.popup.anchor.offset.x - (pContentDivW / 2);
					down_RouteMarker.popup.hide();
					*/
					$(down_RouteMarker.icon.imageDiv).find('div').css('cursor', 'pointer'); //마커 오버 시 스타일
					down_RouteMarker.events.register('click', down_RouteMarker, onMarkerClick);
					down_RouteMarker.events.register('mouseover', down_RouteMarker[i], onMouseMarker);
					down_RouteMarker.events.register('mouseout', down_RouteMarker[i], outMouseMarker);
					down_RouteMarker.popup.events.register('mouseover',down_RouteMarker, onMousePopup);
					down_RouteMarker.popup.events.register('mouseout',down_RouteMarker, outMousePopup);
					
	    	});
			
		
			
		}
		
		var url = "/gbis2014/schBusAPI.action";
		var data = 'cmd=searchMapLineJson';
		data += '&routeId='+routeId;
		
		$.ajax({
			type: "post",
			contentType: "application/x-www-form-urlencoded;charset=UTF-8",
			dataType: "json",
			url: url,
			data: data,
			async:false,
			success: getRouteMultiLineSuccess,
			error: ajaxError,
			beforeSend: ajaxBeforeSend
		});
		
		
	}else{
		alert("조회 실패");
	}
}



var multiLineCnt = 0;

function getRouteMultiLineSuccess(data){	
	var resultGgUpline = data.result.gg.upLine;
	var resultGgDownline = data.result.gg.downLine;
	var ggUplineCnt = resultGgUpline.count;
	var ggDownlineCnt = resultGgDownline.count;
	
	//지도 상행 벡터 생성
	var upPointList = [];
	if(ggUplineCnt > 0){
		$.each(resultGgUpline.list,function(i){
			var upLineLinkId = resultGgUpline.list[i].linkId;
			var upLineSeq = resultGgUpline.list[i].seq;
			var upLineLon = resultGgUpline.list[i].lon;
			var upLineLat = resultGgUpline.list[i].lat;
			
			upPointList.push(new Tmap.Geometry.Point(upLineLon, upLineLat));
		});
		
		var up_lineString = new Tmap.Geometry.LineString(upPointList);
		var up_style_bold = {strokeWidth: 5, strokeColor:lineStyleArr[multiLineCnt]}; //라인스타일
		var up_mLineFeature = new Tmap.Feature.Vector(up_lineString, null, up_style_bold);
		up_mLineFeature.attributes.routeNm = "선택하신 노선은 "+multiRouteNm+"번 ("+multiRegion+ ")입니다.";
		
		map.addLayers([up_line_layerArr[multiLineCnt]]);
		up_line_layerArr[multiLineCnt].addFeatures([up_mLineFeature]);
		up_line_layerArr[multiLineCnt].div.style.zIndex = 340;
	}
	
	//지도 하행 벡터 생성
	var downPointList = [];
	if(ggDownlineCnt > 0){
		$.each(resultGgDownline.list,function(i){
			var downLineLinkId = resultGgDownline.list[i].linkId;
			var downLineSeq = resultGgDownline.list[i].seq;
			var downLineLon = resultGgDownline.list[i].lon;
			var downLineLat = resultGgDownline.list[i].lat;
			
			downPointList.push(new Tmap.Geometry.Point(downLineLon, downLineLat));
		});
		
		var down_lineString = new Tmap.Geometry.LineString(downPointList);
		var down_style_bold = {strokeWidth: 5, strokeColor:lineStyleArr[multiLineCnt]}; //라인스타일
		var down_mLineFeature = new Tmap.Feature.Vector(down_lineString, null, down_style_bold);
		down_mLineFeature.attributes.routeNm = "선택하신 노선은 "+multiRouteNm+"번 ("+multiRegion+ ")입니다.";
		map.addLayers([down_line_layerArr[multiLineCnt]]);
		down_line_layerArr[multiLineCnt].addFeatures([down_mLineFeature]);
		down_line_layerArr[multiLineCnt].div.style.zIndex = 340;
	}
	
	upRouteMarkerLayerArr[0].div.style.zIndex = 500;
	downRouteMarkerLayerArr[0].div.style.zIndex = 500;
	
	//다중노선 노선선택 이벤트
	select = new Tmap.Control.SelectFeature([
	                                         up_line_layerArr[0],up_line_layerArr[1],up_line_layerArr[2],up_line_layerArr[3],up_line_layerArr[4],
	                                         up_line_layerArr[5],up_line_layerArr[6],up_line_layerArr[7],up_line_layerArr[8],up_line_layerArr[9],
	                                         down_line_layerArr[0],down_line_layerArr[1],down_line_layerArr[2],down_line_layerArr[3],down_line_layerArr[4],
	                                         down_line_layerArr[5],down_line_layerArr[6],down_line_layerArr[7],down_line_layerArr[8],down_line_layerArr[9]
											],
			{ 
				callbacks: { 
					     click: onClickFeature
					   }
			});
	
  	map.addControl(select);
  	select.activate();
  	
//  multiRouteCnt++;
//	if(multiRouteCnt>=multiRouteCntTotal){
//		zoomToExtent();
//	}
	
	multiLineCnt++;
}

//다중노선 zoomToExtent
function containerValue(a, b, bool){
	if(bool){
		return (a>b) ? a:b;
	}else{
		return (a<b) ? a:b;
	}
}

function zoomToExtent(){
	var r_ext = up_line_layerArr[0].getDataExtent().clone();
	for(var i = 0; i<multiRouteCntTotal; i++){
		var l1  = up_line_layerArr[i].getDataExtent();
		var l2  = down_line_layerArr[i].getDataExtent();
		
		r_ext.left = containerValue(l1.left, r_ext.left, false);
		if(l2 != null) r_ext.left = containerValue(l2.left, r_ext.left, false);
		 
		r_ext.right = containerValue(r_ext.right, l1.right, true );
		if(l2 != null) r_ext.right = containerValue(r_ext.right, l2.right, true );
		 
		r_ext.top = containerValue(l1.top, r_ext.top, true);
		if(l2 != null) r_ext.top = containerValue(l2.top, r_ext.top, true);
		
		r_ext.bottom = containerValue(r_ext.bottom, l1.bottom , false);
		if(l2 != null) r_ext.bottom = containerValue(r_ext.bottom, l2.bottom , false );
		 
	}
	map.zoomToExtent(r_ext);
}

function resetMultiRoute(){
	var chkBox = $(".list_bus li input:checkbox");
	
	chkBox.attr("checked", false); //체크박스 전체 해제
	
	for (var i = 0; i <= 10; i++){
		//기존 다중노선 마커 삭제
		upRouteMarkerLayerArr[i].clearMarkers();
		downRouteMarkerLayerArr[i].clearMarkers();
		//기존 다중노선 경로 삭제
		if(up_line_layerArr[i] != null) up_line_layerArr[i].destroyFeatures();
		if(down_line_layerArr[i] != null) down_line_layerArr[i].destroyFeatures();
	}
}

function ajaxError(data){
	$( "#loading" ).hide();
	//alert("일시적 오류");
	location.reload();
}

function ajaxBeforeSend(){
	if(!gunbunVal){
		$( "#loading" ).show();
	}	
}

function ajaxComplete(){
	$( "#loading" ).hide();
}

function onMousePopup(evt){
	var control = map.controls[0];
	control.deactivate();
}

function outMousePopup(evt){
	var control = map.controls[0];
	control.activate();
}

var listImg;
var thisClass;
var thisIndex;
function onMouseMarker(evt){
	
	var thisClass = $(this.icon.imageDiv).find('div').attr('class'); //클래스명 추출
	thisIndex = thisClass.replace(/[^0-9]/g,''); //숫자만 추출
	
	//정류장 제외
	if(thisClass.indexOf("routeStation") == -1){
		if(thisClass.indexOf("station") != -1){
			if(thisIndex != selectIndex){
				var thisImg = $(this.icon.imageDiv).find('div img').attr("src");
				$(this.icon.imageDiv).find('div img').attr("src", thisImg.replace("station1.png","station5.png"));
			}
		}else{
			var thisImg = $(this.icon.imageDiv).find('div img').attr("src");
			$(this.icon.imageDiv).find('div img').attr("src", thisImg.replace(".png","_on.png"));
		}
	}
	
	if(thisClass.indexOf("poi") != -1){ //장소 탭
		listImg = $("#search_result1 .list_place > li").eq(thisIndex).find("img").attr("src");
		$("#search_result1 .list_place > li").eq(thisIndex).find(".ico img").attr("src", listImg.replace(".png","_on.png"));
		listImg = $("#roadSearchResult .list_place > li").eq(thisIndex).find("img").attr("src");
		$("#roadSearchResult .list_place > li").eq(thisIndex).find(".ico img").attr("src", listImg.replace(".png","_on.png"));
	}else if(thisClass.indexOf("station") != -1){ //정류소 탭
		listImg = $("#search_result1 .list_station > li").eq(thisIndex).find("img").attr("src");
		$("#search_result1 .list_station > li").eq(thisIndex).find(".ico img").attr("src", listImg.replace(".png","_on.png"));
		listImg = $("#roadSearchResult .list_station > li").eq(thisIndex).find("img").attr("src");
		$("#roadSearchResult .list_station > li").eq(thisIndex).find(".ico img").attr("src", listImg.replace(".png","_on.png"));
	}else if(thisClass.indexOf("subway") != -1){ //지하철 탭
		listImg = $("#search_result1 .list_subway > li").eq(thisIndex).find("img").attr("src");
		$("#search_result1 .list_subway > li").eq(thisIndex).find(".ico img").attr("src", listImg.replace(".png","_on.png"));
		listImg = $("#roadSearchResult .list_subway > li").eq(thisIndex).find("img").attr("src");
		$("#roadSearchResult .list_subway > li").eq(thisIndex).find(".ico img").attr("src", listImg.replace(".png","_on.png"));
	}else if(thisClass.indexOf("route") != -1){ //버스 탭
		$("#search_result1 .list_bus > li").eq(thisIndex).css("background", "#ecf5fa");
		$("#roadSearchResult .list_bus > li").eq(thisIndex).css("background", "#ecf5fa");
	}
}

function outMouseMarker(evt){
	var thisClass = $(this.icon.imageDiv).find('div').attr('class'); //클래스명 추출
	//var thisIndex = thisClass.replace(/[^0-9]/g,''); //숫자만 추출
	
	//정류장 제외
	if(thisClass.indexOf("routeStation") == -1){
		if(thisClass.indexOf("station") != -1){
			if(thisIndex != selectIndex){
				var thisImg = $(this.icon.imageDiv).find('div img').attr("src");
				$(this.icon.imageDiv).find('div img').attr("src", thisImg.replace("station5.png","station1.png"));
			}
		}else{
			var thisImg = $(this.icon.imageDiv).find('div img').attr("src");
			$(this.icon.imageDiv).find('div img').attr("src", thisImg.replace("_on.png",".png"));
		}
	}
	
	if(thisClass.indexOf("poi") != -1){
		if((selectSecFlag == 2) && startEndStatus){
			$("#roadSearchResult .list_place > li").eq(thisIndex).find(".ico img").attr("src", listImg);
		}else if((selectSecFlag == 2) && !startEndStatus){
			$("#roadSearchResult .list_place > li").eq(thisIndex).find(".ico img").attr("src", listImg);
		}else{
			listImg = $("#search_result1 .list_place > li").eq(thisIndex).find("img").attr("src");
			$("#search_result1 .list_place > li").eq(thisIndex).find(".ico img").attr("src", listImg.replace("_on.png",".png"));
			listImg = $("#roadSearchResult .list_place > li").eq(thisIndex).find("img").attr("src");
			$("#roadSearchResult .list_place > li").eq(thisIndex).find(".ico img").attr("src", listImg.replace("_on.png",".png"));
		}
	}else if(thisClass.indexOf("station") != -1){
		if((selectSecFlag == 2) && startEndStatus){
			$("#roadSearchResult .list_station > li").eq(thisIndex).find(".ico img").attr("src", listImg);
		}else if((selectSecFlag == 2) && !startEndStatus){
			$("#roadSearchResult .list_station > li").eq(thisIndex).find(".ico img").attr("src", listImg);
		}else{
			listImg = $("#search_result1 .list_station > li").eq(thisIndex).find("img").attr("src");
			$("#search_result1 .list_station > li").eq(thisIndex).find(".ico img").attr("src", listImg.replace("_on.png",".png"));
			listImg = $("#roadSearchResult .list_station > li").eq(thisIndex).find("img").attr("src");
			$("#roadSearchResult .list_station > li").eq(thisIndex).find(".ico img").attr("src", listImg.replace("_on.png",".png"));
		}
	}else if(thisClass.indexOf("subway") != -1){
		if((selectSecFlag == 2) && startEndStatus){
			$("#roadSearchResult .list_subway > li").eq(thisIndex).find(".ico img").attr("src", listImg);
		}else if((selectSecFlag == 2) && !startEndStatus){
			$("#roadSearchResult .list_subway > li").eq(thisIndex).find(".ico img").attr("src", listImg);
		}else{
			listImg = $("#search_result1 .list_subway > li").eq(thisIndex).find("img").attr("src");
			$("#search_result1 .list_subway > li").eq(thisIndex).find(".ico img").attr("src", listImg.replace("_on.png",".png"));
			listImg = $("#roadSearchResult .list_subway > li").eq(thisIndex).find("img").attr("src");
			$("#roadSearchResult .list_subway > li").eq(thisIndex).find(".ico img").attr("src", listImg.replace("_on.png",".png"));
		}
	}else if(thisClass.indexOf("route") != -1){
		$("#search_result1 .list_bus > li").eq(thisIndex).css("background", "none");
		$("#roadSearchResult .list_bus > li").eq(thisIndex).css("background", "none");
	}
}

//버스 정류장 반경조회
//baepro test line
//:8080/gbis2014/schBusAPI.action?cmd=searchAroundSubWayJson&lon=14135098.230677&lat=4518917.0263602&radius=2000
var localBusStatus = false;
function searchAroundBusJson(){
	
	if(localBusStatus){
		if(map.getZoom() > 15){
			//$(".msg").hide(); //배율 메세지 미표출
			
			var url = "/gbis2014/schBusAPI.action";
			var data = 'cmd=searchAroundBusStationJson';
			data += '&lon='+lonlat.lon;
			data += '&lat='+lonlat.lat;
			data += '&radius=2000';
			//반경 지정 
			//ex) 범위 : 10m ~ 2000m
			
			$.ajax({
				type: "post",
				contentType: "application/x-www-form-urlencoded;charset=UTF-8",
				dataType: "json",
				url: url,
				data: data,
				success: searchAroundBusJsonSuccess,
				error: ajaxError
			});
		}
		//배율 메세지 삭제
		/*
		else{
			$(".msg").show(); //배율 메세지 표출
		}*/
	}else{
		//$(".msg").hide(); //배율 메세지 미표출
		localBusMarkerLayer.clearMarkers(); //버스 마커레이어 삭제
	}
}

function busOnOff(){
	if(!localBusStatus){
		//아이콘 클릭시 줌레벨 강제 조정
		if(map.getZoom() < 16) map.zoomTo(16);
		
		$("#localBus").addClass("show");//버스 아이콘 활성화
		$("#wa_busstop").attr("title","주변정류소보기 선택됨");
		localBusStatus = true;
	}else{
		$("#localBus").removeClass("show");//버스 아이콘 비활성화
		$("#wa_busstop").attr("title","");
		localBusStatus = false;
	}
}

function searchAroundBusJsonSuccess(data){
	var resultMap = data.result.resultMap;
	
	//버스 검색결과
	if(resultMap.list.length > 0){
		$.each(resultMap.list,function(i){
			var stationId = resultMap.list[i].stationId;
			var stationNm = resultMap.list[i].stationNm;
			var stationNmOrg = resultMap.list[i].stationNm;
			var toolStationNm = resultMap.list[i].stationNm;
			if(stationNm.length > 15) {
				toolStationNm = stationNm.substring(0,15)+"...";
			}
			var staNoSi = resultMap.list[i].staNoSi;
			var staNo = resultMap.list[i].staNo;
			var staNo_ = resultMap.list[i].staNo;
			if(staNoSi) staNo = staNoSi;
			if(staNoSi == "00000") staNo = staNo_;
			
			var lat = resultMap.list[i].lat;
			var lon = resultMap.list[i].lon;
			
			//통합검색 정류소 검색결과 제외
			for(var j=0; j < stationIdArr.length; j++){
				if(stationIdArr[j] == stationId) return;
			}
			
			//통합검색 정류소 검색결과 제외
			for(var k=0; k < routeStationIdArr.length; k++){
				if(routeStationIdArr[k] == stationId) return;
			}
			
			var size = new Tmap.Size(20, 20);
			var offset = new Tmap.Pixel(-(size.w / 2), -size.h);
			var iconHtml = new Tmap.IconHtml('<div class="icon_wa line localBus"><img src="/gbis2014/images/ico/common/station1.png" alt="'+stationNm+'" /></div>',size,offset);
			//var iconHtml = new Tmap.IconHtml('<div class="localBus"><img src="/gbis2014/images/ico/common/bus.png" alt="'+stationNm+'" /></div>',size,offset);
			localBusMarker = new Tmap.Marker(new Tmap.LonLat(lon, lat), iconHtml);
			// 마커 레이어 생성
			map.addLayer(localBusMarkerLayer);

			// 마커 생성
			localBusMarkerLayer.addMarker(localBusMarker);
			
			//팝업 생성
			/****************************************************************************************************
			 * Tmap.Popup.Anchored offset 처리 방식
			 * tl : popup.anchor.offset.x - popup.size.w / popup.anchor.offset.y - popup.size.h
			 * tr : popup.anchor.offset.x + popup.anchor.size.w /  popup.anchor.offset.y - popup.size.h
			 * bl : popup.anchor.offset.x - popup.size.w/ popup.anchor.offset.y + popup.anchor.size.h
			 * br : popup.anchor.offset.x + popup.anchor.size.w / popup.anchor.offset.y + popup.anchor.size.h
			 ****************************************************************************************************/
			//poiObj[i] = poiMarker;
			var sizeW = 380;
			var alonlat = new Tmap.LonLat(lon, lat);
			var aSize = new Tmap.Size(10, 20);
			var aOffset = new Tmap.Pixel(-(size.w / 2), -size.h);
			var anchorObj = {
				size : aSize,
				offset : aOffset
			};
			var cSize = new Tmap.Size(sizeW, 400);
			//주변정류소보기
			var label = '<div class="tooltip"><!--주변정류소보기-->';
			
			label += '<h1><a href="javascript:busStationView(\''+stationId+'\',\''+stationNmOrg+'\');" title="'+stationNmOrg+' 정류소 통합검색 결과 새 창으로 보기">'+toolStationNm+' <span class="line">|</span> <span class="station_code" alt="staNo">'+staNo+'</span><span class="crNm" style="display:none">'+stationNm+'</span><span class="stationId" style="display:none">'+stationId+'</span></a></h1>';
			label += '<div class="tooltip_content">';
			label += '<div class="after_bus">';
			label += '<h2>잠시후 도착버스 <span class="line">|</span></h2>';
			label += '<div id="scroller" class="scroller scroller_'+stationId+'" style="position:relative;margin-left:100px;width:218px;height:31px">';
			label += '<div class="scroller_mask" style="width:210px;height:31px;">';
			label += '<ul class="station_bus_scroll_'+stationId+'">';
			label += '</ul>';
			label += '</div>';
			label += '<ul class="scroller_nav" style="width: 238px;">';
			label += '<li></li>';
			// label += '<a tabindex="0" title="잠시후 도착버스 더보기"  style="width: 15px; height: 15px; right: 0px; top: 8px; background-image: url(/gbis2014/images/location/bg_tooltip.png); background-position: -20px 0px; background-repeat: no-repeat;"></a>';
			label += '</ul>';
			label += '</div>';
			label += '</div>';
			label += '<div class="station_bus_list">';
			label += '<ul class="station_bus_list_'+stationId+'">';
			label += '</ul>';
			label += '</div>';
			label += '</div>';
			label += '<div class="tooltip_btn">';
			label += '<button type="button" onclick="btnStartFlag()" class="w_btn start"><span>출발</span></button>\n';
			label += '<button type="button" onclick="btnEndFlag()" class="w_btn end"><span>도착</span></button>';
			label += '</div>';
			label += '<a class="close" title="정류소 도착정보 창 닫기"  href="javascript:tooltipClose()"><i class="fa fa-times" aria-hidden="true"></i></a>';
			label += '<div class="tooltip_arrow"></div>';
			label += '</div>';
			
			localBusMarker.popup = new Tmap.Popup.Anchored("customLabel", alonlat, cSize, label, anchorObj, false);
			localBusMarker.popup.relativePosition = 'tr';

			localBusMarker.popup.updateRelativePosition();
			localBusMarker.popup.calculateRelativePosition = function(px) {
				return localBusMarker.popup.relativePosition;
			};
			localBusMarker.popup.panMapIfOutOfView = false;
			localBusMarker.popup.keepInMap = false;
			
			//팝업 스타일링 부분
			localBusMarker.popup.contentDiv.style.overflow = "hidden";
			localBusMarker.popup.contentDiv.style.padding = "0px 0px 30px 0px";
			localBusMarker.popup.setBackgroundColor("transparent");
			/*
			map.addPopup(localBusMarker.popup);
			var pContentDivW = jQuery(localBusMarker.popup.contentDiv).find('div').width();
			localBusMarker.popup.anchor.offset.x = localBusMarker.popup.anchor.offset.x - (pContentDivW / 2);
			localBusMarker.popup.hide();
			*/
			$(localBusMarker.icon.imageDiv).find('div').css('cursor', 'pointer'); //마커 오버 시 스타일
			localBusMarker.events.register('click', localBusMarker, onMarkerClick);
			
			
			/*
			var index = resultMap.list[i].index;
			var lat = resultMap.list[i].lat;
			var lon = resultMap.list[i].lon;
			var name = resultMap.list[i].name;
			var regionCode = resultMap.list[i].regionCode;
			var regionName = resultMap.list[i].regionName;
			var regionalStationId = resultMap.list[i].regionalStationId;
			var stationClass = resultMap.list[i].stationClass; //1.버스,  2.지하철
			var stationId = resultMap.list[i].stationId;
			var fullAddr = resultMap.list[i].fullAddr;
			
			//버스 일때
			if(stationClass == 1){
				var size = new Tmap.Size(20, 20);
				var offset = new Tmap.Pixel(-(size.w / 2), -size.h);
				var iconHtml = new Tmap.IconHtml('<div class="localBus"><img src="/gbis2014/images/ico/common/bus.png" alt="'+name+'" /></div>',size,offset);
				localBusMarker = new Tmap.Marker(new Tmap.LonLat(lon, lat), iconHtml);
				// 마커 레이어 생성
				map.addLayer(localBusMarkerLayer);

				// 마커 생성
				localBusMarkerLayer.addMarker(localBusMarker);
				
				//팝업 생성
				*//****************************************************************************************************
				 * Tmap.Popup.Anchored offset 처리 방식
				 * tl : popup.anchor.offset.x - popup.size.w / popup.anchor.offset.y - popup.size.h
				 * tr : popup.anchor.offset.x + popup.anchor.size.w /  popup.anchor.offset.y - popup.size.h
				 * bl : popup.anchor.offset.x - popup.size.w/ popup.anchor.offset.y + popup.anchor.size.h
				 * br : popup.anchor.offset.x + popup.anchor.size.w / popup.anchor.offset.y + popup.anchor.size.h
				 ****************************************************************************************************//*
				//poiObj[i] = poiMarker;
				var sizeW = 380;
				var alonlat = new Tmap.LonLat(lon, lat);
				var aSize = new Tmap.Size(10, 20);
				var aOffset = new Tmap.Pixel(-(size.w / 2), -size.h);
				var anchorObj = {
					size : aSize,
					offset : aOffset
				};
				var cSize = new Tmap.Size(sizeW, 183);
				
				var label = '<div class="tooltip">';
				label += '<a class="close" href="javascript:tooltipClose()">툴팁닫기</a>';
				label += '<h1>'+name+'<span class="crNm" style="display:none">'+name+'</span></h1>';
				label += '<div class="tooltip_content">';
				label += '<div class="inner">';
				label += fullAddr;
				label += '</div>';
				label += '</div>';
				label += '<div class="tooltip_btn">';
				label += '<button type="button" onclick="setCommonFlag(0, \''+name+'\', \''+lon+'\', \''+lat+'\')" class="w_btn start"><span>출발</span></button>\n';
				label += '<button type="button" onclick="setCommonFlag(1, \''+name+'\', \''+lon+'\', \''+lat+'\')" class="w_btn end"><span>도착</span></button>';
				label += '</div>';
				label += '<div class="tooltip_arrow"></div>';
				label += '</div>';
				
				localBusMarker.popup = new Tmap.Popup.Anchored("customLabel", alonlat, cSize, label, anchorObj, false);
				localBusMarker.popup.relativePosition = 'tr';

				localBusMarker.popup.updateRelativePosition();
				localBusMarker.popup.calculateRelativePosition = function(px) {
					return localBusMarker.popup.relativePosition;
				};
				localBusMarker.popup.panMapIfOutOfView = false;
				localBusMarker.popup.keepInMap = false;
				
				//팝업 스타일링 부분
				localBusMarker.popup.contentDiv.style.overflow = "hidden";
				localBusMarker.popup.contentDiv.style.padding = "0px 0px 30px 0px";
				localBusMarker.popup.setBackgroundColor("transparent");
				
				map.addPopup(localBusMarker.popup);
				var pContentDivW = jQuery(localBusMarker.popup.contentDiv).find('div').width();
				localBusMarker.popup.anchor.offset.x = localBusMarker.popup.anchor.offset.x - (pContentDivW / 2);
				localBusMarker.popup.hide();
				
				$(localBusMarker.icon.imageDiv).find('div').css('cursor', 'pointer'); //마커 오버 시 스타일
				localBusMarker.events.register('click', localBusMarker, onMarkerClick);
			}
			*/
    	});
		
		
	}
	
}

//지하철 정류장 반경조회
//baepro test line
////:8080/gbis2014/schBusAPI.action?cmd=searchAroundSubWayJson&lon=14135098.230677&lat=4518917.0263602&radius=2000
var localSubwayStatus = false;
function searchAroundSubwayJson(){
	if(localSubwayStatus){
		if(map.getZoom() > 15){
			//$(".msg").hide(); //배율 메세지 미표출
			
			var url = "/gbis2014/schBusAPI.action";
			var data = 'cmd=searchAroundSubWayJson';
			data += '&lon='+lonlat.lon;
			data += '&lat='+lonlat.lat;
			data += '&radius=2000';
			//반경 지정 
			//ex) 범위 : 10m ~ 2000m
			
			$.ajax({
				type: "post",
				contentType: "application/x-www-form-urlencoded;charset=UTF-8",
				dataType: "json",
				url: url,
				data: data,
				success: searchAroundSubwayJsonSuccess,
				error: ajaxError
			});
		}
		//배율 메세지 삭제
		/*
		else{
			$(".msg").show(); //배율 메세지 표출
		}*/
	}else{
		//$(".msg").hide(); //배율 메세지 미표출
		localSubwayMarkerLayer.clearMarkers(); //지하철 마커레이어 삭제
	}
}

function subwayOnOff(){
	if(!localSubwayStatus){
		//아이콘 클릭시 줌레벨 강제 조정
		if(map.getZoom() < 16) map.zoomTo(16);
		
		$("#localSubway").addClass("show");//지하철 아이콘 활성화
		$("#wa_subway").attr("title","주변지하철보기 선택됨");
		localSubwayStatus = true;
	}else{
		$("#localSubway").removeClass("show");//지하철 아이콘 비활성화
		$("#wa_subway").attr("title","");
		localSubwayStatus = false;
	}
}

function searchAroundSubwayJsonSuccess(data){
	
	var resultMap = data.result.resultMap;

	//지하철 검색결과
	if(resultMap.list.length > 0){
		$.each(resultMap.list,function(i){
			
			var index = resultMap.list[i].index;
			var lat = resultMap.list[i].lat;
			var lon = resultMap.list[i].lon;
			var name = resultMap.list[i].name;
			var regionCode = resultMap.list[i].regionCode;
			var regionName = resultMap.list[i].regionName;
			var regionalStationId = resultMap.list[i].regionalStationId;
			var stationClass = resultMap.list[i].stationClass; //1.버스,  2.지하철
			var stationId = resultMap.list[i].stationId;
			var fullAddr = resultMap.list[i].fullAddr;
			
			//지하철 일때
			if(stationClass == 2){
				var size = new Tmap.Size(20, 20);
				var offset = new Tmap.Pixel(-(size.w / 2), -size.h);
				var iconHtml = new Tmap.IconHtml('<div class="localSubway"><img src="/gbis2014/images/ico/common/subway.png" alt="'+name+'" /></div>',size,offset);
				
				localSubwayMarker = new Tmap.Marker(new Tmap.LonLat(lon, lat), iconHtml);
				// 마커 레이어 생성
				map.addLayer(localSubwayMarkerLayer);

				// 마커 생성
				localSubwayMarkerLayer.addMarker(localSubwayMarker);
				
				//팝업 생성
				/****************************************************************************************************
				 * Tmap.Popup.Anchored offset 처리 방식
				 * tl : popup.anchor.offset.x - popup.size.w / popup.anchor.offset.y - popup.size.h
				 * tr : popup.anchor.offset.x + popup.anchor.size.w /  popup.anchor.offset.y - popup.size.h
				 * bl : popup.anchor.offset.x - popup.size.w/ popup.anchor.offset.y + popup.anchor.size.h
				 * br : popup.anchor.offset.x + popup.anchor.size.w / popup.anchor.offset.y + popup.anchor.size.h
				 ****************************************************************************************************/
				//poiObj[i] = poiMarker;
				var sizeW = 380;
				var alonlat = new Tmap.LonLat(lon, lat);
				var aSize = new Tmap.Size(10, 20);
				var aOffset = new Tmap.Pixel(-(size.w / 2), -size.h);
				var anchorObj = {
					size : aSize,
					offset : aOffset
				};
				var cSize = new Tmap.Size(sizeW, 183);
				
				var label = '<div class="tooltip">';
				
				label += '<h1>'+name+'<span class="crNm" style="display:none">'+name+'</span></h1>';
				label += '<div class="tooltip_content">';
				label += '<div class="inner">';
				label += fullAddr;
				label += '</div>';
				label += '</div>';
				label += '<div class="tooltip_btn">';
				label += '<button type="button" onclick="setCommonFlag(0, \''+name+'\', \''+lon+'\', \''+lat+'\')" class="w_btn start"><span>출발</span></button>\n';
				label += '<button type="button" onclick="setCommonFlag(1, \''+name+'\', \''+lon+'\', \''+lat+'\')" class="w_btn end"><span>도착</span></button>';
				label += '</div>';
				label += '<a class="close" title="정류소 도착정보 창 닫기"  href="javascript:tooltipClose()"><i class="fa fa-times" aria-hidden="true"></i></a>';
				label += '<div class="tooltip_arrow"></div>';
				label += '</div>';
				
				localSubwayMarker.popup = new Tmap.Popup.Anchored("customLabel", alonlat, cSize, label, anchorObj, false);
				localSubwayMarker.popup.relativePosition = 'tr';

				localSubwayMarker.popup.updateRelativePosition();
				localSubwayMarker.popup.calculateRelativePosition = function(px) {
					return localSubwayMarker.popup.relativePosition;
				};
				localSubwayMarker.popup.panMapIfOutOfView = false;
				localSubwayMarker.popup.keepInMap = false;
				
				//팝업 스타일링 부분
				localSubwayMarker.popup.contentDiv.style.overflow = "hidden";
				localSubwayMarker.popup.contentDiv.style.padding = "0px 0px 30px 0px";
				localSubwayMarker.popup.setBackgroundColor("transparent");
				/*
				map.addPopup(localSubwayMarker.popup);
				var pContentDivW = jQuery(localSubwayMarker.popup.contentDiv).find('div').width();
				localSubwayMarker.popup.anchor.offset.x = localSubwayMarker.popup.anchor.offset.x - (pContentDivW / 2);
				localSubwayMarker.popup.hide();
				*/
				$(localSubwayMarker.icon.imageDiv).find('div').css('cursor', 'pointer'); //마커 오버 시 스타일
				localSubwayMarker.events.register('click', localSubwayMarker, onMarkerClick);
			}
    	});
	}
	
}

//공공기관 반경조회
var localOfficeStatus = false;
function searchAroundPublicPOIJson(){
	
	if(localOfficeStatus){
		if(map.getZoom() > 15){
			//$(".msg").hide(); //배율 메세지 미표출
			
			var url = "/gbis2014/schBusAPI.action";
			var data = 'cmd=searchAroundPublicPOIJson';
			data += '&lon='+lonlat.lon;
			data += '&lat='+lonlat.lat;
			data += '&radius=1';
			//범위 : 1 ~ 33
			//ex) {1:300m , 2:600m , 3:900m , … , 33:9900m}
			
			$.ajax({
				type: "post",
				contentType: "application/x-www-form-urlencoded;charset=UTF-8",
				dataType: "json",
				url: url,
				data: data,
				success: searchAroundPublicPOIJsonSuccess,
				error: ajaxError
			});
		}
		//배율 메세지 삭제
		/*
		else{
			$(".msg").show(); //배율 메세지 표출
		}*/
	}else{
		//$(".msg").hide(); //배율 메세지 미표출
		localOfficeMarkerLayer.clearMarkers(); //공공기관 마커레이어 삭제
	}
}

function publicOnOff(){
	if(!localOfficeStatus){
		//아이콘 클릭시 줌레벨 강제 조정
		if(map.getZoom() < 16) map.zoomTo(16);
		
		$("#localPublic").addClass("show");//공공기관 아이콘 활성화
		$("#wa_public").attr("title","주변관공서보기 선택됨");
		localOfficeStatus = true;
	}else{
		$("#localPublic").removeClass("show");//공공기관 아이콘 비활성화
		$("#wa_public").attr("title","");
		localOfficeStatus = false;
	}
}

function searchAroundPublicPOIJsonSuccess(data){
	var resultPublic = data.result.poi;
	var poiCnt = resultPublic.count;
	
	//공공기관 검색결과
	if(poiCnt > 0){
		$.each(resultPublic.list,function(i){
			
			var lat = resultPublic.list[i].lat;
			var lon = resultPublic.list[i].lon;
			var poiAddrName = resultPublic.list[i].poiAddrName;
			var poiBuildingNo1 = resultPublic.list[i].poiBuildingNo1;
			var poiBuildingNo2 = resultPublic.list[i].poiBuildingNo2;
			var poiId = resultPublic.list[i].poiId;
			var poiMerchantFlag = resultPublic.list[i].poiMerchantFlag;
			var poiNm = resultPublic.list[i].poiNm;
			var poiParkFlag = resultPublic.list[i].poiParkFlag;
			var poiRoadName = resultPublic.list[i].poiRoadName;
			var poiRpFlag = resultPublic.list[i].poiRpFlag;
			var poiTelNo = resultPublic.list[i].poiTelNo;
			
			var size = new Tmap.Size(20, 20);
			var offset = new Tmap.Pixel(-(size.w / 2), -size.h);
			var iconHtml = new Tmap.IconHtml('<div class="localOffice"><img src="/gbis2014/images/ico/common/office.png" alt="'+poiNm+'" /></div>',size,offset);
			localOfficeMarker = new Tmap.Marker(new Tmap.LonLat(lon, lat), iconHtml);
			// 마커 레이어 생성
			map.addLayer(localOfficeMarkerLayer);

			// 마커 생성
			localOfficeMarkerLayer.addMarker(localOfficeMarker);

			//팝업 생성
			/****************************************************************************************************
			 * Tmap.Popup.Anchored offset 처리 방식
			 * tl : popup.anchor.offset.x - popup.size.w / popup.anchor.offset.y - popup.size.h
			 * tr : popup.anchor.offset.x + popup.anchor.size.w /  popup.anchor.offset.y - popup.size.h
			 * bl : popup.anchor.offset.x - popup.size.w/ popup.anchor.offset.y + popup.anchor.size.h
			 * br : popup.anchor.offset.x + popup.anchor.size.w / popup.anchor.offset.y + popup.anchor.size.h
			 ****************************************************************************************************/
			//poiObj[i] = poiMarker;
			var sizeW = 380;
			var alonlat = new Tmap.LonLat(lon, lat);
			var aSize = new Tmap.Size(10, 20);
			var aOffset = new Tmap.Pixel(-(size.w / 2), -size.h);
			var anchorObj = {
				size : aSize,
				offset : aOffset
			};
			var cSize = new Tmap.Size(sizeW, 183);
			
			var label = '<div class="tooltip">';
			
			label += '<h1>'+poiNm+'<span class="crNm" style="display:none">'+poiNm+'</span></h1>';
			label += '<div class="tooltip_content">';
			label += '<div class="inner">';
			label += poiTelNo+'<br />';
			label += poiAddrName;
			label += '</div>';
			label += '</div>';
			label += '<div class="tooltip_btn">';
			label += '<button type="button" onclick="setCommonFlag(0, \''+poiNm+'\', \''+lon+'\', \''+lat+'\')" class="w_btn start"><span>출발</span></button>\n';
			label += '<button type="button" onclick="setCommonFlag(1, \''+poiNm+'\', \''+lon+'\', \''+lat+'\')" class="w_btn end"><span>도착</span></button>';
			label += '</div>';
			label += '<a class="close"  title="정류소 도착정보 창 닫기"  href="javascript:tooltipClose()"><i class="fa fa-times" aria-hidden="true"></i></a>';
			label += '<div class="tooltip_arrow"></div>';
			label += '</div>';
			
			localOfficeMarker.popup = new Tmap.Popup.Anchored("customLabel", alonlat, cSize, label, anchorObj, false);
			localOfficeMarker.popup.relativePosition = 'tr';

			localOfficeMarker.popup.updateRelativePosition();
			localOfficeMarker.popup.calculateRelativePosition = function(px) {
				return localOfficeMarker.popup.relativePosition;
			};
			localOfficeMarker.popup.panMapIfOutOfView = false;
			localOfficeMarker.popup.keepInMap = false;
			
			//팝업 스타일링 부분
			localOfficeMarker.popup.contentDiv.style.overflow = "hidden";
			localOfficeMarker.popup.contentDiv.style.padding = "0px 0px 30px 0px";
			localOfficeMarker.popup.setBackgroundColor("transparent");
			/*
			map.addPopup(localOfficeMarker.popup);
			var pContentDivW = jQuery(localOfficeMarker.popup.contentDiv).find('div').width();
			localOfficeMarker.popup.anchor.offset.x = localOfficeMarker.popup.anchor.offset.x - (pContentDivW / 2);
			localOfficeMarker.popup.hide();
			*/
			$(localOfficeMarker.icon.imageDiv).find('div').css('cursor', 'pointer'); //마커 오버 시 스타일
			localOfficeMarker.events.register('click', localOfficeMarker, onMarkerClick);
			
    	});
	}
}

function selectUpLineBusLayer(){
	upRealBusRouteMarkerLayer.setVisibility(true);
	downRealBusRouteMarkerLayer.setVisibility(false);
	upRealBusRouteLowMarkerLayer.setVisibility(false);
	downRealBusRouteLowMarkerLayer.setVisibility(false);
	$(".bus_lineView li").removeClass("show");
	$("#selectUpLineBus").addClass("show");
	$('#wa_downbound').attr("title","");
	$('#wa_lowfloor').attr("title","");
	$('#wa_removeBus').attr("title","");
	$('#wa_allBus').attr("title","");
	$('#wa_upbound').attr("title","상행버스보기 선택됨");
}

function selectDownLineBusLayer(){
	upRealBusRouteMarkerLayer.setVisibility(false);
	downRealBusRouteMarkerLayer.setVisibility(true);
	upRealBusRouteLowMarkerLayer.setVisibility(false);
	downRealBusRouteLowMarkerLayer.setVisibility(false);
	$(".bus_lineView li").removeClass("show");
	$("#selectDownLineBus").addClass("show");
	$('#wa_upbound').attr("title","");
	$('#wa_lowfloor').attr("title","");
	$('#wa_removeBus').attr("title","");
	$('#wa_allBus').attr("title","");
	$('#wa_downbound').attr("title","하행버스보기 선택됨");
}

function selectLowBusLayer(){
	upRealBusRouteMarkerLayer.setVisibility(false);
	downRealBusRouteMarkerLayer.setVisibility(false);
	upRealBusRouteLowMarkerLayer.setVisibility(true);
	downRealBusRouteLowMarkerLayer.setVisibility(true);
	$(".bus_lineView li").removeClass("show");
	$("#selectLowBus").addClass("show");
	$('#wa_upbound').attr("title","");
	$('#wa_downbound').attr("title","");
	$('#wa_removeBus').attr("title","");
	$('#wa_allBus').attr("title","");
	$('#wa_lowfloor').attr("title","저상버스보기 선택됨");
}

function selectHiddenBusLayer(){
	upRealBusRouteMarkerLayer.setVisibility(false);
	downRealBusRouteMarkerLayer.setVisibility(false);
	upRealBusRouteLowMarkerLayer.setVisibility(false);
	downRealBusRouteLowMarkerLayer.setVisibility(false);
	$(".bus_lineView li").removeClass("show");
	$("#selectHiddenBus").addClass("show");
	$('#wa_upbound').attr("title","");
	$('#wa_downbound').attr("title","");
	$('#wa_lowfloor').attr("title","");
	$('#wa_allBus').attr("title","");
	$('#wa_removeBus').attr("title","버스안보기 선택됨");
}

function selectShowBusLayer(){
	upRealBusRouteMarkerLayer.setVisibility(true);
	downRealBusRouteMarkerLayer.setVisibility(true);
	upRealBusRouteLowMarkerLayer.setVisibility(true);
	downRealBusRouteLowMarkerLayer.setVisibility(true);
	$(".bus_lineView li").removeClass("show");
	$("#selectShowBus").addClass("show");
	$('#wa_upbound').attr("title","");
	$('#wa_downbound').attr("title","");
	$('#wa_lowfloor').attr("title","");
	$('#wa_removeBus').attr("title","");
	$('#wa_allBus').attr("title","모든버스보기 선택됨");
}

// 실시간 버스 정보 클릭시 이벤트
function realTimeBusInfoChange(busNum, routeId){
	jQuery("#allSearch").css("display", "none");
	jQuery("#roadSearch").css("display", "none");
	jQuery("#realTimeBus").css("display", "");
	
	jQuery(".local_info").css("display","none");
	jQuery(".icon_info").css("display", "");
	jQuery(".icon_info .cross").css("display", "none");
	jQuery('.route_dtl').hide();
	
	//탭이동 검색 결과 리셋
	selectTabReset();
	
	//플래그 설정
	selectSecFlag = i;
	
	searchRealtime(busNum, routeId); // 실시간버스와 연동
	jQuery('.menu').addClass('active_tab3'); // 실시간버스 탭 활성화
}

//버스 번호 클릭시 버스노선 정보로 바로 가기
function busInfoSuccess(data){
	
	var resultBusRoute = data.result.busRoute;
	$.each(resultBusRoute.list,function(i){
		var routeNm = resultBusRoute.list[i].routeNm;
		if(mainSearchTxt == routeNm){
			var routeId = resultBusRoute.list[i].routeId;
			if(routeIdVal){
				if(routeIdVal == routeId){
					var siFlag = resultBusRoute.list[i].siFlag;
					var routeTp = resultBusRoute.list[i].routeTp;
					getRouteDetail(routeId, routeNm, siFlag, routeTp);
				}
			}else{
				var siFlag = resultBusRoute.list[i].siFlag;
				var routeTp = resultBusRoute.list[i].routeTp;
				getRouteDetail(routeId, routeNm, siFlag, routeTp);
			}
		}
		
	});
}

var popStationStationNm;
var popStationstationNo;
function searchPopStation(stationNm,stationNo){
	
	popStationStationNm = stationNm;
	popStationstationNo = stationNo;
	
	jQuery(".busLine_detail2").html("");
	
	var url = "/gbis2014/schBusAPI.action";
	var data = 'cmd=searchBusStationJson';
	data += '&stationId='+station_id;
	
	$.ajax({
		type: "post",
		contentType: "application/x-www-form-urlencoded;charset=UTF-8",
		dataType: "json",
		url: url,
		data: data,
		success: searchPopStationSuccess,
		error: ajaxError
	});
	
	//경로탐색이 아닐 때
	if(selectSecFlag != 2){
		jQuery(".busLine_detail2").show();
	}
	
}

function searchPopStationSuccess(data){
	
	var busLineDetail = "";
	var className = "";
	var iconTag = '<span style="display:inline-block;float:left;width:35px;height:35px;background:#background;border-radius:2px;font-size:13px;font-weight:900;color:#color;text-align:center;line-height:35px;box-shadow:0px 1px 2px rgb(0 0 0 / 10%);margin-right:5px;">#text</span>';
	var iconImg = "";
	var routeTpNm="";
	
	if(data.success){
		var result = data.result;
		var count = result.count;
		var stationNm = result.stationNm;
		if(stationNm.length > 16) stationNm = stationNm.substring(0,16)+"...";
		var stationNmOrg = result.stationNm;
		var stationId = result.stationId;
		var busArrivalList = result.busArrivalList;
		var busArrivalInfo = result.busArrivalInfo;
		var busStationInfo = result.busStationInfo;
		
		var arrivalInfoStat = false; //도착예정목록에 노선정보가 있는지 유무
		
		busLineDetail += '<div class="dtl_hd bx_station">';
		busLineDetail += '	<span class="station_tit" title="'+stationNmOrg+'"><strong>'+stationNm+'</strong></span>';
		busLineDetail += '	<span class="station_no">'+popStationstationNo+'</span>';
		busLineDetail += '<a href="#" onclick="detailLineClose();return false" class="btn_close">닫기</a>';
		busLineDetail += '</div>';
		busLineDetail += '<ul class="list_cmn list_bus" id="getMultiRoute" style="height:calc(100% - 104px);">';
		busLineDetail += '	<li class="btn_multi" style="text-align:center;margin-left:0px;">';
		busLineDetail += '		<a href="javascript:detailLineGetMultiRoute()" class="view" style="float:none;width:40%;">다중노선 보기</a>';
		busLineDetail += '		<a href="javascript:resetMultiRoute()" class="reset" style="float:none;width:40%;">초기화</a>';
		busLineDetail += '	</li>';
		
		$.each(busStationInfo,function(i){
			
			var stationRouteId = busStationInfo[i].routeId;
			var stationRouteName = busStationInfo[i].routeName;
			var stationRouteDestName =  busStationInfo[i].routeDestName;
			var stationStaOrder =  busStationInfo[i].staOrder;
			
			arrivalInfoStat = false; //도착예정목록에 노선정보가 있는지 유무 초기화
			
			$.each(busArrivalInfo,function(i){
				
				var routeId = busArrivalInfo[i].routeId;
				var routeTypeCd = busArrivalInfo[i].routeTypeCd;
				var routeName = busArrivalInfo[i].routeName;
				var routeDestName = busArrivalInfo[i].routeDestName;
				var flag = busArrivalInfo[i].flag;
				var plateNo1 = busArrivalInfo[i].plateNo1;
				var predictTime1 = busArrivalInfo[i].predictTime1;
				var locationNo1 = busArrivalInfo[i].locationNo1;
				var remainSeatCnt1 = busArrivalInfo[i].remainSeatCnt1;
				var delayYn1 = busArrivalInfo[i].delayYn1;
				var plateNo2 = busArrivalInfo[i].plateNo2;
				var predictTime2 = busArrivalInfo[i].predictTime2;
				var locationNo2 = busArrivalInfo[i].locationNo2;
				var remainSeatCnt2 = busArrivalInfo[i].remainSeatCnt2;
				var delayYn2 = busArrivalInfo[i].delayYn2;
				var crowded1 = busArrivalInfo[i].crowded1;
				var crowded2 = busArrivalInfo[i].crowded2;
				var siFlag = 0;
				var staOrder = busArrivalInfo[i].staOrder;
				
	            
	            //노선번호 색상
				/*
				Route_tp = 11, 21, 14  --> red(직행)
				Route_tp = 12  --> blue
				Route_tp = 30  --> yellow
				Route_tp = 41, 42, 43  --> violet(시외)
				Route_tp = 51, 52, 53  --> grey (공항)
				나머지 --> green
				 */
				if(routeTypeCd == 11 || routeTypeCd == 21 || routeTypeCd == 14 || routeTypeCd == 16){
					className = "num_red";
				}else if(routeTypeCd == 12){
					className = "num_blue";
				}else if(routeTypeCd == 30  ){
					className = "num_yellow";
				}else if(routeTypeCd == 41 || routeTypeCd == 42 || routeTypeCd == 43){
					className = "num_purple";
				}else if(routeTypeCd == 51 || routeTypeCd == 52 || routeTypeCd == 53){
					className = "num_gray";
				}else{
					className = "num_green";
				}
				
				//노선 아이콘
				/*
				SI_FLAG = 1 --> 서울
					Route_tp = 51,52, 53  --> 공항버스(seoul.gif, airport.gif)
					Route_tp = 41, 42, 43  --> 시외버스(seoul.gif, si.gif)
					Route_tp = 나머지 --> seoul.gif
				SI_FLAG = 3 --> 인천
					Route_tp = 51,52, 53  --> 공항버스(inchon.gif airport.gif)
					Route_tp = 41, 42, 43  --> 시외버스(inchon.gif, si.gif)
					Route_tp = 나머지 --> inchon.gif
				SI_FLAG = 나머지 --> 경기도
					Route_tp = 51,52, 53  --> 공항버스(airport.gif)
					Route_tp = 41, 42, 43  --> 시외버스(si.gif)
					Route_tp = 나머지 --> 이미지 없음
				 */
				if(siFlag == 1){ //서울
					if(routeTypeCd == 51 || routeTypeCd == 52 || routeTypeCd == 53){
						routeTpNm="공항";
						iconImg = iconTag.replace("#background","#558ed5").replace("#color","#fff").replace("#text","서울");
						iconImg += iconTag.replace("#background","#6d6d6d").replace("#color","#fff").replace("#text",routeTpNm);
						//iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/4.png" alt="공항" />';
					}else if(routeTypeCd == 41 || routeTypeCd == 42 || routeTypeCd == 43){
						routeTpNm="시외";
						iconImg = iconTag.replace("#background","#558ed5").replace("#color","#fff").replace("#text","서울");
						iconImg += iconTag.replace("#background","#8400ff").replace("#color","#fff").replace("#text",routeTpNm);
						//iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/3.png" alt="시외" />';
					}else if(routeTypeCd == 11 || routeTypeCd == 21 || routeTypeCd == 16){
						routeTpNm="직좌";
						iconImg = iconTag.replace("#background","#558ed5").replace("#color","#fff").replace("#text","서울");
						iconImg += iconTag.replace("#background","#ff0000").replace("#color","#fff").replace("#text",routeTpNm);
						//iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/7_1.png" alt="직좌" />';
					}else if(routeTypeCd == 14){
						routeTpNm="광역";
						iconImg = iconTag.replace("#background","#558ed5").replace("#color","#fff").replace("#text","서울");
						iconImg += iconTag.replace("#background","#ff0000").replace("#color","#fff").replace("#text",routeTpNm);
						//iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/7_1.png" alt="직좌" />';	
					}else if(routeTypeCd == 12 ){
						routeTpNm="좌석";
						iconImg = iconTag.replace("#background","#558ed5").replace("#color","#fff").replace("#text","서울");
						iconImg += iconTag.replace("#background","#0000ff").replace("#color","#fff").replace("#text",routeTpNm);
						//iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/5_1.png" alt="좌석" />';
					}else if(routeTypeCd == 30){
						routeTpNm="마을";
						iconImg = iconTag.replace("#background","#558ed5").replace("#color","#fff").replace("#text","서울");
						iconImg += iconTag.replace("#background","#efe600").replace("#color","#000").replace("#text",routeTpNm);
						//iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/9_7.png" alt="마을" />';
					}else{
						routeTpNm="일반";
//						iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />';
						iconImg = iconTag.replace("#background","#558ed5").replace("#color","#fff").replace("#text","서울");
						iconImg += iconTag.replace("#background","#0b7240").replace("#color","#fff").replace("#text",routeTpNm);
						//iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/6_1.png" alt="일반" />';
					}
				}else if(siFlag == 3){ //인천
					if(routeTypeCd == 51 || routeTypeCd == 52 || routeTypeCd == 53){
						routeTpNm="공항";
						iconImg = iconTag.replace("#background","#0b7204").replace("#color","#fff").replace("#text","인천");
						iconImg += iconTag.replace("#background","#6d6d6d").replace("#color","#fff").replace("#text",routeTpNm);
						//iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/4.png" alt="공항" />';
					}else if(routeTypeCd == 41 || routeTypeCd == 42 || routeTypeCd == 43){
						routeTpNm="시외";
						iconImg = iconTag.replace("#background","#0b7204").replace("#color","#fff").replace("#text","인천");
						iconImg += iconTag.replace("#background","#8400ff").replace("#color","#fff").replace("#text",routeTpNm);
						//iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/3.png" alt="시외" />';
					}else if(routeTypeCd == 11 || routeTypeCd == 21 || routeTypeCd == 16){
						routeTpNm="직좌";
						iconImg = iconTag.replace("#background","#0b7204").replace("#color","#fff").replace("#text","인천");
						iconImg += iconTag.replace("#background","#ff0000").replace("#color","#fff").replace("#text",routeTpNm);
						//iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/7_1.png" alt="직좌" />';
					}else if(routeTypeCd == 14){
						routeTpNm="광역";
						iconImg = iconTag.replace("#background","#0b7204").replace("#color","#fff").replace("#text","인천");
						iconImg += iconTag.replace("#background","#ff0000").replace("#color","#fff").replace("#text",routeTpNm);
						//iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/7_1.png" alt="직좌" />';	
					}else if(routeTypeCd == 12 ){
						routeTpNm="좌석";
						iconImg = iconTag.replace("#background","#0b7204").replace("#color","#fff").replace("#text","인천");
						iconImg += iconTag.replace("#background","#0000ff").replace("#color","#fff").replace("#text",routeTpNm);
						//iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/5_1.png" alt="좌석" />';
					}else if(routeTypeCd == 30){
						routeTpNm="마을";
						iconImg = iconTag.replace("#background","#0b7204").replace("#color","#fff").replace("#text","인천");
						iconImg += iconTag.replace("#background","#efe600").replace("#color","#000").replace("#text",routeTpNm);
						//iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/9_7.png" alt="마을" />';
					}else{
						routeTpNm="일반";
//						iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />';
						iconImg = iconTag.replace("#background","#0b7204").replace("#color","#fff").replace("#text","인천");
						iconImg += iconTag.replace("#background","#0b7240").replace("#color","#fff").replace("#text",routeTpNm);
						//iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/6_1.png" alt="일반" />';
					}
				}else{//경기도
					if(routeTypeCd == 51 || routeTypeCd == 52 || routeTypeCd == 53){
						routeTpNm="공항";
						iconImg = iconTag.replace("#background","#6d6d6d").replace("#color","#fff").replace("#text",routeTpNm);
						//iconImg = '<img src="/gbis2014/images/ico/bus_type/4.png" alt="공항" />';
					}else if(routeTypeCd == 41 || routeTypeCd == 42 || routeTypeCd == 43){
						routeTpNm="시외";
						iconImg = iconTag.replace("#background","#8400ff").replace("#color","#fff").replace("#text",routeTpNm);
						//iconImg = '<img src="/gbis2014/images/ico/bus_type/3.png" alt="시외" />';
					}else if(routeTypeCd == 11 || routeTypeCd == 21 || routeTypeCd == 16){
						routeTpNm="직좌";
						iconImg = iconTag.replace("#background","#ff0000").replace("#color","#fff").replace("#text",routeTpNm);
						//iconImg = '<img src="/gbis2014/images/ico/bus_type/7_1.png" alt="직좌" />';
					}else if(routeTypeCd == 14){
						routeTpNm="광역";
						iconImg = iconTag.replace("#background","#ff0000").replace("#color","#fff").replace("#text",routeTpNm);
						//iconImg = '<img src="/gbis2014/images/ico/bus_type/7_1.png" alt="직좌" />';	
					}else if(routeTypeCd == 12 ){
						routeTpNm="좌석";
						iconImg = iconTag.replace("#background","#0000ff").replace("#color","#fff").replace("#text",routeTpNm);
						//iconImg = '<img src="/gbis2014/images/ico/bus_type/5_1.png" alt="좌석" />';
					}else if(routeTypeCd == 30){
						routeTpNm="마을";
						iconImg = iconTag.replace("#background","#efe600").replace("#color","#000").replace("#text",routeTpNm);
						//iconImg = '<img src="/gbis2014/images/ico/bus_type/9_7.png" alt="마을" />';
					}else{
						routeTpNm="일반";
//						iconImg = '';
						iconImg = iconTag.replace("#background","#0b7240").replace("#color","#fff").replace("#text",routeTpNm);
						//iconImg = '<img src="/gbis2014/images/ico/bus_type/6_1.png" alt="일반" />';
					}
				}
				
				if(stationRouteId == routeId && stationStaOrder == staOrder){					
					
					arrivalInfoStat = true; //도착예정목록에 노선정보 있음
				
					busLineDetail += '	<li style="padding:10px 10px 5px 10px;">';
					busLineDetail += '		<div class="chk"><input type="checkbox" name="'+routeId+'" title="'+routeTpNm+' '+routeName+'"></div>';
					busLineDetail += '		<a title="새 창으로 보기" href="javascript:busInfoView(\''+routeName+'\',\''+routeId+'\',\''+routeTypeCd+'\')">';
					busLineDetail += iconImg;
					busLineDetail += '		<div style="float:left;">';
					busLineDetail += '			<strong class="'+className+'" style="font-family:\'S-Core\';vertical-align:middle;font-size:15px;margin-right:10px;">'+routeName+'</strong>';					
					if(stationRouteDestName.length > 13){
						busLineDetail += '		<p>'+stationRouteDestName.substring(0,10)+'.. 방면</p>';
					}else{
						busLineDetail += '		<p>'+stationRouteDestName+' 방면</p>';
					}
					busLineDetail += '	</div></a></li>';
					
				}
			});
			
			//도착예정목록에 해당노선 없을 시 
			if(!arrivalInfoStat){
				
				var routeTypeCd = busStationInfo[i].routeTypeCd;
				var siFlag =0;
				
				if(routeTypeCd == 11 || routeTypeCd == 21 || routeTypeCd == 14 || routeTypeCd == 16){
					className = "num_red";
				}else if(routeTypeCd == 12){
					className = "num_blue";
				}else if(routeTypeCd == 30  ){
					className = "num_yellow";
				}else if(routeTypeCd == 41 || routeTypeCd == 42 || routeTypeCd == 43){
					className = "num_purple";
				}else if(routeTypeCd == 51 || routeTypeCd == 52 || routeTypeCd == 53){
					className = "num_gray";
				}else{
					className = "num_green";
				}
				
				if(siFlag == 1){ //서울
					if(routeTypeCd == 51 || routeTypeCd == 52 || routeTypeCd == 53){
						routeTpNm="공항";
						iconImg = iconTag.replace("#background","#558ed5").replace("#color","#fff").replace("#text","서울");
						iconImg += iconTag.replace("#background","#6d6d6d").replace("#color","#fff").replace("#text",routeTpNm);
						//iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/4.png" alt="공항" />';
					}else if(routeTypeCd == 41 || routeTypeCd == 42 || routeTypeCd == 43){
						routeTpNm="시외";
						iconImg = iconTag.replace("#background","#558ed5").replace("#color","#fff").replace("#text","서울");
						iconImg += iconTag.replace("#background","#8400ff").replace("#color","#fff").replace("#text",routeTpNm);
						//iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/3.png" alt="시외" />';
					}else if(routeTypeCd == 11 || routeTypeCd == 21 || routeTypeCd == 16){
						routeTpNm="직좌";
						iconImg = iconTag.replace("#background","#558ed5").replace("#color","#fff").replace("#text","서울");
						iconImg += iconTag.replace("#background","#ff0000").replace("#color","#fff").replace("#text",routeTpNm);
						//iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/7_1.png" alt="직좌" />';
					}else if(routeTypeCd == 14){
						routeTpNm="광역";
						iconImg = iconTag.replace("#background","#558ed5").replace("#color","#fff").replace("#text","서울");
						iconImg += iconTag.replace("#background","#ff0000").replace("#color","#fff").replace("#text",routeTpNm);
						//iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/7_1.png" alt="직좌" />';	
					}else if(routeTypeCd == 12 ){
						routeTpNm="좌석";
						iconImg += iconTag.replace("#background","#0000ff").replace("#color","#fff").replace("#text",routeTpNm);
						//iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/5_1.png" alt="좌석" />';
					}else if(routeTypeCd == 30){
						routeTpNm="마을";
						iconImg = iconTag.replace("#background","#558ed5").replace("#color","#fff").replace("#text","서울");
						iconImg += iconTag.replace("#background","#efe600").replace("#color","#000").replace("#text",routeTpNm);
						//iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/9_7.png" alt="마을" />';
					}else{
						routeTpNm="일반";
//						iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />';
						iconImg = iconTag.replace("#background","#558ed5").replace("#color","#fff").replace("#text","서울");
						iconImg += iconTag.replace("#background","#0b7240").replace("#color","#fff").replace("#text",routeTpNm);
						//iconImg = '<img src="/gbis2014/images/ico/bus_type/1.png" alt="서울" />&nbsp;<img src="/gbis2014/images/ico/bus_type/6_1.png" alt="일반" />';
					}
				}else if(siFlag == 3){ //인천
					if(routeTypeCd == 51 || routeTypeCd == 52 || routeTypeCd == 53){
						routeTpNm="공항";
						iconImg = iconTag.replace("#background","#0b7204").replace("#color","#fff").replace("#text","인천");
						iconImg += iconTag.replace("#background","#6d6d6d").replace("#color","#fff").replace("#text",routeTpNm);
						//iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/4.png" alt="공항" />';
					}else if(routeTypeCd == 41 || routeTypeCd == 42 || routeTypeCd == 43){
						routeTpNm="시외";
						iconImg += iconTag.replace("#background","#8400ff").replace("#color","#fff").replace("#text",routeTpNm);
						//iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/3.png" alt="시외" />';
					}else if(routeTypeCd == 11 || routeTypeCd == 21 || routeTypeCd == 16){
						routeTpNm="직좌";
						iconImg = iconTag.replace("#background","#0b7204").replace("#color","#fff").replace("#text","인천");
						iconImg += iconTag.replace("#background","#ff0000").replace("#color","#fff").replace("#text",routeTpNm);
						//iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/7_1.png" alt="직좌" />';
					}else if(routeTypeCd == 14){
						routeTpNm="광역";
						iconImg = iconTag.replace("#background","#0b7204").replace("#color","#fff").replace("#text","인천");
						iconImg += iconTag.replace("#background","#ff0000").replace("#color","#fff").replace("#text",routeTpNm);
						//iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/7_1.png" alt="직좌" />';	
					}else if(routeTypeCd == 12 ){
						routeTpNm="좌석";
						iconImg = iconTag.replace("#background","#0b7204").replace("#color","#fff").replace("#text","인천");
						iconImg += iconTag.replace("#background","#0000ff").replace("#color","#fff").replace("#text",routeTpNm);
						//iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/5_1.png" alt="좌석" />';
					}else if(routeTypeCd == 30){
						routeTpNm="마을";
						iconImg = iconTag.replace("#background","#0b7204").replace("#color","#fff").replace("#text","인천");
						iconImg += iconTag.replace("#background","#efe600").replace("#color","#000").replace("#text",routeTpNm);
						//iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/9_7.png" alt="마을" />';
					}else{
						routeTpNm="일반";
//						iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />';
						iconImg = iconTag.replace("#background","#0b7204").replace("#color","#fff").replace("#text","인천");
						iconImg += iconTag.replace("#background","#0b7240").replace("#color","#fff").replace("#text",routeTpNm);
						//iconImg = '<img src="/gbis2014/images/ico/bus_type/2.png" alt="인천" />&nbsp;<img src="/gbis2014/images/ico/bus_type/6_1.png" alt="일반" />';
					}
				}else{//경기도
					if(routeTypeCd == 51 || routeTypeCd == 52 || routeTypeCd == 53){
						routeTpNm="공항";
						iconImg = iconTag.replace("#background","#6d6d6d").replace("#color","#fff").replace("#text",routeTpNm);
						//iconImg = '<img src="/gbis2014/images/ico/bus_type/4.png" alt="공항" />';
					}else if(routeTypeCd == 41 || routeTypeCd == 42 || routeTypeCd == 43){
						routeTpNm="시외";
						iconImg = iconTag.replace("#background","#8400ff").replace("#color","#fff").replace("#text",routeTpNm);
						//iconImg = '<img src="/gbis2014/images/ico/bus_type/3.png" alt="시외" />';
					}else if(routeTypeCd == 11 || routeTypeCd == 21 || routeTypeCd == 16){
						routeTpNm="직좌";
						iconImg = iconTag.replace("#background","#ff0000").replace("#color","#fff").replace("#text",routeTpNm);
						//iconImg = '<img src="/gbis2014/images/ico/bus_type/7_1.png" alt="직좌" />';
					}else if(routeTypeCd == 14){
						routeTpNm="광역";
						iconImg = iconTag.replace("#background","#ff0000").replace("#color","#fff").replace("#text",routeTpNm);
						//iconImg = '<img src="/gbis2014/images/ico/bus_type/7_1.png" alt="직좌" />';	
					}else if(routeTypeCd == 12 ){
						routeTpNm="좌석";
						iconImg = iconTag.replace("#background","#0000ff").replace("#color","#fff").replace("#text",routeTpNm);
						//iconImg = '<img src="/gbis2014/images/ico/bus_type/5_1.png" alt="좌석" />';
					}else if(routeTypeCd == 30){
						routeTpNm="마을";
						iconImg = iconTag.replace("#background","#efe600").replace("#color","#000").replace("#text",routeTpNm);
						//iconImg = '<img src="/gbis2014/images/ico/bus_type/9_7.png" alt="마을" />';
					}else{
						routeTpNm="일반";
//						iconImg = '';
						iconImg = iconTag.replace("#background","#0b7240").replace("#color","#fff").replace("#text",routeTpNm);
						//iconImg = '<img src="/gbis2014/images/ico/bus_type/6_1.png" alt="일반" />';
					}
				}
				
				busLineDetail += '	<li style="padding:10px 10px 5px 10px;">';
				busLineDetail += '		<div class="chk"><input type="checkbox" name="'+stationRouteId+'" title="'+routeTpNm+' '+stationRouteName+'"></div>';
				busLineDetail += '		<a title="새 창으로 보기" href="javascript:busInfoView(\''+stationRouteName+'\', \''+stationRouteId+'\')">';
				busLineDetail += iconImg;
				busLineDetail += '		<div style="float:left;">';
				busLineDetail += '			<strong class="'+className+'" style="font-family:\'S-Core\';vertical-align:middle;font-size:15px;margin-right:10px;">'+routeName+'</strong>';					
				if(stationRouteDestName.length > 13){
					busLineDetail += '		<p>'+stationRouteDestName.substring(0,10)+'.. 방면</p>';
				}else{
					busLineDetail += '		<p>'+stationRouteDestName+' 방면</p>';
				}
				busLineDetail += '	</div></a></li>';
			}
		});
			
	}else{
		busLineDetail += '<div class="dtl_hd bx_station">';
		busLineDetail += '	<span class="station_tit"><strong>'+popStationStationNm+'</strong></span>';
		busLineDetail += '	<span class="station_no">'+popStationstationNo+'</span>';
		busLineDetail += '<a href="#" onclick="detailLineClose();return false" class="btn_close">닫기</a>';
		busLineDetail += '</div>';
		busLineDetail += '<ul class="list_cmn list_bus" style="height:calc(100% - 104px);">';
		busLineDetail += '	<li class="btn_multi" style="text-align:center;margin-left:0px;">';
		busLineDetail += '		<a href="javascript:detailLineGetMultiRoute()" class="view" style="float:none;width:40%;">다중노선 보기</a>';
		busLineDetail += '		<a href="javascript:resetMultiRoute()" class="reset" style="float:none;width:40%;">초기화</a>';
		busLineDetail += '	</li>';
		busLineDetail += '	<li>';
		busLineDetail += '도착 예정 정보가 없습니다.';
		busLineDetail += '	</li>';
		busLineDetail += '</ul>	';
	}
		
	$('.busLine_detail2').html(busLineDetail);
}

function detailLineClose(){
	$('.busLine_detail2').hide();
	$('.busLine_detail2').html("");
}

function detailLineGetMultiRoute(){
	
	//열려있는 툴팁 있을 시 툴팁 닫기
	if(crPopup) crPopup.hide();

	var chkBox = $(".list_bus li input:checkbox");
	var arrRouteId = [];
	var arrIndex = 0;
	multiRouteCnt = 0;
	
	if(chkBox.is(":checked")){ //체크된 노선이 있으면
		
		if($(".list_bus li input:checkbox:checked").length > 10){ // 6개 이상이면
			alert("노선비교는 10개까지만 조회 가능합니다");
		}else{
			
			for (var i = 0; i < 5; i++){
				//기존 다중노선 마커 삭제
				upRouteMarkerLayerArr[i].clearMarkers();
				downRouteMarkerLayerArr[i].clearMarkers();
				//기존 다중노선 경로 삭제
				if(up_line_layerArr[i] != null) up_line_layerArr[i].destroyFeatures();
				if(down_line_layerArr[i] != null) down_line_layerArr[i].destroyFeatures();
			}
			
			chkBox.each(function(i){
				if(this.checked){
					arrRouteId[arrIndex] = this.name;
					arrIndex++;
				}
			});
			multiRouteCntTotal = arrIndex;
			
			$.each(arrRouteId,function(i){
				
				var url = "/gbis2014/schBusAPI.action";
				var data = 'cmd=searchRouteJson';
				data += '&routeId='+arrRouteId[i];
				
				var myMessenger =new ResultToSuccess(i);
				$.ajax({
					type: "post",
					contentType: "application/x-www-form-urlencoded;charset=UTF-8",
					dataType: "json",
					url: url,
					data: data,
					success: function(data){
						myMessenger.sendToSuccess(data);
					},
					error: ajaxError,
					beforeSend: ajaxBeforeSend,
				    complete: ajaxComplete
				});
			});
		}
		
	}else{ //체크된 노선이 없으면
		alert("노선을 선택해 주세요");
	}
}

//다중노선 노선 선택 이벤트
function onClickFeature(event) {
	
	if(event.attributes.routeNm){
		alert(event.attributes.routeNm);
	}
}

//다중노선 노선 선택취소 이벤트
function onFeatureUnselect(event) {
    var feature = event.feature;
    if(feature.popup) {
        map.removePopup(feature.popup);
        feature.popup.destroy();
        delete feature.popup;
    }
}

function onPopupClose(evt) {
    select.unselectAll();
}

function changeRouteInterval(timerVal){
	stopRouteInterval();
	refreshRouteInterval = timerVal;
	runDataRefreshRoute();
}

function standByRefreshRoute(){
	getRouteDetail(routeId_c, routeNm_c, siFlag_c, routeTp_c);
}

function runDataRefreshRoute(){
	stopRouteInterval();
	routeT = setInterval("standByRefreshRoute()", refreshRouteInterval * 1000);
	
	/*
	var now = new Date(); // 현재시간
    var nowTime =now.getHours() + "시" + now.getMinutes() + "분";
    //console.log(nowTime+" 갱신");
    */
}

function stopRouteInterval(){
	clearInterval(routeT);
	routeT= "";
}

///////////////////// WA_웹접근성 ///////////////////////////////
$(document).ready(function(){
	console.log('move focus focus');
	//var list_id_i ="";
	//list_id_i = $('#list_id_0').val();
	//console.log(list_id_i);
	
});

//////////////////// 다중 노선도비교 기능추가 ////////////////////


var compareTray = document.querySelector('#compareTray');

var toDos = [];

function deleteToDo(event){
    const li = event.target.parentElement;
	li.remove();

	 for(var i = 0; i < toDos.length; i++) {
	   if(toDos[i] === li.id)  {
		   toDos.splice(i, 1);
		   i--;
	   }
	 }
}


function paintToDo(newToDoObj){
	var routeList = document.createElement("li");
	routeList.id = newToDoObj.id;
	routeList.innerText = newToDoObj.text;
	var deleteButton = document.createElement("button");
	deleteButton.className="btnDeleteList";
    deleteButton.innerText = "X";
	deleteButton.setAttribute("aria-label", "닫기");
	deleteButton.setAttribute("title", "닫기");
    routeList.appendChild(deleteButton);
	compareTray.appendChild(routeList);
	deleteButton.addEventListener("click", deleteToDo);
}

function highLight(id){
	
	
}

function handleToDoSubmit (event){
	var arrRouteId = $("#compareTray li");
	
	var mapct_middle = document.querySelector('.mapct_middle');
    if(mapct_middle.classList.contains('show')){
		var textArray = event.target.title;
        var routeId = event.target.name; 
        const newToDoObj = {
            text : textArray,
            id : routeId,
        };
        
        if(toDos.includes(newToDoObj.id)){
//        	highLight(newToDoObj.id);
        }else{
        	if(arrRouteId.length > 9){ // 6개 이상이면
    			alert("노선도 비교는 10개까지만 조회 가능합니다");
    		}else{
	        	toDos.push(newToDoObj.id);
	            paintToDo(newToDoObj);
    		}    
        }
        
	}
    
}

// 노선비교 초기화 
function resetMultiRouteDraw(){
	
	console.log('it is clicked');
	resetSearch();
	var compareTray = document.querySelector('#compareTray');
	compareTray.innerHTML='';
	toDos=[];
}



// 실시간 버스 통합

var globalUD = "";


function estimateTime(event, stationNmOrg, seq){
	
	if(event && event.preventDefault) {
		event.preventDefault();
	}
	
	var ud = "";

	if(seq*1 <= turnSequence*1){
		ud = "up";
	}else{
		ud = "down";
	}
	
	
	var popupMenu = document.querySelector('#popupMenu');
	var popupTitle = document.querySelector('#popupTitle');
	popupTitle.textContent = stationNmOrg;
	
	var target = event.currentTarget;
	var rect = target.getBoundingClientRect();
	popupMenu.style.top = (window.scrollY + rect.bottom -230) + "px";
    popupMenu.style.left = (window.scrollX + rect.left + 80) + "px";
	
	popupMenu.style.display = "block";
	
	
	const closeBtn = document.getElementById("closeBtn");
	closeBtn.onclick = function(){
		popupMenu.style.display = "none";
	};
	
	var staBtn = document.getElementById("staBtn");
	var endBtn = document.getElementById("endBtn");
	
	staBtn.onclick = function(){
		setStaStation(seq, stationNmOrg, ud);
		popupMenu.style.display = "none";
	};

	endBtn.onclick = function(){
		setEndStation(seq, stationNmOrg, ud);
		popupMenu.style.display = "none";
	};
	
}


function setStaStation(str, stationNmOrg, ud){
	
	jQuery("#departure").val(stationNmOrg);
	var departureSeq = document.getElementById("departure");
	departureSeq.setAttribute("data-seq", str);

	// 출발 정류소 선택 시 방향 고정
	if(!globalUD){
		globalUD = ud; //처음 출발 선택시 방향 저장
	}

	var startSeq = departureSeq.getAttribute("data-seq");
	var arrivalSeq = document.getElementById("destination");
	var endSeq = arrivalSeq.getAttribute("data-seq");
	
	//출발 정류소와 도착 정류소 모두 세팅됐으면 시간,거리 계산
	if(startSeq != "" && endSeq != "") {

		if(startSeq*1 >= endSeq*1){
			alert("도착 정류소보다 이전의 정류소를 선택해주세요");
			startSeq = "";
			jQuery("#departure").val("");
		}else{

			if(routeSep == 'Y' && globalUD && globalUD != ud){ // 출발도착 방향 비교
				alert("이 노선은 회차점에서 쉬어가는 노선이므로\n 상행, 하행을 분리하여 예상소요시간 정보를 제공하고 있습니다.\n 같은 상행선/하행선 안에서 출발/도착 정류소를 선택해주세요.");
				jQuery("#departure").val("");
				startSeq = "";
				departureSeq.setAttribute("data-seq", "");
				return;
			}

			calTraTime_Final(startSeq, endSeq);
		}
	}
}
function setEndStation(str, stationNmOrg, ud){

	
	jQuery("#destination").val(stationNmOrg);
	var arrivalSeq = document.getElementById("destination");
	arrivalSeq.setAttribute("data-seq", str);
	var endSeq = arrivalSeq.getAttribute("data-seq");
	
	var departureSeq = document.getElementById("departure");
	var startSeq = departureSeq.getAttribute("data-seq");
	
	//출발 정류소와 도착 정류소 모두 세팅됐으면 시간,거리 계산
	if(startSeq != "" && endSeq != "") {
		
		if(startSeq*1 >= endSeq*1){
			alert("출발 정류소보다 이후의 정류소를 선택해주세요");
			endSeq = "";
			jQuery("#destination").val("");
			arrivalSeq.setAttribute("data-seq", "");
		}else{

			if(routeSep == 'Y' && globalUD && globalUD != ud){ // 출발도착 방향 비교
				alert("이 노선은 회차점에서 쉬어가는 노선이므로\n 상행, 하행을 분리하여 예상소요시간 정보를 제공하고 있습니다.\n 같은 상행선/하행선 안에서 출발/도착 정류소를 선택해주세요.");
				jQuery("#destination").val("");
				endSeq = "";
				arrivalSeq.setAttribute("data-seq", "");
				return;
			}


			calTraTime_Final(startSeq, endSeq);
		}
	}
}


function calTraTime_Final(startSeq, endSeq){

	startSeq = parseInt(startSeq, 10);
	endSeq = parseInt(endSeq, 10);

	var totalTm = 0;
	var totalLn = 0;

	for (var i = 0; i< routeEstimate.length; i++){
		var order = parseInt(routeEstimate[i].staOrder, 10);

		if (order > startSeq && order <= endSeq){
			totalTm += parseInt(routeEstimate[i].ptts, 10);
			totalLn += parseInt(routeEstimate[i].length, 10);
		}
	}
	var totalLnKm = parseInt(totalLn/1000);
	var totalLnM = parseInt((totalLn%1000)/100);
	var totalTmHour = parseInt(totalTm/3600);
	var totalTmMin = parseInt((totalTm%3600)/60);
	var hourStr = "";
	if(totalTmHour == 0){
		hourStr = "";
	}else{
		hourStr = totalTmHour+"시간";
	}

	var objTTimeView = $('#tTimeView');

	if (totalTmMin == 0)
	{
		objTTimeView.html("<em>" + totalLnKm + "."+totalLnM+"</em>km </em>" + hourStr +  "1</em>분 이하 소요예정입니다.");
	}else{
		objTTimeView.html("<em>" + totalLnKm + "."+totalLnM+"</em>km <em>" + hourStr + " " + totalTmMin + "</em>분 소요예정입니다.");
	}
}


function resetEstiStart(){
    jQuery("#departure").val("");
	var departureSeq = document.getElementById("departure");
	departureSeq.setAttribute("data-seq", "");
	
	$('#tTimeView').html('<p class="txt" id="tTimeView">&#8251; 정류소 '+'<span class="tcr dblue"><i class="fa fa-angle-down"></i></span> <span class="tcr red"><i class="fa fa-angle-down"></i></span>'+'를 선택하시면 <strong>예상소요시간</strong>을 알려드립니다.</p>');
}
function resetEstiEnd(){
    jQuery("#destination").val("");
	var arrivalSeq = document.getElementById("destination");
	arrivalSeq.setAttribute("data-seq", "");
	
	$('#tTimeView').html('<p class="txt" id="tTimeView">&#8251; 정류소 '+'<span class="tcr dblue"><i class="fa fa-angle-down"></i></span> <span class="tcr red"><i class="fa fa-angle-down"></i></span>'+'를 선택하시면 <strong>예상소요시간</strong>을 알려드립니다.</p>');
}

function selectStation() {
	alert('정류소 목록에서 선택해주세요');
}

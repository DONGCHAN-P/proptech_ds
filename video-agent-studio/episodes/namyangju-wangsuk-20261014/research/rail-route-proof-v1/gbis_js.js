
/** 콜 */
function fnBusInfoLoad(idx){
	var bFlug = "N";
	var gubun = idx;
	jQuery("#loading").show();

	/* 
	 * highExpr : 간섭급행 
	 * attendance : 출근형급행
	 * wideExpr : 광역급행
	 * latenight : 심야
	 * loop : 경기순환
	 * lowfloor : 지상버스
	 */
	
	var url = "/gbis2014/mtrbsRoute.action";
	var data = "cmd=busRouteCategory";
	data += "&category=" + gubun;

	$.ajax({
		type: "post",
		contentType: "application/x-www-form-urlencoded;charset=UTF-8",
		dataType: "json",
		url: url,
		data: data,
		success: callbackLoad,
		async:true,
		error:function(error){
			alert("Server Error : " + error);
		}
	});
	
}

/** 콜백 */
function callbackLoad(data){
	
	var category = "";
	var filePath = "";
	var fileName = "";
	var orgFileName = "";
	
	// 실패
	if( data.success == false) {
		alert( data.result.msg );
		return;
	}
	
	// 성공
	var resultList = data.list;
	
	if(resultList.length > 0) {
		$("#filePath2").val(resultList[0].FILE_PATH);
	    $("#fileName2").val(resultList[0].FILE_NAME);
	    $("#orgFileName1").val(resultList[0].ORGFILE_NAME);
		filePath = resultList[0].FILE_PATH;
		fileName = resultList[0].FILE_NAME;
		orgFileName = resultList[0].ORGFILE_NAME;
	    category = resultList[0].CATEGORY;
	    
	    excelList(filePath, fileName, orgFileName, category);
	}else {
		$("#filePath2").val("");
		$("#fileName2").val("");
		$("#orgFileName1").val("");
	}
	
	
}

//엑셀읽어서 화면 뿌리기
function excelList(path, name, origin, cate) {
	
	var filePath = path;
	var fileName = name;
	var orgFileName = origin;
	var cid = cate;
	
	var url = "/gbis2014/mtrbsRoute.action?cmd=busRouteList";
	var data = {filePath : filePath, fileName : fileName, orgFileName : orgFileName};
	
	$.ajax({
			url: url,
			type: "post",
			contentType: "application/x-www-form-urlencoded;charset=UTF-8",
			dataType: "json",
			data: data,
			success:function(data, textStatus){
				var html = "";
				var arrayAreaTemp = new Array();
				var arrayTemp = new Array();
				var cnTemp = new Array();
				var arrayNum = "";
				var tempNanme = "";
				var cnt = 0;
				
				html += "<colgroup>";
				if(cid == "highExpr")			// 간섭급행버스
				{
					html += "<col width=\"9%\" />"; 
					html += "<col width=\"11%\" />";
					html += "<col width=\"8%\" />";
					html += "<col width=\"8%\" />";
					html += "<col />";
					html += "<col width=\"8%\" />";
					html += "<col width=\"8%\" />";
					html += "<col width=\"8%\" />";
					html += "<col width=\"9%\" />";
				}
				else if(cid == "attendance")		// 출근형급행버스
				{
					html += "<col width=\"8%\" />"; 
					html += "<col width=\"8%\" />";
					html += "<col width=\"10%\" />";
					html += "<col />";
					html += "<col width=\"8%\" />";
					html += "<col width=\"8%\" />";
					html += "<col width=\"8%\" />";
					html += "<col width=\"9%\" />";
					html += "<col width=\"13%\" />";
				}
				else if(cid == "wideExpr")	// 광역급행버스
				{
					html += "<col width=\"8%\" />"; 
					html += "<col width=\"9%\" />";
					html += "<col width=\"8%\" />";
					html += "<col width=\"10%\" />";
					html += "<col />";
					html += "<col width=\"8%\" />";
					html += "<col width=\"8%\" />";
					html += "<col width=\"8%\" />";
				}
				else if(cid == "latenight")		// 심야버스
				{
					html += "<col width=\"8%\" />"; 
					html += "<col width=\"9%\" />";
					html += "<col width=\"8%\" />";
					html += "<col width=\"10%\" />";
					html += "<col />";
					html += "<col width=\"8%\" />";
					html += "<col width=\"8%\" />";
					html += "<col width=\"8%\" />";
				}
				else if(cid == "loop")			// 경기순환버스
				{
					html += "<col width=\"9%\" />"; 
					html += "<col width=\"7%\" />";
					html += "<col width=\"4%\" />";
					html += "<col width=\"10%\" />";
					html += "<col width=\"14%\" />";
				}
				else if(cid == "lowfloor")		// 지상버스
				{
					html += "<col width=\"10%\" />"; 
					html += "<col width=\"10%\" />";
					html += "<col width=\"10%\" />";
					html += "<col width=\"20%\"/>";
					html += "<col />";
					html += "<col width=\"10%\" />";
					html += "<col width=\"10%\" />";
					html += "<col width=\"10%\" />";
				}
				html += "</colgroup>";
				
				html +="<thead>";
				html += "<th scope=\"col\" abbr=\"" + data.area[1].areaTemp+"\">"+data.area[1].areaTemp + "</th>";
				html += "<th scope=\"col\" abbr=\"" + data.office[0].areaTemp+"\">"+data.office[0].areaTemp + "</th>";
				html += "<th scope=\"col\" abbr=\"" + data.routenum[0].areaTemp+"\">"+data.routenum[0].areaTemp + "</th>";
				html += "<th scope=\"col\" abbr=\"" + data.spoint[0].areaTemp+"\">"+data.spoint[0].areaTemp + "</th>";
				html += "<th scope=\"col\" abbr=\"" + data.routestation[0].areaTemp+"\">"+data.routestation[0].areaTemp + "</th>";
				if(data.epoint != "")
				{
					if(data.epoint[0].areaTemp != "routeId")
					{
						html += "<th scope=\"col\" abbr=\"" + data.epoint[0].areaTemp+"\">"+data.epoint[0].areaTemp + "</th>";
					}
					
				}
				if(data.distance != null) 
				{
					if(data.distance[0].areaTemp != "routeId")
					{
						html += "<th scope=\"col\" abbr=\"" + data.distance[0].areaTemp+"\">"+data.distance[0].areaTemp + "</th>";
					}
					
				}
				if(data.runalgebra != null)
				{
					if(data.runalgebra[0].areaTemp != "routeId")
					{
						html += "<th scope=\"col\" abbr=\"" + data.runalgebra[0].areaTemp+"\">"+data.runalgebra[0].areaTemp + "</th>";
					}
					
				}
				if(data.runnumber != null)
				{
					if(data.runnumber[0].areaTemp != "routeId")
					{
						html += "<th scope=\"col\" abbr=\"" + data.runnumber[0].areaTemp+"\">"+data.runnumber[0].areaTemp + "</th>";
					}
					
				}
				html +="</thead>";
				
				//1번 셀 병합 이름과 갯수 추출
				for(var i = 0; i < data.area.length; i++)
				{
					arrayTemp[i] = data.area[i].cntTemp;
					arrayAreaTemp[i] = data.area[i].areaTemp;
				}
				
				html +="<tbody>";
				
				for(var i=1; i < data.office.length; i++)
				{
					html += "<tr>";

					arrayNum = arrayAreaTemp.indexOf(data.office[i].upareaTemp);

					if(cnt == 0)
					{
						cnTemp = excelView(data, arrayNum).split(",");

						cnt = parseInt(cnTemp[1])+1;
						tempNanme = cnTemp[0];

						html += "<td class=\"bg\"  rowspan=\""+cnt+"\">" + data.area[arrayNum].areaTemp + "</td>";
					}
					else
					{
						cnTemp = excelView(data, arrayNum).split(",");
						
						if(cnt != (parseInt(cnTemp[1])+1) )
						{
							cnt = parseInt(cnTemp[1])+1;
							tempNanme = cnTemp[0];
							
							html += "<td rowspan=\""+cnt+"\">" + data.area[arrayNum].areaTemp + "</td>";
						}
						else if(cnTemp[0] != tempNanme && cnt == (parseInt(cnTemp[1])+1))
						{
							cnt = parseInt(cnTemp[1])+1;
							tempNanme = cnTemp[0];
							
							html += "<td rowspan=\""+cnt+"\">" + data.area[arrayNum].areaTemp + "</td>";
						}
					}
					
					if(cid == "highExpr")			// 간섭급행버스
					{
						html +="<td>" + data.office[i].areaTemp							+ "</td>";
						
						var tempSplit = data.routenum[i].areaTemp.split("-");
						
						if(tempSplit[1] == null) {
							html +="<td><a title=\"새 창으로 보기\" href=\"javascript:execlBusInfoView(\'" + parseInt(data.routenum[i].areaTemp) + "\','" + data.routeId[i].areaTemp +"\')\" class=\"red\">" + parseInt(data.routenum[i].areaTemp) + "</a></td>";
						}else {
							html +="<td><a title=\"새 창으로 보기\" href=\"javascript:execlBusInfoView(\'" + data.routenum[i].areaTemp  + "\','" + data.routeId[i].areaTemp + "\')\" class=\"red\">" + data.routenum[i].areaTemp  + "</a></td>";
						}
						
						html +="<td>" + data.spoint[i].areaTemp							+ "</td>";
						html +="<td>" + data.routestation[i].areaTemp				    + "</td>";
						html +="<td>" + data.epoint[i].areaTemp						    + "</td>";
						html +="<td>" + parseInt(data.distance[i].areaTemp)				+ "</td>";
						html +="<td>" + parseInt(data.runalgebra[i].areaTemp)			+ "</td>";
						html +="<td>" + parseInt(data.runnumber[i].areaTemp)			+ "</td>";
					}
					else if(cid == "attendance")		// 출근형급행버스
					{
						html +="<td>" + data.office[i].areaTemp 						  + "</td>";
						
						var tempSplit = data.routenum[i].areaTemp.split("-");
						
						if(tempSplit[1] == null) {
							html +="<td><a title=\"새 창으로 보기\" href=\"javascript:execlBusInfoView(\'" + parseInt(data.routenum[i].areaTemp) + "\','" + data.routeId[i].areaTemp + "\')\" class=\"red\">" + parseInt(data.routenum[i].areaTemp) + "</a></td>";
						}else {
							html +="<td><a title=\"새 창으로 보기\" href=\"javascript:execlBusInfoView(\'" + data.routenum[i].areaTemp  + "\','" + data.routeId[i].areaTemp + "\')\" class=\"red\">" + data.routenum[i].areaTemp + "</a></td>";
						}
						
						html +="<td>" + data.spoint[i].areaTemp							  + "</td>";
						html +="<td>" + data.routestation[i].areaTemp					  + "</td>";
						html +="<td>" + data.epoint[i].areaTemp							  + "</td>";
						html +="<td>" + parseInt(data.distance[i].areaTemp)				  + "</td>";
						html +="<td>" + parseInt(data.runalgebra[i].areaTemp)			  + "</td>";
						html += "<td>";
						var attendanceSeq = 1;
						for(var j=1; j < data.runnumber.length;j++)
						{
							if(data.routenum[i].routeTemp == data.runnumber[j].routeTemp)
							{
								if(attendanceSeq == 1){
									html += "<table align=\"center\">";
								}else{
									html += "<table align=\"center\" style='border-top:1px solid #d9d9d9;'>";
								}
								html += "<tr>";
								html +="<td align=\"center\" style='border-top:none;'>" + data.runnumber[j].areaTemp + "</td>";
								html += "</tr>";
								html += "</table>";
								
								attendanceSeq++;
							}
						}
						html += "</td>";
					}
					else if(cid == "wideExpr")	// 광역급행버스
					{
						html +="<td>" + data.office[i].areaTemp 				+ "</td>";	
						html +="<td><a title=\"새 창으로 보기\" href=\"javascript:execlBusInfoView(\'" + data.routenum[i].areaTemp + "\','" + data.runnumber[i].areaTemp  + "\')\" class=\"red\">" + data.routenum[i].areaTemp + "</a></td>";
						html +="<td>" + data.spoint[i].areaTemp					+ "</td>";
						html +="<td>" + data.routestation[i].areaTemp			+ "</td>";
						html +="<td>" + data.epoint[i].areaTemp					+ "</td>";
						html +="<td>" + parseInt(data.distance[i].areaTemp)		+ "</td>";
						html +="<td>" + parseInt(data.runalgebra[i].areaTemp)	+ "</td>";
					}
					else if(cid == "latenight")		// 심야버스
					{
						html +="<td>"+data.office[i].areaTemp+"</td>";
						
						var tempSplit = data.routenum[i].areaTemp.split("-");
						
						if(tempSplit[1] == null) {
							html +="<td><a title=\"새 창으로 보기\" href=\"javascript:execlBusInfoView(\'" + parseInt(data.routenum[i].areaTemp) + "\','" + parseInt(data.routeId[i].areaTemp) + "\')\" class=\"red\">" + parseInt(data.routenum[i].areaTemp) + "</a></td>";
						}else {
							html +="<td><a title=\"새 창으로 보기\" href=\"javascript:execlBusInfoView(\'" + data.routenum[i].areaTemp + "\','" + data.routeId[i].areaTemp + "\')\" class=\"red\">" + data.routenum[i].areaTemp + "</a></td>";
						}
						
						html +="<td>" + data.spoint[i].areaTemp 			  + "</td>";
						html +="<td>" + data.routestation[i].areaTemp 		  + "</td>";
						html +="<td>" + data.epoint[i].areaTemp 			  + "</td>";
						html +="<td>" + data.distance[i].areaTemp 			  + "</td>";
						html +="<td>" + parseInt(data.runalgebra[i].areaTemp) + "</td>";
						html +="<td>" + data.runnumber[i].areaTemp			  + "</td>";
					}
					else if(cid == "loop")			// 경기순환버스
					{
						html +="<td><a title=\"새 창으로 보기\" href=\"javascript:execlBusInfoView(\'" + parseInt(data.office[i].areaTemp)+ "\','" + data.epoint[i].areaTemp + "\')\" target=\"_blank\"  class=\"red\">" + parseInt(data.office[i].areaTemp) + "</a></td>";
						html +="<td>" + parseInt(data.routenum[i].areaTemp) + "</td>";
						html +="<td>" + data.spoint[i].areaTemp + "</td>";
						html += "<td>";
						var loopSeq = 1;
						for(var j=1; j < data.routestation.length; j++)
						{
							if(data.routenum[i].upareaTemp == data.routestation[j].upareaTemp)
							{
								if(loopSeq == 1){
									html += "<table>";
								}else{
									html += "<table style='border-top:1px solid #d9d9d9;'>";
								}
								html += "<tr>";
								html +="<td style='border-top:none;'>" + data.routestation[j].areaTemp + "</td>";
								html += "</tr>";
								html += "</table>";
								loopSeq++;
						
							}
						}
						html += "</td>";
					}
					else if(cid == "lowfloor")		// 저상버스
					{
						html +="<td>" + data.office[i].areaTemp				 + "</td>";
						
						var tempSplit = data.routenum[i].areaTemp.split("-");
						
						if(tempSplit[1] == null) {
							html +="<td><a title=\"새 창으로 보기\" href=\"javascript:execlBusInfoView(\'"+ parseInt(data.runalgebra[i].areaTemp)+ "\','" + parseInt(data.runnumber[i].areaTemp) +"\')\" class=\"red\">" + parseInt(data.routenum[i].areaTemp)  + "</a></td>";
						}else {
							html +="<td><a title=\"새 창으로 보기\" href=\"javascript:execlBusInfoView(\'"+ data.runalgebra[i].areaTemp + "\','" + data.runnumber[i].areaTemp +"\')\" class=\"red\">" + data.routenum[i].areaTemp  + "</a></td>";
						}
						html +="<td>" + data.spoint[i].areaTemp				 + "</td>";
						html +="<td>" + data.routestation[i].areaTemp		 + "</td>";
						html +="<td>" + data.epoint[i].areaTemp				 + "</td>";
						html +="<td>" + data.distance[i].areaTemp  + "</td>";
						html +="<td>" + parseInt(data.runalgebra[i].areaTemp)+ "</td>";
						html += "<td>";
					}
					html += "</tr>";
				}
				html +="</tbody>";
				
				jQuery("#list_sty01").html(html);
			}
	});
	
	jQuery("#loading").hide();
}

function excelView(obj, num)
{
	var cnt = 0;
	var arrayTemp = "";
	
	for(var i=1; i < obj.office.length; i++)
	{
		if(obj.area[num].areaTemp == obj.office[i].upareaTemp)
		{
			arrayTemp = obj.area[num].areaTemp +","+ cnt++;
		}
	}
	return arrayTemp;
}



/** 버스 상세 맵 뷰 이동 - 엑셀파일 */
function execlBusInfoView(busNum,routeId){
	var excelBusInfo = "excelBusInfo";
	var url = "/gbis2014/schBus.action?cmd=mainSearchText";
	var data = "&gubun=" + excelBusInfo + "&searchText=" + busNum + "&routeId=" + routeId;

	window.open(url+data,"_blank");
}

/** 버스 상세 맵 뷰 이동 */
function busInfoView(busNum, routeId){
	var busInfo = "busInfo";
	var url = "/gbis2014/schBus.action?cmd=mainSearchText";
	var data = "&gubun=" + busInfo + "&searchText=" + busNum + "&routeId=" + routeId;

	window.open(url+data,"_blank");
}

/** 통합검색 정류소 이동 */
function busStationView(stationId, stationNm){
	var url = "/gbis2014/schBus.action?cmd=mainSearchText";
	
	var substrStationNm = stationNm.substring(stationNm.length-3, stationNm.length); 
	
	if( substrStationNm != "..."){
		var data = "&searchText=" + stationNm;
	} else {
		var data = "&searchText=" + stationNm.substring(0,stationNm.length-3);
	}
	
	window.open(url+data,"_blank");
}




/*
 * @(#)searchBoard.js 1.0 2015/06/15
 * 
 * COPYRIGHT (C) 2013 WISEITECH CO., LTD. ALL RIGHTS RESERVED.
 */

/**
 * 일반 게시판 내용을 검색하는 스크립트이다.
 *
 * @author 김은삼
 * @version 1.0 2015/06/15
 */
$(function() {
    // 컴포넌트를 초기화한다.
    initComp();
    
    // 마스크를 바인딩한다.
    bindMask();
    
    // 이벤트를 바인딩한다.
    bindEvent();
    
    // 옵션을 로드한다.
    loadOptions();
    
    // 데이터를 로드한다.
    loadData();
    
    // GNB메뉴 바인딩한다.
	if (window.location.href.indexOf("statdata")> -1) {
		menuOn(1, 8);
	}  else if (window.location.href.indexOf("pres")> -1) {
		menuOn(3, 1);
	} else if (window.location.href.indexOf("rpt")> -1) {
		menuOn(3, 2);
	} else if (window.location.href.indexOf("resr")> -1) {
		menuOn(3, 3);
	} else if (window.location.href.indexOf("housdata")> -1) {
		menuOn(3, 3);
	}
	
});

////////////////////////////////////////////////////////////////////////////////
// 글로벌 변수
////////////////////////////////////////////////////////////////////////////////
/**
 * 템플릿
 */
var templates = {
    // 일반 게시판
    general:{
        data:
        	"<tr>"                                                              +
            "<td class=\"number rowNum\"></td>"                                +
            "<td class=\"listSubNm\">"                                        +
            "<td class=\"title left\">"                                        +
	            "<a href=\"#\" class=\"bbsTit\"></a>"                          +
	            "<ul class=\"mobile-info\">"                                   +
	            "<li class=\"userDttm\"></li>"                                 +
	            "<li class=\"none viewCnt\"></li>"                             +
	            "</ul>"                                                        +
	        "</td>"                                                            +
	        "<td class=\"file fileCnt\"></span></td>"                          +
            "<td class=\"date userDttm\"></td>"                                +
            "<td class=\"hit viewCnt\"></td>"                                  +
        "</tr>",
        data2:
                	"<tr>"                                                              +
                    "<td class=\"number rowNum\"></td>"                                +
                    "<td class=\"title left\">"                                        +
        	            "<a href=\"#\" class=\"bbsTit\"></a>"                          +
        	            "<ul class=\"mobile-info\">"                                   +
        	            "<li class=\"userDttm\"></li>"                                 +
        	            "<li class=\"none viewCnt\"></li>"                             +
        	            "</ul>"                                                        +
        	        "</td>"                                                            +
        	        "<td class=\"file fileCnt\"></span></td>"                          +
                    "<td class=\"date userDttm\"></td>"                                +
                    "<td class=\"hit viewCnt\"></td>"                                  +
                "</tr>",
        none:
	        "<tr>"                                                             +
	            "<td colspan=\"6\" class=\"noData\">해당 자료가 없습니다.</td>"+
	        "</tr>"
    },
    // 댓글 게시판
    comment:{
        data:
            "<tr>"                                                                                                                                               +
                "<td><span class=\"mq_tablet rowNum\"></span></td>"                                                                                              +
                "<td class=\"area_tit\">"                                                                                                                        +
                    "<a href=\"#\" class=\"link tit ellipsis w_400 bbsTit\"></a>"                                                                                +
                    "<strong class=\"btn_detail mq_mobile\"><a href=\"#\">상세보기</a></strong>"                                                                 +
                "</td>"                                                                                                                                          +
                "<td><span class=\"writer userNm\"></span></td>"                                                                                                 +
                "<td><span class=\"date userDttm\"></span></td>"                                                                                                 +
                "<td><span class=\"mq_tablet viewCnt\"></span></td>"                                                                                             +
                "<td><span class=\"reply ansCnt\"><img src=\"" + com.wise.help.url("/img/ggportal/desktop/common/icon_reply.png") + "\" alt=\"\" /></span></td>" +
            "</tr>",
        none:
            "<tr>"                                                              +
                "<td colspan=\"6\" class=\"noData\">해당 자료가 없습니다.</td>" +
            "</tr>"
    }
};

var listSubFirst = 0;
////////////////////////////////////////////////////////////////////////////////
// 초기화 함수
////////////////////////////////////////////////////////////////////////////////
/**
 * 컴포넌트를 초기화한다.
 */
function initComp() {
    var code = $("#board-search-form [name=listSubCd]").val();
    $(".board-section-tab[href='#" + code + "']").addClass("on");
    
    $("#board-searchtype-combo").val($("#board-search-form [name=searchType]").val());
    $("#board-searchword-field").val($("#board-search-form [name=searchWord]").val());
}

/**
 * 마스크를 바인딩한다.
 */
function bindMask() {
    // Nothing to do.
}

/**
 * 이벤트를 바인딩한다.
 */
function bindEvent() {
    $(".board-insert-button").each(function(index, element) {
        // 일반 게시판 내용 작성 버튼에 클릭 이벤트를 바인딩한다.
        $(this).bind("click", function(event) {
            // 일반 게시판 내용을 등록한다.
            insertBoard();
            return false;
        });
        
        // 일반 게시판 내용 작성 버튼에 키다운 이벤트를 바인딩한다.
        $(this).bind("keydown", function(event) {
            if (event.which == 13) {
                // 일반 게시판 내용을 등록한다.
                insertBoard();
                return false;
            }
        });
    });
    
    $(".board-section-tab").each(function(index, element) {
        // 일반 게시판 내용 섹션 탭에 클릭 이벤트를 바인딩한다.
        $(this).bind("click", function(event) {
            // 일반 게시판 내용 섹션을 변경한다.
            changeBoardSection(this);
            return false;
        });
        
        // 일반 게시판 내용 섹션 탭에 키다운 이벤트를 바인딩한다.
        $(this).bind("keydown", function(event) {
            if (event.which == 13) {
                // 일반 게시판 내용 섹션을 변경한다.
                changeBoardSection(this);
                return false;
            }
        });
    });
    
    // 일반 게시판 검색어 필드에 키다운 이벤트를 바인딩한다.
    $("#board-searchword-field").bind("keydown", function(event) {
        if (event.which == 13) {
            // 일반 게시판 검색어를 변경한다.
            changeBoardSearchWord();
            return false;
        }
    });
    
    // 일반 게시판 검색 버튼에 클릭 이벤트를 바인딩한다.
    $("#board-search-button").bind("click", function(event) {
        // 일반 게시판 검색어를 변경한다.
        changeBoardSearchWord();
        return false;
    });
    
    // 일반 게시판 검색 버튼에 키다운 이벤트를 바인딩한다.
    $("#board-search-button").bind("keydown", function(event) {
        if (event.which == 13) {
            // 일반 게시판 검색어를 변경한다.
            changeBoardSearchWord();
            return false;
        }
    });
    
    // 통계뉴스 게시판 분류 combobox change 이벤트를 바인딩한다.
   /* $("#listSubCd").bind('change', function () {
        $("#board-search-form [name=listSubCd]").val($("#listSubCd").val());
    });*/
    
    $("#tab-area li a").bind("click", function(event) {
    	$("#tab-area li a").removeClass("on");
    	$(this).addClass("on");
    	$("#board-search-form [name=listSubCd]").val($(this).attr("data-id"));
    	// 일반 게시판 내용을 검색한다.
        searchBoard();
        
    	return false;
    });
    
    $("#list-menu-select").on("change", function() { 
        var selectedValue = $(this).val();
        
        // 모든 요소의 클래스를 제거합니다.
        //$(".left_tab ul li a").removeClass("selected");
        
        // 선택한 값을 가진 요소에 selected 클래스를 추가합니다.
        //$(".left_tab ul li a[data-id='" + selectedValue + "']").addClass("selected");
        
        // 선택한 값을 listSubCd 필드에 설정합니다.
        $("#board-search-form [name=listSubCd]").val(selectedValue);
        
        // 검색을 실행합니다.
        searchBoard();
        
        return false;
    });
    
    
}

/**
 * 옵션을 로드한다.
 */
function loadOptions() {
    // Nothing do do.
}

/**
 * 데이터를 로드한다.
 */
function loadData() {
    // 일반 게시판 내용을 검색한다.
    searchBoard($("#board-search-form [name=page]").val());
}

////////////////////////////////////////////////////////////////////////////////
// 서비스 함수
////////////////////////////////////////////////////////////////////////////////
/**
 * 일반 게시판 내용을 검색한다.
 * 
 * @param page {String} 페이지 번호
 */
function searchBoard(page) {
    // 데이터를 검색한다.
    doSearch({
        url:resolveUrl("/searchBulletin.do"),
        page:page ? page : "1",
        before:beforeSearchBoard,
        after:afterSearchBoard,
        pager:"board-pager-sect",
        counter:{
            count:"board-count-sect",
            pages:"board-pages-sect"
        }
    });
}

/**
 * 일반 게시판 내용을 조회한다.
 * 
 * @param data {Object} 데이터
 */
function selectBoard(data) {
    // if (!verifyWriter(data.lockTag, "board-search-form", selectBoard, data)) {
    //     return;
    // }

    var url = resolveUrl("/selectBulletinPage.do");
   
     
    // 데이터를 조회하는 화면으로 이동한다.
    goSelect({
        url:url,
        form:"board-search-form",
        data:[{
            name:"bbsCd",
            value:data.bbsCd
        }, {
            name:"seq",
            value:data.seq
        }, {
            name:"noticeYn",
            value:data.noticeYn
        }]
    });
}

/**
 * 일반 게시판 내용을 등록한다.
 */
function insertBoard() {
    // 데이터를 등록하는 화면으로 이동한다.
    goInsert({
        url:resolveUrl("/insertBulletinPage.do"),
        form:"board-search-form",
        data:[{
            name:"seq",
            value:""
        }]
    });
}

/**
 * 일반 게시판 내용 섹션을 변경한다.
 * 
 * @param tab {Element} 탭
 */
function changeBoardSection(tab) {
    if (!$(tab).hasClass("on")) {
        $(".board-section-tab.on").removeClass("on");
        
        $(tab).addClass("on");
    }
    
    var code = $(tab).attr("href").substring(1);
    
    $("#board-search-form [name=listSubCd]").val(code);
    
    // 일반 게시판 내용을 검색한다.
    searchBoard();
}

/**
 * 일반 게시판 검색어를 변경한다.
 */
function changeBoardSearchWord() {
    $("#board-search-form [name=searchType]").val($("#board-searchtype-combo").val());
    $("#board-search-form [name=searchWord]").val($("#board-searchword-field").val());
    
    // 일반 게시판 내용을 검색한다.
    searchBoard();
}

/**
 * URL을 반환한다.
 * 
 * @param url {String} URL
 */
function resolveUrl(url) {
    var matches = window.location.href.match(/\/portal\/[^\/]+\//);
    
    return matches[0] + $("#board-search-form [name=bbsCd]").val().toLowerCase() + url;
}

////////////////////////////////////////////////////////////////////////////////
// 전처리 함수
////////////////////////////////////////////////////////////////////////////////
/**
 *  일반 게시판 내용 검색 전처리를 실행한다.
 * 
 * @param options {Object} 옵션
 * @returns {Object} 데이터
 */
function beforeSearchBoard(options) {
    var data = {
        // Nothing do do.
    };
    
    var form = $("#board-search-form");
    
    if (com.wise.util.isBlank(options.page)) {
        form.find("[name=page]").val("1");
    }
    else {
        form.find("[name=page]").val(options.page);
    }
    
    $.each(form.serializeArray(), function(index, element) {
        switch (element.name) {
            case "seq":
            case "noticeYn":
                break;
            default:
                data[element.name] = element.value;
                break;
        }
    });
    
    if (com.wise.util.isBlank(data.bbsCd)) {
        return null;
    }
    
    return data;
}

// 통계뉴스용 popup 호출 처리
function pressOpenWin(url) {

    if ( com.wise.util.isBlank(url) ||  com.wise.util.isNull(url) ) {
        alert("요청하신 페이지 정보가 없습니다.");
        return;
    } 

    window.open(url);
}

////////////////////////////////////////////////////////////////////////////////
// 후처리 함수
////////////////////////////////////////////////////////////////////////////////
/**
 * 일반 게시판 내용 검색 후처리를 실행한다.
 * 
 * @param data {Array} 데이터
 */
function afterSearchBoard(data) {
    var table = $("#board-data-table");
    
    table.find("tr").each(function(index, element) {
        if (index > 0) {
            $(this).remove();
        }
    });
    var bbsCd = $("input[name=bbsCd]").val();
    var template = "";
    template = table.find("th.comment").length > 0 ? templates.comment : templates.general;

    for (var i = 0; i < data.length; i++) {
        var row = $("#board-search-form [name=grpCd]").val() != "" ? $(template.data) : $(template.data2) ;
        
        if (data[i].noticeYn == "Y") {
            row.addClass("notice");
            
            row.find(".rowNum").html("<span class=\"icon notice\">공지</span>");
        }
        else {
            row.find(".rowNum").text(getRowNumber($("#board-count-sect").text(), "" + data[i].rowNum));
        }

        row.find(".listSubNm").text(data[i].listSubNm);
        
        row.find(".bbsTit").text(data[i].bbsTit);
        
        // if (data[i].secretYn == "Y") {
        //     row.find(".bbsTit").prepend("<img src=\"" + com.wise.help.url("/img/ggportal/desktop/common/icon_lock.png") + "\" alt=\"\" title=\"비밀글 아이콘\" /> ");
        // }
        
        if (data[i].newYn == "Y") {
        	row.find(".bbsTit").prepend("<img src=\"" + com.wise.help.url("/images/rone/portal/icon_new@2x.png") + "\" alt=\"새글\" class=\"board-icon mobile\"/> ");
        }
        
        if (data[i].viewCnt >= data[i].hlCnt) {
            row.find(".bbsTit").addClass("best");
        }
        
       // row.find(".regUserNm").text(data[i].userNm);
        row.find(".userDttm").text(data[i].userDttm);
        
        if (data[i].fileCnt) {
            row.find(".fileCnt").append("<img src=\"" + com.wise.help.url("/images/rone/portal/icon_file@2x.png") + "\" alt=\"파일\" class=\"board-icon mobile\"/>");
        }
        
        row.find(".viewCnt").text(com.wise.util.toCurrency(data[i].viewCnt.toString()));
        row.find(".ansCnt").append(com.wise.util.toCurrency(data[i].ansCnt.toString()));
        
        row.find("a").each(function(index, element) {
            // 일반 게시판 내용 제목 링크에 클릭 이벤트를 바인딩한다.
            $(this).bind("click", {
                bbsCd:data[i].bbsCd,
                seq:data[i].seq,
                noticeYn:data[i].noticeYn,
                lockTag:data[i].lockTag,
                url:data[i].url
            }, function(event) {
                // 일반 게시판 내용을 조회한다.
                selectBoard(event.data);
                return false;
            });
            
            
            // 일반 게시판 내용 제목 링크에 키다운 이벤트를 바인딩한다.
            $(this).bind("keydown", {
                bbsCd:data[i].bbsCd,
                seq:data[i].seq,
                noticeYn:data[i].noticeYn,
                lockTag:data[i].lockTag,
                url:data[i].url
            }, function(event) {
                if (event.which == 13) {
                    // 일반 게시판 내용을 조회한다.
                    selectBoard(event.data);
                    return false;
                }
            });
        });
        
        table.append(row);
    }
    
    if (data.length == 0) {
        var row = $(template.none);
        
        table.append(row);
    }
    
    // 메인에서 호출시 탭 이벤트
    var listSubCd = $("#board-search-form input[name='listSubCd']").val();
	if (!com.wise.util.isBlank(listSubCd) && listSubFirst == 0) {
	     //$(".left_tab ul li a").removeClass("selected");
	     //$('.left_tab ul li a[data-id="' + listSubCd + '"]').addClass("selected");
	     
	     $("#list-menu-select").val(listSubCd).prop("selected", true);
	     
	     listSubFirst++;
	}
}

////////////////////////////////////////////////////////////////////////////////
// 이벤트 함수
////////////////////////////////////////////////////////////////////////////////
/**
 * 탭이 레프트메뉴로 표시된경우 레프트메뉴 게시판 조회 이벤트
 * @param index 메뉴 위치(순서)
 */
function tabSearchBoard(index) {
    $(".left_tab ul li a").removeClass("selected");
    var $li = $(".left_tab ul li").eq(index);
    $li.find("a").addClass("selected");
    $("#board-search-form [name=listSubCd]").val($li.find("a").attr("data-id"));
    
    $("#list-menu-select").val($li.find("a").attr("data-id")).prop("selected", true);
    searchBoard();
}
$(document).ready(function () {
    // Create link when clicking on share button
    $('.create-shareable-link').on('click', function () {
        let url = window.location.href;
        $('#shareable-link').html('<a href="' + url + '">' + url + '</a>');
    });
    $('#copybutton').click(function () {
        var $temp = $("<input>");
        $("body").append($temp);
        $temp.val($('#shareable-link').text()).select();
        document.execCommand("copy");
        $temp.remove();
    });

//function for toggling conferences
    $(":checkbox").change(function () {
        let checkboxes;
        if ($(this).is($('.toggle-all'))) {
            if ($(this).prop("checked") === true) {
                checkboxes = $(this).closest('ul').find(':checkbox');
                checkboxes.prop('checked', $(this).is(':checked'));
            } else {
                checkboxes = $(this).closest('ul').find(':checkbox');
                checkboxes.prop('checked', false);
            }
        } else if ($(this).is($('.toggle-domain'))) {
            function toggleConferences(val, check) {
                $(":checkbox").filter(function () {
                    return $(this).attr("class") === val;
                }).prop("checked", check);
            }

            if ($(this).prop("checked") === true) {
                toggleConferences($(this).val(), true);
            } else {
                toggleConferences($(this).val(), false);
            }
        }
        if ($(this).is(":checked")) {
            var isAllChecked = 0;

            $("." + $(this).attr("class")).each(function () {
                if (!this.checked)
                    isAllChecked = 1;
            });

            if (isAllChecked == 0) {
                $("#" + $(this).attr("class")).prop("checked", true);
                $(".toggle-all").prop("checked", true);

            }
        } else {
            $("#" + $(this).attr("class")).prop("checked", false);
            $(".toggle-all").prop("checked", false);
        }
        window.location.href = getUrl();
    });

//change page
    $('.page-link').on('click', function () {
        let currentPageNr
        let params = new URLSearchParams(window.location.search)
        if (params.has('page')) {
            currentPageNr = parseInt(params.get('page'));
        } else {
            currentPageNr = 1
        }
        let page = $.trim($(this).text());

        let pageNr;
        let maxPages = $("a:contains('»')").attr("value");
        if (page === "«") {
            pageNr = 1;
        } else if (page === "‹") {
            if (currentPageNr !== 1)
                pageNr = currentPageNr - 1;
        } else if (page === "›") {
            pageNr = currentPageNr + 1;

        } else if (page === "»") {
            pageNr = maxPages;

        } else {
            pageNr = parseInt(page)
        }
        $('#page').val(pageNr);
        window.location.href = getUrl();

    })

//function for setting the location and timespan
    $('select').on('change', function () {
        window.location.href = getUrl();
    });

//function for ordering
    $('i').filter(function () {
        let elementClass = $(this).attr("class");
        if (elementClass === ("fa fa-fw fa-sort") || elementClass === ("fa fa-fw fa-sort-asc") || elementClass === ("fa fa-fw fa-sort-desc")) {
            return true;
        } else return false;
    }).on('click', function () {
        function setOrderByValue(element, orderdirection) {
            let compare = element.parent().text();
            let order_direction, orderby;
            if (compare.includes("Name ")) {
                orderby = "name";
            } else if (compare.includes("current Publications ")) {
                orderby = "pubs"
            } else if (compare.includes("all AI-Ranking Publications ")) {
                orderby = "total_pubs"
            } else if (compare.includes("selected ")) {
                orderby = "h_index"
            } else {
                orderby = "total_hindex"
            }
            if (orderdirection === "") {
                order_direction = "desc"
            } else {
                order_direction = orderdirection;
            }
            $('#orderby').val(orderby)
            $('#orderdirection').val(order_direction)
        }

        if ($(this).attr("class") === "fa fa-fw fa-sort-desc") {
            setOrderByValue($(this), "asc");
        } else if ($(this).attr("class") === "fa fa-fw fa-sort-asc") {
            setOrderByValue($(this), "desc");
        } else {
            setOrderByValue($(this), "")
        }
        window.location.href = getUrl()

    })

    //function for selecting the language
    $("#ger").on('click', function () {
        localStorage.setItem("lang", "ger");
        if (document.location.href.includes('?language=eng')) {
            let url = window.location.href
            url= url.replace('language=eng', 'language=ger')
            window.location.href = url

        }else if (document.location.href.includes('?language=ger')){
            //do nothing
        } else if (document.location.href.includes('?')) {
            window.location.href += '&language=ger'
        } else {
            window.location.href += '?language=ger'
        }
    })
    $("#eng").on('click', function () {
        localStorage.setItem("lang", "eng");
        if (document.location.href.includes('?language=ger')) {
            let url = window.location.href
            url=url.replace('language=ger', 'language=eng')
            window.location.href = url
        }else if (document.location.href.includes('?language=eng')){
            //do nothing
        }
        else if (document.location.href.includes('?')) {
            window.location.href += '&language=eng'
        } else {
            window.location.href += '?language=eng'
        }
    })


    $('#search').on('keypress', function (e) {
        if (e.which == '13') {
            window.location.href = getUrl();
        }

    })

    $('#download').on("click",function (){

        window.location.href=getUrl(true)
        //window.location.href=(url).replace('/download',"")
    })

    //Table on authorpage
    // $(document).ready(function () {
    //     $('#publication').DataTable();
    // });
})
;

function removeParam(key, sourceURL) {
    var rtn = sourceURL.split("?")[0],
        param,
        params_arr = [],
        queryString = (sourceURL.indexOf("?") !== -1) ? sourceURL.split("?")[1] : "";
    if (queryString !== "") {
        params_arr = queryString.split("&");
        for (var i = params_arr.length - 1; i >= 0; i -= 1) {
            param = params_arr[i].split("=")[0];
            if (param === key) {
                params_arr.splice(i, 1);
            }
        }
        rtn = rtn + "?" + params_arr.join("&");
    }
    return rtn;
}

function getUrl(download) {
    let country = $('#country option:selected').text();
    let fromyear = $('#fromyear option:selected').text();
    let toyear = $('#toyear option:selected').text();
    let search = $('#search').val();
    let orderby = $('#orderby').val();
    let orderdirection = $('#orderdirection').val();
    let page = $('#page').val();
    let venues = $('input:checkbox:checked');
    let url = location.protocol + "//" + location.host + "?";
    if(download){
        url = url + "download=true" + "&";
    }
    if (country !== "Germany") {
        url = url + "country=" + country + "&";
    }
    if (fromyear !== "1970") {
        url = url + "fromyear=" + fromyear + "&";
    }
    if (toyear !== "2020") {
        url = url + "toyear=" + toyear + "&";
    }
    if (search !== "") {
        url = url + "search=" + search + "&";
    }
    if (orderby !== "pubs") {
        url = url + "orderby=" + orderby + "&";
    }
    if (orderdirection !== "desc") {
        url = url + "orderdirection=" + orderdirection + "&";
    }
    if (page !== "1") {
        url = url + "page=" + page + "&"
    }
    url = url + "venues=";
    $.each(venues, function () {
        url = url + this.value + ",";
    });
    url = url.slice(0, -1);
    return url;
}

function UnCryptMailto(s) {
    var n = 0;
    var r = "";
    for (var i = 0; i < s.length; i++) {
        n = s.charCodeAt(i);
        if (n >= 8364) {
            n = 128;
        }
        r += String.fromCharCode(n - 1);
    }
    return r;
}

function linkTo_UnCryptMailto(s) {
    location.href = UnCryptMailto(s);
}
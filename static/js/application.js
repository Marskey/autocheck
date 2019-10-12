var socket = null
var navbar_h = $(".navbar").outerHeight();
$(document).ready(function(){
    //connect to the socket server.
    var server = 'http://' + document.domain + ':' + location.port;
    console.log("server url:" + server);
    socket = io(server);
    var log_received = [];
    // 每页的数据数量
    var one_page_count = 10;
    var server_time_offset = 0;
    var sel_page = 0;
    var data_inited = false;

    navbar_h = $(".navbar").height();

    socket.on('disconnect', () => {
        socket.open();
    });

    socket.on('reconnect', (data) => {
        alert('reconnect');
    });

    socket.on('connect_timeout', (data) => {
        socket.open();
    });

    socket.on('connect_error', (data) => {
        socket.open();
    });

    socket.on('connect', () => {
    })

    // 分页显示逻辑处理
    function changePagination(offset, total) {
        var visual_count = 9;
        var cur_page = parseInt(offset / one_page_count) + 1;
        var total_page = parseInt(total / one_page_count + 0.5);
        if (total_page == 0) {
            total_page = 1
        }

        var first_page = '<li><a href="?offset=(0)" >&laquo;</a>\
                          </li>';
        if (cur_page == 1) {
            first_page = '<li class = "disabled"><a>&laquo;</a>\
                          </li>';
        }

        var min_num = cur_page - parseInt(visual_count / 2);
        if (min_num <= 0) {
            min_num = 1;
        }

        var max_num = cur_page + parseInt(visual_count / 2)
        if (max_num > total_page) {
            max_num = total_page;
        }

        var pre_page = '';
        var pre_page_num = (cur_page - 1);
        if (pre_page_num <= 0) {
            pre_page = '<li class = "disabled"><a><</a>\
                       </li>';
        } else {
            pre_page = '<li><a href="?offset=' + (pre_page_num - 1) * one_page_count + '"><</a>\
                       </li>';
        }

        var contain = '';

        for (i = min_num; i <= max_num; ++i) {
            if (i - min_num > visual_count) {
                break;
            }

            if (i == cur_page) {
                contain += '<li class="active"><a>' + i + '</a></li>'
            } else {
                contain += '<li><a href="?offset=' + (i - 1) * one_page_count + '">' + i + '</a></li>'
            }
        }

        var next_page = ''
        var next_page_num = (cur_page + 1);
        if (next_page_num > total_page) {
            next_page = '<li class = "disabled"><a>';
        } else {
            next_page = '<li><a href="?offset=' + (next_page_num - 1) * one_page_count + '">';
        }
        next_page += '></a>\
                      </li>';

        var last_page = '<li><a href="?offset=' + (total_page - 1) * one_page_count + '">';
        if (cur_page == total_page) {
            last_page = '<li class = "disabled"><a>';
        }

        last_page += '&raquo;</a>\
                      </li>';


        sel_page = cur_page;
        $('#pagination').html(first_page + pre_page + contain + next_page + last_page)
    }

    socket.on('server_log', function (data) {
        if (log_received.length > 12) {
            log_received.shift()
        }
        log_received.push(data);
        numbers_string = '';
        log_received.slice().reverse().forEach((value) => {
            numbers_string = numbers_string + '<h4>' + value + '</h4>';
        })
        $('#log').html(numbers_string);
    });

    socket.on('checker_state', function(state) {
        if (state == 1) {
            $("#check_btn").removeClass("btn-success").addClass("btn-danger").html('停止检查<i class="glyphicon glyphicon-stop"></i>')
            $("#table_container button").attr('disabled', true)
        } else {
            $("#check_btn").removeClass("btn-danger").addClass("btn-success").html('开始检查<i class="glyphicon glyphicon-play"></i>')
            $("#table_container button").attr('disabled', false)

            if (data_inited) {
                req_revision_info()
            }
        }
    })

    // 请求版本信息
    function req_revision_info() {
        if (socket != null) {
            $('#table_container').html('<tr><td colspan="4"><p>Loading...</p></td></tr>');
            offset = getQueryVariable("offset", 0);
            socket.emit('req_revision_info', $("#checker_selector").val(), parseInt(offset), parseInt(one_page_count));
            data_inited = false;
        }
    }

    // 版本信息回包处理
    socket.on('ack_revision_info', (msg) => {
        $('#table_container').html("");
        Object.keys(msg.data).sort().reverse().forEach((key) => {
            value = msg.data[key];
            // 版本号, 时间
            var row = "<tr id='" + key + "'>\
                       <td><a href=''>r" + value.rev + "</a></td>\
                       <td>" + value.time + "</td>"

            // 报告
            row += "<td>"
            if (value.report_path !== "") {
                row += "<a href='" + value.report_path + "'>网页报告</a>"
                row += ", "
                row += "<a href='" + value.plog_path + "?local_dir=" + $("#local_src_dir").val() + "'>下载原报告文件</a>"
            } else {
                row += "None"
            }

            row += "<button class='btn btn-info pull-right' type='button'>\
                            重检 <i class='glyphicon glyphicon-repeat'></i>\
                        </button>"

            row += "</td>"

            // 作者
            row += "<td>"
            row += "<a href=''>" + value.author + "</a>"
            row += "</td>"
            row += "</tr>"
            // newline
            // 有错误的文件名preview
            if (value.analysis_files.length != 0) {
                row += "<tr><td colspan='4'><div style='max-height: 150px; overflow:auto;'> <table class='table table-bordered '> <tbody>"
                value.analysis_files.forEach(function (proj_file) {
                    row += "<tr class='warning'>"
                    var items = proj_file.split(',')
                    row += "<td style='width:15%'>" + items[0] + "</td>"
                    if (items.length > 1) {
                        row += "<td>" + items[1] + "</td>"
                    }
                    row += "</tr>"
                })
                row += "</tbody></table></div></td><tr>"
            }

            // newline
            // commit 日志
            row +="<tr><td colspan='4'>"
            row +="<strong>" + value.msg + "</strong>" 
            row +="</td></tr>"

            $('#table_container').append(row);
        })

        server_time = parseInt(msg.cur_time);
        server_time_offset = server_time - parseInt(new Date().getTime() / 1000)
        show_left_time();

        changePagination(msg.offset, msg.total);
        data_inited = true;
    })

    $("#check_btn").on('click', function () {
        if (socket != null) {
            if ($(this).hasClass("btn-success")) {
                socket.emit('start_check')
            } else {
                socket.emit('stop_check')
            }
        }
    })

    InterValObj = window.setInterval(show_left_time, 1000);
    function show_left_time() {
        // 9, 12, 15, 18, 21
        var left_sec = 0;
        var cur_time = new Date()
        var event = new Date();
        if (cur_time.getHours() < 9) {
            event.setHours(9, 0, 0);
        } else if (cur_time.getHours() < 12) {
            event.setHours(12, 0, 0);
        } else if (cur_time.getHours() < 15) {
            event.setHours(15, 0, 0);
        } else if (cur_time.getHours() < 18) {
            event.setHours(18, 0, 0);
        } else if (cur_time.getHours() < 21) {
            event.setHours(21, 0, 0);
        } else {
            event.setDate(event.getDate() + 1)
            event.setHours(9, 0, 0);
        }

        left_sec = parseInt((event - cur_time + server_time_offset) / 1000);

        var htmlstr = "<h4>距离下次自检还有: ";
        left_sec = left_sec % (24 * 3600);
        var hour = parseInt(left_sec / 3600);
        if (hour != 0) {
            htmlstr += hour + "小时 ";
        }

        left_sec %= 3600;
        var min = parseInt(left_sec / 60);
        if (min != 0) {
            htmlstr += min + "分钟 ";
        }

        left_sec %= 60;
        var sec = left_sec;
        htmlstr += sec + "秒 ";

        htmlstr += "</h4>"

        $("#left_time").html(htmlstr);
    }

    socket.on('ack_checker_list', (msg) => {
        var contain = ""
        msg.forEach(function(value) {
            contain += "<option>"
            contain += value
            contain += "</option>"
        })
        $("#checker_selector").html(contain)
        $("#checker_selector").selectpicker('refresh')

        co_checker_name = getCookie('checker')
        if (co_checker_name != null) {
            $("#checker_selector").selectpicker('val', co_checker_name)
        } 

        req_revision_info()
    })

    $("#checker_selector").on('change', function() {
        req_revision_info()
        checker_name = $("#checker_selector").val()
        setCookie('checker', checker_name)
    })

    $("#table_container").on('click', 'button', function() {
        rev = $(this).parent().parent().attr('id')
        checker_name = $("#checker_selector").val()
        if (socket != null) {
            socket.emit('recheck', rev, checker_name)
        }
    })

    $("#local_src_dir").on('change', (e) => {
        setCookie('local_dir', $("#local_src_dir").val())
        checkHasLocalDir()
    })

    local_dir = getCookie('local_dir')
    $("#local_src_dir").val(local_dir)
    $("#local_src_dir").attr('title', local_dir)
    checkHasLocalDir()

    function checkHasLocalDir() {
        if ($("#local_src_dir").val() == "") {
            $('body').prepend('<div class="alert alert-warning alert-dismissible " style="position: fixed; margin-top: 60px; left:50%; z-index:10">\
        <button type="button" class="close" data-dismiss="alert" aria-label="Close"><span\
                aria-hidden="true">&times;</span></button>\
        <strong>Warning!</strong> 未输入本地项目路径，这将会影响报告文件索引\
    </div>')
            $("#local_src_dir").parent().addClass('has-error')
        } else {
            $('.alert').remove()
            $("#local_src_dir").parent().removeClass('has-error')
        }
    }
});

$(document).scroll(function () {
    var scroll_h = $(document).scrollTop(); //滚动条高度

    if (scroll_h > navbar_h + 50) { //当滚动条高度 > 侧边栏底部到顶部的高
        $("#sidepanel").css({
            'position': 'fixed',
            'top': navbar_h,
        });
    } else { //如果滚动条高度 <  侧边栏底部到顶部的高
        $("#sidepanel").css({
            'position': '',
            'top': '',
        });
    }
})

function getQueryVariable(variable, def_value)
{
       var query = window.location.search.substring(1);
       var vars = query.split("&");
       for (var i=0;i<vars.length;i++) {
               var pair = vars[i].split("=");
               if(pair[0] == variable){return pair[1];}
       }
       return def_value;
}

function setCookie(name, value) {
    var Days = 30;
    var exp = new Date();
    exp.setTime(exp.getTime() + Days*24*60*60*1000);
    document.cookie = name + "="+ escape (value) + ";expires=" + exp.toGMTString();
}

//获取cookie
function getCookie(name)
{
    var arr,reg=new RegExp("(^| )"+name+"=([^;]*)(;|$)");
    if(arr=document.cookie.match(reg))
    return unescape(arr[2]);
    else
    return null;
}

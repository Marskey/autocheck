var socket = null
var navbar_h = 0;
var header_h = 0;
$(document).ready(function(){
    //connect to the socket server.
    var server = 'http://' + document.domain + ':' + location.port;
    socket = io(server);
    var log_received = [];
    // 每页的数据数量
    var one_page_count = 10;
    var server_time_offset = 0;
    var sel_page = 0;
    navbar_h = $(".navbar").height();
    header_h = $(".page-header").outerHeight();

    resetLogPanelHeight()

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

    socket.on('server_log', function (data) {
        if (log_received.length > 12) {
            log_received.shift()
        }
        log_received.push(data);
        numbers_string = '';
        log_received.slice().reverse().forEach((value) => {
            numbers_string = numbers_string + '<p>' + value + '</p>';
        })
        $('#log').html(numbers_string);
    });

    socket.on('checker_state', function(state) {
        if (state == 1) {
            $("#check_btn").removeClass("btn-success").addClass("btn-danger").html('停止检查<i class="glyphicon glyphicon-stop"></i>')
        } else {
            $("#check_btn").removeClass("btn-danger").addClass("btn-success").html('立即检查<i class="glyphicon glyphicon-play"></i>')
        }
    })

    socket.on('checking_progress', function(data) {
        var has_excep = false

        var percent = 100
        if (data.total == 0) {
            has_excep = true
            $('#text_progress').html("")
        } else {
            percent = data.cur / data.total * 100 
            $('#text_progress').html(data.cur + "/" + data.total)
        }

        if (percent == 0) {
            $('.progress-bar').removeClass("progress-bar-success");
            $('.progress-bar').removeClass("progress-bar-danger");
            $('.panel-footer').css('border-color', "#ddd")
            $('.progress-bar').addClass('notransition')
            $('.progress-bar').css('width', percent + '%');
            $('.progress-bar').removeClass('notransition')
        } else {
            $('.progress-bar').css('width', percent + '%');
        }

        if (percent >= 100) {
            var progressbar_color = "progress-bar-success"
            var board_color = "#5cb85c"

            if (has_excep) {
                progressbar_color = "progress-bar-danger"
                board_color = "#d9534f"
            }

            $('.progress-bar').addClass(progressbar_color);
            $('.panel-footer').css('border-color', board_color)
            $('.progress').slideUp('slow');
        } else {
            $('.progress').slideDown('fast');
        }
    })

    // 请求版本信息
    function req_revision_info() {
        if (socket != null) {
            $('#table_container').html('<tr><td colspan="4"><p>Loading...</p></td></tr>');
            var offset = getQueryVariable("offset", 0);
            socket.emit('req_revision_info', $("#checker_selector").val(), parseInt(offset), parseInt(one_page_count), $('#search_input').val());
        }
    }

    // 版本信息回包处理
    socket.on('ack_revision_info', (msg) => {
        $('#table_container').html("");
        Object.keys(msg.data).sort().reverse().forEach((key) => {
            value = msg.data[key];
            var row = "<tr>"
            // project
            row += "<td style='overflow-wrap: break-word;' >" + value.project + "</td>"

            // file
            row += "<td style='overflow-wrap: break-word;' >" + value.file + "</td>"

            // time
            row += "<td>" + value.time + "</td>"

            // result
            row += "<td>"
            row += "<a target='_blank' href='" + value.html_path + "'>网页报告</a>"
            row += "<br> "
            row += "<a href='" + value.report_path + "?local_dir=" + $("#local_src_dir").val() + "'>下载原报告文件</a>"
            row += "<br> "
            row += "<a onclick='ignore_report(this, \"" + value.file_path + "\")'>忽略</a>"
            row += "</td>"

            // newline
            // log
            if (value.log.length != 0) {
                row += "<tr><td colspan='4'><div style='max-height: 150px; overflow:auto;'> <table class='table table-bordered '> <tbody>"
                value.log.forEach(function (pre_log) {
                    log_json = JSON.parse(pre_log)
                    row += "<tr class='warning'>"
                    row += "<td style='width:87px'>" + log_json.rev + "</td>"
                    row += "<td style='width:87px'>" + log_json.author + "</td>"
                    row += "<td>" + log_json.msg + "</td>"
                    row += "</tr>"
                })
                row += "</tbody></table></div></td><tr>"
            }

            row = row.replace(/[\r\n]/, "<br>")
            if ($('#search_input').val() != "") {
                var regEx = new RegExp("(<td[^>]*>[^<]*?)(" + $('#search_input').val() + ")(.*?<\/td>)", 'ig')
                row = row.replace(regEx, "$1<span class='search-highlight'>$2</span>$3")
            }

            $('#table_container').append(row);
        })
    })

    socket.on('ack_report_total', function (data) {
        changePagination(data.offset, data.total);
        var server_time = parseInt(data.time)
        server_time_offset = server_time - parseInt(new Date().getTime() / 1000)
        show_left_time();
        $('#result').html(data.total)
    })

    socket.on('ack_get_checker_config', function(data) {
        var json = JSON.parse(data)
        for (var key in json) {
            $('#checkerConfigModal .modal-dialog .modal-content .modal-body .row').html('\
                    <div>\
                    <label class="col-sm-2 control-label">'+ key +'</label>\
                    <div class="col-sm-10">\
                        <input class="form-control" value="'+ json[key] +'">\
                    </div></div>')
        }
        $('#checkerConfigModal').modal({ keyboard: false });
    })

    $("#check_btn").on('click', function () {
        if (socket != null) {
            if ($(this).hasClass("btn-success")) {
                checker_name = $("#checker_selector").val()
                socket.emit('start_check')
            } else {
                socket.emit('stop_check')
            }
        }
    })

    InterValObj = window.setInterval(show_left_time, 1000);

    function show_left_time() {
        // // 9, 12, 15, 18, 21
        // var left_sec = 0;
        // var cur_time = new Date()
        // var event = new Date();
        // if (cur_time.getHours() < 9) {
        //     event.setHours(9, 0, 0);
        // } else if (cur_time.getHours() < 12) {
        //     event.setHours(12, 0, 0);
        // } else if (cur_time.getHours() < 15) {
        //     event.setHours(15, 0, 0);
        // } else if (cur_time.getHours() < 18) {
        //     event.setHours(18, 0, 0);
        // } else if (cur_time.getHours() < 21) {
        //     event.setHours(21, 0, 0);
        // } else {
        //     event.setDate(event.getDate() + 1)
        //     event.setHours(9, 0, 0);
        // }

        // left_sec = parseInt((event - cur_time + server_time_offset) / 1000);

        // var htmlstr = "<h4>距离下次自检还有: ";
        // left_sec = left_sec % (24 * 3600);
        // var hour = parseInt(left_sec / 3600);
        // if (hour != 0) {
        //     htmlstr += hour + "小时 ";
        // }

        // left_sec %= 3600;
        // var min = parseInt(left_sec / 60);
        // if (min != 0) {
        //     htmlstr += min + "分 ";
        // }

        // left_sec %= 60;
        // var sec = left_sec;
        // htmlstr += sec + "秒 ";

        // htmlstr += "</h4>"

        // $("#left_time").html(htmlstr);
    }

    socket.on('ack_init_data', (data) => {
        var contain = ""
        data.checker_list.forEach(function(value) {
            contain += "<option>"
            contain += value
            contain += "</option>"
        })
        $("#checker_selector").html(contain)
        $("#checker_selector").selectpicker('refresh')

        co_checker_name = getCookie('checker')
        if (co_checker_name != null) {
            $("#checker_selector").selectpicker('val', co_checker_name)
        } else {
            co_checker_name = $("#checker_selector").val()
        }

        if (data.checker_state == 1) {
            $("#check_btn").removeClass("btn-success").addClass("btn-danger").html('停止检查<i class="glyphicon glyphicon-stop"></i>')
        } else {
            $("#check_btn").removeClass("btn-danger").addClass("btn-success").html('立即检查<i class="glyphicon glyphicon-play"></i>')
        }

        $('#rev_start').val("从版本 r" + data.dic_err_revs[co_checker_name] + " 开始检查")

        req_revision_info()
    })

    $("#checker_selector").on('change', function() {
        req_revision_info()
        checker_name = $(this).val()
        setCookie('checker', checker_name)
    })

    $("#local_src_dir").on('change', (e) => {
        setCookie('local_dir', $("#local_src_dir").val())
        checkHasLocalDir()
    })

    local_dir = getCookie('local_dir')
    $("#local_src_dir").val(local_dir)
    $("#local_src_dir").attr('title', local_dir)
    checkHasLocalDir()
    $("#search_input").val(getCookie('search'))

    function checkHasLocalDir() {
        if ($("#local_src_dir").val() == "") {
            $('body').prepend('<div class="alert alert-warning alert-dismissible " style="position: fixed; margin-top: 60px; left:70%; z-index:10">\
        <button type="button" class="close" data-dismiss="alert" aria-label="Close"><span\
                aria-hidden="true">&times;</span></button>\
        <strong>注意!</strong>&nbsp&nbsp未输入本地项目路径，这将会影响报告文件索引\
    </div>')
            $("#local_src_dir").parent().addClass('has-error')
        } else {
            $('.alert').remove()
            $("#local_src_dir").parent().removeClass('has-error')
        }
    }

    // 分页显示逻辑处理
    function changePagination(offset, total) {
        var visual_count = 6;
        var cur_page = parseInt(offset / one_page_count) + 1;
        var total_page = parseInt((total - 1) / one_page_count) + 1;

        var pre_page = '';
        var pre_page_num = (cur_page - 1);
        if (pre_page_num <= 0) {
            pre_page = '<li class = "disabled"><a>< Prev</a></li>';
        } else {
            pre_page = '<li><a href="?offset=' + (pre_page_num - 1) * one_page_count + '">< Prev</a></li>';
        }

        var min_num = 1;
        var max_num = total_page;

        if (total_page > visual_count) {
            var min_num = cur_page - parseInt(visual_count / 2);
            var max_num = cur_page + parseInt(visual_count / 2);
            if (min_num <= 0) {
                var dif_val = 1 - min_num;
                min_num += dif_val;
                max_num += dif_val;
            } else if (max_num >= total_page) {
                var dif_val = max_num - total_page;
                max_num -= dif_val;
                min_num -= dif_val;
            }
        }

        var first_page = ''
        if (min_num != 1) {
            first_page = '<li><a href="?offset=0">1</a></li><li><a>...</a></li>';
        }

        var last_page = ''
        if (max_num != total_page) {
            last_page = '<li><a>...</a></li><li><a href="?offset=' + (total_page - 1) * one_page_count + '">';
            last_page += total_page
            last_page += '</a></li>';
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
        next_page += 'Next ></a>\
                      </li>';

        sel_page = cur_page;
        $('#pagination').html(pre_page + first_page + contain + last_page + next_page)
    }

    $('#search_input').on("search", function (e) {
        $(this).val($(this).val().trim())
        setCookie('search', $(this).val())
        window.location.href = "?offset=0"
        req_revision_info()
    })

    $('#checker_config_btn').on("click", function() {
        var title = $('#checker_selector').val() + " Config"
        $('#checkerConfigModal .modal-dialog .modal-content .modal-header .modal-title').html(title)
        socket.emit('get_checker_config', $("#checker_selector").val());
    })

    $('#save_checker_config').on("click", function() {
        var data = {}
        $('#checkerConfigModal .modal-dialog .modal-content .modal-body .row').children().each(function(i, n) {
                data[$(n).find(".control-label") .html()] = $(n).find(".col-sm-10 .form-control").val()
        })
        socket.emit('set_checker_config', $("#checker_selector").val(), JSON.stringify(data))
        $('#checkerConfigModal').modal('hide');
    })
});

$(document).scroll(function () {
    var scroll_h = $(document).scrollTop(); //滚动条高度
    if (scroll_h > navbar_h + header_h) { //当滚动条高度 > 侧边栏底部到顶部的高
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

$(window).resize(function () {
    resetLogPanelHeight()
})

function resetLogPanelHeight() {
    $(".panel-body").css('max-height', $(window).height() - navbar_h - header_h - $(".panel-heading").height() - 150);
    $(".main").css('height', $(window).height() - navbar_h - header_h - $(".panel-heading").height() - 80);
}

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

function ignore_report(self, file_path) {
    if (!confirm("确定要忽略？ " + file_path)) {
        return
    }
    socket.emit('ignore_report', $("#checker_selector").val(), file_path)
    self.closest("tr").nextElementSibling.remove()
    self.closest("tr").remove()
}

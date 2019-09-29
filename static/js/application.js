var socket = null
$(document).ready(function(){
    //connect to the socket server.
    var server = 'http://' + document.domain + ':' + location.port;
    console.log("server url:" + server);
    socket = io(server);
    var log_received = [];
    // 每页的数据数量
    var one_page_count = 5;
    var server_time_offset = 0;

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
        req_revision_info(offset)
    })

    // 分页显示逻辑处理
    function changePagination(offset, total) {
        var visual_count = 9;
        var cur_page = parseInt(offset / one_page_count) + 1;
        var total_page = parseInt(total / one_page_count + 0.5);

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


        $('ul').html(first_page + pre_page + contain + next_page + last_page)
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
            $(".btn").removeClass("btn-success").addClass("btn-danger").html('<i class="glyphicon glyphicon-stop"></i>')
        } else {
            $(".btn").removeClass("btn-danger").addClass("btn-success").html('<i class="glyphicon glyphicon-play"></i>')
        }
    })

    // 请求版本信息
    function req_revision_info(offset) {
        if (socket != null) {
            $('table tbody').html('<tr><td colspan="3"><p>Loading...</p></td></tr>');
            socket.emit('req_revision_info', parseInt(offset), parseInt(one_page_count));
        }
    }

    // 版本信息回包处理
    socket.on('ack_revision_info', (msg) => {
        $('table tbody').html("");
        Object.keys(msg.data).sort().reverse().forEach((key) => {
            value = msg.data[key];
            var row = "<tr id='" + key + "'>\
                       <td><a href=''>" + value.rev + "</a></td>\
                       <td>" + value.time + "</td>"

            if (value.report_path !== "") {
                row += "<td>"
                row += "<a href='" + value.report_path + "'>PVS-Html</a>"
                row += ", "
                row += "<a href='" + value.plog_path + "'>下载plog</a>"
                row += "</td>"
            } else {
                row += "<td>None</td>"
            }

            row += "</tr>"

            $('table tbody').append(row);
        })

        server_time = parseInt(msg.cur_time);
        server_time_offset = server_time - parseInt(new Date().getTime() / 1000)
        show_left_time();

        changePagination(msg.offset, msg.total);
    })

    $(".btn").on('click', function () {
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
});
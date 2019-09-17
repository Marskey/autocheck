var socket = null
$(document).ready(function(){
    //connect to the socket server.
    var server = 'http://' + document.domain + ':' + location.port;
    console.log("server url:" + server);
    socket = io(server);
    var log_received = [];
    // 每页的数据数量
    var one_page_count = 5;

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

    // 版本信息回包处理
    socket.on('ack_revision_info', (msg) => {
        $('table tbody').html("");
        $.each(msg.data, function(key, value) {
            var row = "<tr id='" + key + "'>\
                       <td><a href=''>" + value.rev + "</a></td>\
                       <td>" + value.time + "</td>"

            if (value.report_path !== "") {
                row += "<td><a href='" + value.report_path + "'>PVS-Studio</a></td>"
            } else {
                row += "<td>None</td>"
            }

            row += "</tr>"

            $('table tbody').append(row);
        })

        console.log(msg.offset, msg.total)

        changePagination(msg.offset, msg.total);
    })

    // 分页显示逻辑处理
    function changePagination(offset, total) {
        var visual_count = 9;
        var cur_page = parseInt(offset / one_page_count) + 1;
        var total_page = parseInt(total / one_page_count) + 1;

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

            contain += '<li '
            if (i == cur_page) {
                contain += 'class="active"'
            }

            contain += '><a href="?offset=' + (i - 1) * one_page_count + '">' + i + '</a></li>'
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
        // if (log_received.length > 100) {
        //     log_received.shift()
        // }
        // log_received.push(data.msg);
        // numbers_string = '';
        // for (var i = 0; i < log_received.length; i++) {
        //     numbers_string = numbers_string + '<p>' + log_received[i].toString() + '</p>';
        // }
        // $('#log').html(numbers_string);
    });

    // 请求版本信息
    function req_revision_info(offset) {
        if (socket != null) {
            socket.emit('req_revision_info', parseInt(offset), parseInt(one_page_count));
        }
    }
});


var socket = null
$(document).ready(function(){
    //connect to the socket server.
    var server = 'http://' + document.domain + ':' + location.port;
    console.log("server url:" + server);
    socket = io(server);
    var log_received = [];

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
        req_revision_info(0);
    })

    socket.on('ack_revision_info', (msg) => {
        $.each(msg.data, function(key, value) {
            var row = "<tr id='" + key + "'>\
                       <td><a href=''>" + value.rev + "</a></td>\
                       <td>" + value.time + "</td>\
                       <td><a href='" + value.report_path + "'>PVS-Studio</a>\
                       </td>\
                   </tr>"
            $('table tbody').append(row);
        })

        console.log(msg.offset, msg.total)

        changePagination(msg.offset, msg.total);
    })

    function changePagination(offset, total) {
        var first_page = '<li><a href="javascript:req_revision_info(0)" aria-label="First">\
                               <span aria-hidden="true">&laquo;</span>\
                           </a>\
                       </li>';
        
        var visual_count = 9;
        var one_page_count = 20;
        var cur_page = parseInt(offset / one_page_count) + 1;
        var total_page = parseInt(total / one_page_count) + 1;

        if (cur_page + parseInt(visual_count / 2)  > total_page) {
            num = total_page - visual_count + 1;
        }

        var num = cur_page - parseInt(visual_count / 2);
        if (num <= 0) {
            num = 1;
        }

        var pre_page = '';
        var pre_page_num = (cur_page - 1);
        if (pre_page_num <= 1) {
            pre_page = '<li class = "disabled"><a><</a>\
                       </li>';
        } else {
            pre_page = '<li><a href="javascript:req_revision_info(' + (pre_page_num - 1) * one_page_count + ')" aria-label="Previous">\
                               <span aria-hidden="true"><</span>\
                           </a>\
                       </li>';
        }

        var contain = '';
        for (i = 0; i < visual_count; ++i) {
            if (i > total_page) {
                break;
            }
            contain += '<li><a href="#">' + num 
            if (num == cur_page) {
                contain += '<span class="sr-only">(current)</span>'
            }
            contain += '</a></li>'
            ++num
        }

        var next_page = ''
        var next_page_num = (cur_page + 1);
        if (next_page_num >= total_page) {
            next_page = '<li class = "disabled"><a>></a>\
                         </li>';
        } else {
            next_page = '<li><a href="javascript:req_revision_info(' + (next_page_num - 1) * one_page_count + ')" aria-label="Next">\
                               <span aria-hidden="true">></span>\
                           </a>\
                         </li>';
        }

        var last_page = '<li><a href="javascript:req_revision_info(' + (total_page - 1) * one_page_count + ')" aria-label="Last">\
                               <span aria-hidden="true">&raquo;</span>\
                           </a>\
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
});

function req_revision_info(offset) {
    if (socket != null) {
        socket.emit('req_revision_info', parseInt(offset));
    }
}

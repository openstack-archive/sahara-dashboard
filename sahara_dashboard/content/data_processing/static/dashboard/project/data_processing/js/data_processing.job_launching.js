horizon.job_launching_warning = {

    show_warning: function(cl_name_status_map, status_message_map) {
        var cl_choice_elem = $('.cluster_choice').parent();
        var current_cl_name = $('.cluster_choice option:selected').text();
        var current_cl_status = cl_name_status_map[current_cl_name];
        var warning_msg = status_message_map[current_cl_status];
        var warning_elem = "<div class=\"not_active_state_warning alert alert-dismissable alert-warning\">" +
                            "<h4>" + gettext("Warning!") + "</h4>" +
                            "<p>" + warning_msg + "</p>" +
                            "</div>";

        if ($.isEmptyObject(cl_name_status_map) || current_cl_status === 'Active') {
            $('.not_active_state_warning').remove();
        } else {
            cl_choice_elem.append(warning_elem);
            $('.not_active_state_warning').css('margin-top', '5px');
        }
    }

};

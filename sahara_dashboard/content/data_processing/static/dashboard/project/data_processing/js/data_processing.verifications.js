horizon.verifications = {
    data_update_url: null,

    update_health_checks: function() {
        var url = this.data_update_url + "/verifications";
        $.get(url).done(function(data) {
            horizon.verifications.update_health_checks_view(data.checks);
            horizon.verifications.schedule_next_update(data);
        }).fail(function() {
            horizon.alert("error", gettext("Verification is not available."));
        });
    },

    update_health_checks_view: function(checks) {
        // Clear health checks
        $("#sahara_health_checks_body").find("tr").remove();

        $(checks).each(function (i, check) {
            horizon.verifications.create_check_row(check);
        });
    },

    create_check_row: function(check) {
        var check_row_template = "" +
            "<tr id='%check_id%'>" +
            "<td>%status%</td>" +
            "<td>%name%</td>" +
            "<td>%duration%</td>" +
            "<td>%description%</td>" +
            "</tr>";

        var status_template = "" +
            "<span class='label label-%label_type%'>%status_text%</span>";
        var status = status_template
                .replace(/%label_type%/g, check.label)
                .replace(/%status_text%/g, check.status);

        var row = check_row_template
                .replace(/%check_id%/g, check.id)
                .replace(/%name%/g, check.name)
                .replace(/%duration%/g, check.duration)
                .replace(/%status%/g, status)
                .replace(/%description%/g, check.description);
        $("#sahara_health_checks_body").append(row);
    },

    schedule_next_update: function(data) {
        // 2-3 sec delay so that if there are multiple tabs polling the
        // backend the requests are spread in time
        var delay = 2000 + Math.floor((Math.random() * 1000) + 1);

        if (data.need_update) {
            setTimeout(function() {
                horizon.verifications.update_health_checks(); }, delay);
        }
    }

};

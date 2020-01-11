# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pytz import timezone as ptz

from django.template import defaultfilters as filters
from django.utils import timezone
from django.utils.translation import ugettext
from django.utils.translation import ugettext_lazy as _
from oslo_utils import timeutils

import sahara_dashboard.content.data_processing. \
    utils.workflow_helpers as work_helpers
from sahara_dashboard.api import sahara as saharaclient


class Helpers(object):
    def __init__(self, request):
        self.request = request

    def _get_node_processes(self, plugin):
        processes = []
        for proc_lst in plugin.node_processes.values():
            processes += proc_lst

        return [(proc_name, proc_name) for proc_name in processes]

    def get_node_processes(self, plugin_name, hadoop_version):
        plugin = saharaclient.plugin_get_version_details(self.request,
                                                         plugin_name,
                                                         hadoop_version)

        return self._get_node_processes(plugin)

    def _extract_parameters(self, configs, scope, applicable_target):
        parameters = []
        for config in configs:
            if (config['scope'] == scope and
                    config['applicable_target'] == applicable_target):

                parameters.append(work_helpers.Parameter(config))

        return parameters

    def get_cluster_general_configs(self, plugin_name, hadoop_version):
        plugin = saharaclient.plugin_get_version_details(self.request,
                                                         plugin_name,
                                                         hadoop_version)

        return self._extract_parameters(plugin.configs, 'cluster', "general")

    def get_general_node_group_configs(self, plugin_name, hadoop_version):
        plugin = saharaclient.plugin_get_version_details(self.request,
                                                         plugin_name,
                                                         hadoop_version)

        return self._extract_parameters(plugin.configs, 'node', 'general')

    def get_general_and_service_nodegroups_parameters(self, plugin_name,
                                                      hadoop_version):
        plugin = saharaclient.plugin_get_version_details(
            self.request, plugin_name, hadoop_version)

        general_parameters = self._extract_parameters(
            plugin.configs, 'node', 'general')

        service_parameters = {}
        for service in plugin.node_processes.keys():
            service_parameters[service] = self._extract_parameters(
                plugin.configs, 'node', service)

        return general_parameters, service_parameters

    def get_targeted_cluster_configs(self, plugin_name, hadoop_version):
        plugin = saharaclient.plugin_get_version_details(self.request,
                                                         plugin_name,
                                                         hadoop_version)

        parameters = {}

        for service in plugin.node_processes.keys():
            parameters[service] = self._extract_parameters(plugin.configs,
                                                           'cluster', service)

        return parameters

    def is_from_guide(self):
        referer = self.request.environ.get("HTTP_REFERER")
        if referer and ("/cluster_guide" in referer
                        or "/jobex_guide" in referer):
            return True
        return False

    def reset_guide(self):
        try:
            self.request.session.update(
                {"plugin_name": None,
                 "plugin_version": None,
                 "master_name": None,
                 "master_id": None,
                 "worker_name": None,
                 "worker_id": None,
                 "guide_cluster_template_name": None})
        except Exception:
            return False
        return True

    def reset_job_guide(self):
        try:
            self.request.session.update(
                {"guide_job_type": None,
                 "guide_job_name": None,
                 "guide_job_id": None,
                 "guide_datasource_id": None,
                 "guide_datasource_name": None, })
        except Exception:
            return False
        return True

    def get_duration(self, start_time, end_time=None):
        """Calculates time delta between start and end timestamps

        Calculates the delta between given timestamps. The arguments should
        be provided as strings. The format should match %Y-%m-%dT%H:%M:%S
        which is returned by default from Sahara API.
        The end time may be skipped. In this case datetime.now() will be used.

        :param start_time: Start timestamp.
        :param end_time: (optional) End timestamp.
        :return: The delta between timestamps.
        """

        start_datetime = timeutils.parse_isotime(start_time)

        if end_time:
            end_datetime = timeutils.parse_isotime(end_time)
        else:
            end_datetime = timeutils.utcnow(True)
            end_datetime = end_datetime.replace(microsecond=0)

        return str(end_datetime - start_datetime)

    def to_time_zone(self, datetime, tzone=None,
                     input_fmt=None, localize=False):
        """Changes given datetime string into given timezone

        :param datetime: datetime string
        :param tzone: (optional) timezone as a string (e.g. "Europe/Paris"),
               by default it's the current django timezone
        :param input_fmt: (optional) format of datetime param, if None then
               the default Sahara API format (%Y-%m-%dT%H:%M:%S) will be used
        :param localize: (optional) if True then format of datetime will be
               localized according to current timezone else it will be in
               the default Sahara API format (%Y-%m-%dT%H:%M:%S)
        :return datetime string in the current django timezone
        """

        default_fmt = '%Y-%m-%dT%H:%M:%S'
        if tzone is None:
            tzone = self.request.session.get('django_timezone', 'UTC')
        if input_fmt is None:
            input_fmt = default_fmt
        dt_in_utc = timezone.utc.localize(
            timeutils.parse_strtime(datetime, input_fmt))
        dt_in_zone = dt_in_utc.astimezone(ptz(tzone))
        if localize:
            return filters.date(dt_in_zone, "DATETIME_FORMAT")
        else:
            return dt_in_zone.strftime(default_fmt)


# Map needed because switchable fields need lower case
# and our server is expecting upper case.  We will be
# using the 0 index as the display name and the 1 index
# as the value to pass to the server.
JOB_TYPE_MAP = {"pig": [_("Pig"), "Pig"],
                "hive": [_("Hive"), "Hive"],
                "spark": [_("Spark"), "Spark"],
                "storm": [_("Storm"), "Storm"],
                "storm.pyleus": [_("Storm Pyleus"), "Storm.Pyleus"],
                "mapreduce": [_("MapReduce"), "MapReduce"],
                "mapreduce.streaming": [_("Streaming MapReduce"),
                                        "MapReduce.Streaming"],
                "java": [_("Java"), "Java"],
                "shell": [_("Shell"), "Shell"]}

# Statuses of clusters that we can choose for job execution and
# suitable messages that will be displayed next to the cluster name
ALLOWED_STATUSES = {
    "Active": "",
    "Error": "(in error state)",
}

# Cluster status and suitable warning message that will be displayed
# in the Job Launch form
STATUS_MESSAGE_MAP = {
    "Error": ugettext("You\'ve chosen a cluster that is in \'Error\' state. "
                      "Appropriate execution of the job can't be guaranteed."),
}

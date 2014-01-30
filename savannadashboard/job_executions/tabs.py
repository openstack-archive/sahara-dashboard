# Copyright (c) 2013 Red Hat Inc.
#
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

import logging

from django.utils.translation import ugettext_lazy as _

from horizon import tabs

from savannadashboard.api.client import client as savannaclient

LOG = logging.getLogger(__name__)


class GeneralTab(tabs.Tab):
    name = _("General Info")
    slug = "job_execution_tab"
    template_name = ("job_executions/_details.html")

    def get_context_data(self, request):
        job_execution_id = self.tab_group.kwargs['job_execution_id']
        savanna = savannaclient(request)
        job_execution = savanna.job_executions.get(job_execution_id)
        object_names = self.get_object_names(job_execution, savanna)

        return {"job_execution": job_execution,
                "object_names": object_names}

    def get_object_names(self, job_ex, s_client):
        object_names = {}
        obj_names_map = {'input_name': {'obj': 'data_sources',
                                        'obj_id': job_ex.input_id},
                         'output_name': {'obj': 'data_sources',
                                         'obj_id': job_ex.output_id},
                         'cluster_name': {'obj': 'clusters',
                                          'obj_id': job_ex.cluster_id},
                         'job_name': {'obj': 'jobs',
                                      'obj_id': job_ex.job_id}}
        for item in obj_names_map:
            object_names[item] = (
                self.get_object_name(obj_names_map[item]['obj_id'],
                                     obj_names_map[item]['obj'],
                                     s_client))

        return object_names

    def get_object_name(self, obj_id, savanna_obj, s_client):
        object_name = None
        try:
            s_obj = getattr(s_client, savanna_obj)
            obj = s_obj.get(obj_id)
            object_name = obj.name
        except Exception as e:
            LOG.warn("Unable to get name for %s with object_id %s (%s)" %
                     (savanna_obj, obj_id, str(e)))
        return object_name


class JobExecutionDetailsTabs(tabs.TabGroup):
    slug = "job_execution_details"
    tabs = (GeneralTab,)
    sticky = True

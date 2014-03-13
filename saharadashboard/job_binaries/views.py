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

from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django import http
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon import tabs

from saharadashboard.api.client import client as savannaclient

import saharadashboard.job_binaries.forms as job_binary_forms
from saharadashboard.job_binaries.tables import JobBinariesTable
import saharadashboard.job_binaries.tabs as _tabs


LOG = logging.getLogger(__name__)


class JobBinariesView(tables.DataTableView):
    table_class = JobBinariesTable
    template_name = 'job_binaries/job_binaries.html'

    def get_data(self):
        savanna = savannaclient(self.request)
        job_binaries = savanna.job_binaries.list()
        return job_binaries


class CreateJobBinaryView(forms.ModalFormView):
    form_class = job_binary_forms.JobBinaryCreateForm
    success_url = reverse_lazy('horizon:sahara:job_binaries:index')
    classes = ("ajax-modal")
    template_name = "job_binaries/create.html"


class JobBinaryDetailsView(tabs.TabView):
    tab_group_class = _tabs.JobBinaryDetailsTabs
    template_name = 'job_binaries/details.html'

    def get_context_data(self, **kwargs):
        context = super(JobBinaryDetailsView, self)\
            .get_context_data(**kwargs)
        return context

    def get_data(self):
        pass


class DownloadJobBinaryView(View):
    def get(self, request, job_binary_id=None):
        try:
            savanna = savannaclient(request)
            jb = savanna.job_binaries.get(job_binary_id)
            data = savanna.job_binaries.get_file(job_binary_id)
        except Exception:
            redirect = reverse('horizon:sahara:job_binaries:index')
            exceptions.handle(self.request,
                              _('Unable to fetch job binary: %(exc)s'),
                              redirect=redirect)

        response = http.HttpResponse(mimetype='application/binary')
        response['Content-Disposition'] = \
            'attachment; filename=%s' % slugify(jb.name)
        response.write(data)
        response['Content-Length'] = str(len(data))
        return response

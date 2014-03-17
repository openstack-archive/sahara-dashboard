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

from horizon import tables

from saharaclient.api import base as api_base
from saharadashboard.api import client as saharaclient


LOG = logging.getLogger(__name__)


class CreateJobBinary(tables.LinkAction):
    name = "create job binary"
    verbose_name = _("Create Job Binary")
    url = "horizon:sahara:job_binaries:create-job-binary"
    classes = ("btn-launch", "ajax-modal")


class DeleteJobBinary(tables.BatchAction):
    name = "delete"
    action_present = _("Delete")
    action_past = _("Deleted")
    data_type_singular = _("Job binary")
    data_type_plural = _("Job binaries")
    classes = ('btn-danger', 'btn-terminate')

    def action(self, request, obj_id):
        sahara = saharaclient.client(request)
        jb = sahara.job_binaries.get(obj_id)
        (jb_type, jb_internal_id) = jb.url.split("://")
        if jb_type == "savanna-db":
            try:
                sahara.job_binary_internals.delete(jb_internal_id)
            except api_base.APIException:
                # nothing to do for job-binary-internal if
                # it does not exist.
                pass

        sahara.job_binaries.delete(obj_id)


class DownloadJobBinary(tables.LinkAction):
    name = "download job binary"
    verbose_name = _("Download Job Binary")
    url = "horizon:sahara:job_binaries:download"
    classes = ("btn-edit")


class JobBinariesTable(tables.DataTable):
    name = tables.Column("name",
                         verbose_name=_("Name"),
                         link=("horizon:sahara:job_binaries:details"))
    type = tables.Column("url",
                         verbose_name=_("Url"))
    description = tables.Column("description",
                                verbose_name=_("Description"))

    class Meta:
        name = "job_binaries"
        verbose_name = _("Job Binaries")
        table_actions = (CreateJobBinary,
                         DeleteJobBinary)
        row_actions = (DeleteJobBinary, DownloadJobBinary)

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

from django.http import Http404  # noqa
from django.urls import reverse
from django.utils import http
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy
from saharaclient.api import base as api_base

from horizon import messages
from horizon import tables
from horizon.tabs import base as tabs_base

from sahara_dashboard.api import sahara as saharaclient
from sahara_dashboard.content.data_processing.jobs.job_templates \
    import tables as j_t
from sahara_dashboard.content.data_processing \
    import tables as sahara_table
from sahara_dashboard.content.data_processing.utils \
    import acl as acl_utils
from sahara_dashboard.content.data_processing.utils import helpers


class JobsFilterAction(tables.FilterAction):
    filter_type = "server"
    filter_choices = (('id', _("ID"), True),
                      ('job', _("Job"), True),
                      ('cluster', _("Cluster"), True),
                      ('status', _("Status"), True))


class JobExecutionGuide(tables.LinkAction):
    name = "jobex_guide"
    verbose_name = _("Job Guide")
    url = "horizon:project:data_processing.jobs:jobex_guide"


class DeleteJob(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Job",
            u"Delete Jobs",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Job",
            u"Deleted Jobs",
            count
        )

    def delete(self, request, obj_id):
        saharaclient.job_execution_delete(request, obj_id)


class ReLaunchJobExistingCluster(j_t.ChoosePlugin):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Launch Job",
            u"Launch Jobs",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Launched Job",
            u"Launched Jobs",
            count
        )

    name = "relaunch-job-existing"
    verbose_name = _("Relaunch On Existing Cluster")
    url = "horizon:project:data_processing.jobs:launch-job"
    classes = ('ajax-modal', 'btn-launch')

    def get_link_url(self, datum):
        base_url = reverse(self.url)
        try:
            job_template_id = datum.job_template_id  # typical APIv2
        except AttributeError:
            job_template_id = datum.job_id  # APIv1.1, older APIv2
        params = http.urlencode({'job_id': job_template_id,
                                 'job_execution_id': datum.id})
        return "?".join([base_url, params])


class ReLaunchJobNewCluster(ReLaunchJobExistingCluster):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Launch Job",
            u"Launch Jobs",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Launched Job",
            u"Launched Jobs",
            count
        )

    name = "relaunch-job-new"
    verbose_name = _("Relaunch On New Cluster")
    url = "horizon:project:data_processing.jobs:choose-plugin"
    classes = ('ajax-modal', 'btn-launch')


class UpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, job_execution_id):
        try:
            return saharaclient.job_execution_get(request, job_execution_id)
        except api_base.APIException as e:
            if e.error_code == 404:
                raise Http404
            else:
                messages.error(request, _("Unable to update row"))


class MakePublic(acl_utils.MakePublic):
    def change_rule_method(self, request, datum_id, **update_kwargs):
        saharaclient.job_execution_update(request, datum_id, **update_kwargs)


class MakePrivate(acl_utils.MakePrivate):
    def change_rule_method(self, request, datum_id, **update_kwargs):
        saharaclient.job_execution_update(request, datum_id, **update_kwargs)


class MakeProtected(acl_utils.MakeProtected):
    def change_rule_method(self, request, datum_id, **update_kwargs):
        saharaclient.job_execution_update(request, datum_id, **update_kwargs)


class MakeUnProtected(acl_utils.MakeUnProtected):
    def change_rule_method(self, request, datum_id, **update_kwargs):
        saharaclient.job_execution_update(request, datum_id, **update_kwargs)


class JobsTable(sahara_table.SaharaPaginateTabbedTable):
    tab_name = 'job_tabs%sjobs_tab' % tabs_base.SEPARATOR

    class StatusColumn(tables.Column):
        def get_raw_data(self, datum):
            return datum.info['status']

    class JobNameColumn(tables.Column):
        @staticmethod
        def link(job_execution):
            if job_execution.job_name:
                try:
                    # typical APIv2
                    job_template_id = job_execution.job_template_id
                except AttributeError:
                    # APIv1.1, older APIv2
                    job_template_id = job_execution.job_id
                return reverse("horizon:project:data_processing."
                               "jobs:jt-details",
                               args=(http.urlquote(job_template_id),))
            else:
                # No link should be generated for a deleted Job.
                return None

        def get_data(self, job_execution):
            return job_execution.job_name or _("Not available")

    class ClusterNameColumn(tables.Column):

        @staticmethod
        def link(job_execution):
            if job_execution.cluster_name:
                return reverse(
                    "horizon:project:data_processing.clusters:cluster-details",
                    args=(http.urlquote(job_execution.cluster_id),))
            else:
                # No link should be generated for a deleted Cluster.
                return None

        def get_data(self, job_execution):
            return job_execution.cluster_name or _("Not available")

    class DurationColumn(tables.Column):

        def get_data(self, job_execution):
            status = job_execution.info["status"]

            end_time = None
            if status in [k for k, v in JobsTable.STATUS_CHOICES]:
                end_time = job_execution.updated_at

            return helpers.Helpers(None).get_duration(job_execution.created_at,
                                                      end_time)

    STATUS_CHOICES = (
        ("DONEWITHERROR", False),
        ("FAILED", False),
        ("KILLED", False),
        ("SUCCEEDED", True),
    )
    STATUS_DISPLAY_CHOICES = (
        ("DONEWITHERROR", pgettext_lazy("Current status of a Job",
                                        u"Done with Error")),
        ("FAILED", pgettext_lazy("Current status of a Job",
                                 u"Failed")),
        ("KILLED", pgettext_lazy("Current status of a Job",
                                 u"Killed")),
        ("SUCCEEDED", pgettext_lazy("Current status of a Job",
                                    u"Succeeded")),
    )

    name = tables.Column("id",
                         verbose_name=_("ID"),
                         display_choices=(("id", "ID"),
                                          ("name", pgettext_lazy("Name")),),
                         link=("horizon:project:data_processing."
                               "jobs:details"))
    job_name = JobNameColumn(
        "job_name",
        verbose_name=_("Job Template"),
        link=JobNameColumn.link)

    cluster_name = ClusterNameColumn(
        "cluster_name",
        verbose_name=_("Cluster"),
        link=ClusterNameColumn.link)

    status = StatusColumn("info",
                          status=True,
                          status_choices=STATUS_CHOICES,
                          display_choices=STATUS_DISPLAY_CHOICES,
                          verbose_name=_("Status"))

    duration = DurationColumn("duration",
                              verbose_name=_("Duration"))

    def get_object_display(self, datum):
        return datum.id

    class Meta(object):
        name = "jobs"
        row_class = UpdateRow
        status_columns = ["status"]
        verbose_name = _("Jobs")
        table_actions = [JobExecutionGuide,
                         DeleteJob,
                         JobsFilterAction]

        table_actions_menu = [MakePublic, MakePrivate,
                              MakeProtected, MakeUnProtected]
        row_actions = [DeleteJob,
                       ReLaunchJobExistingCluster,
                       ReLaunchJobNewCluster,
                       MakePublic, MakePrivate,
                       MakeProtected, MakeUnProtected]

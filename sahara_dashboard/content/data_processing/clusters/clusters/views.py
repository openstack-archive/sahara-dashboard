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

import json

from django.http import HttpResponse
from django.urls import reverse
from django.utils.translation import ugettext as _
from django.views.generic import base as django_base
from oslo_utils import timeutils
from saharaclient.api.base import APIException

from horizon import exceptions
from horizon import tabs
from horizon.utils import memoized
from horizon import workflows

from sahara_dashboard.api import sahara as saharaclient
import sahara_dashboard.content.data_processing.clusters.clusters. \
    tables as c_tables
import sahara_dashboard.content.data_processing.clusters.clusters. \
    tabs as _tabs
import sahara_dashboard.content.data_processing.clusters.clusters. \
    workflows.create as create_flow
import sahara_dashboard.content.data_processing.clusters.clusters. \
    workflows.scale as scale_flow
import sahara_dashboard.content.data_processing.clusters.clusters. \
    workflows.update as update_flow
import sahara_dashboard.content.data_processing.utils.helpers as helpers


class ClusterDetailsView(tabs.TabView):
    tab_group_class = _tabs.ClusterDetailsTabs
    template_name = 'horizon/common/_detail.html'
    page_title = "{{ cluster.name|default:cluster.id }}"

    @memoized.memoized_method
    def get_object(self):
        cl_id = self.kwargs["cluster_id"]
        try:
            return saharaclient.cluster_get(self.request, cl_id)
        except Exception:
            msg = _('Unable to retrieve details for cluster "%s".') % cl_id
            redirect = self.get_redirect_url()
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super(ClusterDetailsView, self).get_context_data(**kwargs)
        cluster = self.get_object()
        context['cluster'] = cluster
        context['url'] = self.get_redirect_url()
        context['actions'] = self._get_actions(cluster)
        return context

    def _get_actions(self, cluster):
        table = c_tables.ClustersTable(self.request)
        return table.render_row_actions(cluster)

    @staticmethod
    def get_redirect_url():
        return reverse("horizon:project:data_processing.clusters:index")


class ClusterEventsView(django_base.View):

    @staticmethod
    def _created_at_key(obj):
        return timeutils.parse_isotime(obj["created_at"])

    def get(self, request, *args, **kwargs):

        cluster_id = kwargs.get("cluster_id")
        time_helpers = helpers.Helpers(request)

        try:
            cluster = saharaclient.cluster_get(request, cluster_id,
                                               show_progress=True)
            node_group_mapping = {}
            for node_group in cluster.node_groups:
                node_group_mapping[node_group["id"]] = node_group["name"]

            provision_steps = cluster.provision_progress

            # Sort by create time
            provision_steps = sorted(provision_steps,
                                     key=ClusterEventsView._created_at_key,
                                     reverse=True)

            for step in provision_steps:
                # Sort events of the steps also
                step["events"] = sorted(step["events"],
                                        key=ClusterEventsView._created_at_key,
                                        reverse=True)

                successful_events_count = 0

                for event in step["events"]:
                    if event["node_group_id"]:
                        event["node_group_name"] = node_group_mapping[
                            event["node_group_id"]]

                    event_result = _("Unknown")
                    if event["successful"] is True:
                        successful_events_count += 1
                        event_result = _("Completed Successfully")
                    elif event["successful"] is False:
                        event_result = _("Failed")

                    event["result"] = event_result

                    if not event["event_info"]:
                        event["event_info"] = _("No info available")

                step["duration"] = time_helpers.get_duration(
                    step["created_at"],
                    step["updated_at"])
                step['started_at'] = time_helpers.to_time_zone(
                    step["created_at"], localize=True)
                result = _("In progress")
                step["completed"] = successful_events_count

                if step["successful"] is True:
                    step["completed"] = step["total"]
                    result = _("Completed Successfully")
                elif step["successful"] is False:
                    result = _("Failed")

                step["result"] = result

            status = cluster.status.lower()
            need_update = status not in ("active", "error")
        except APIException:
            # Cluster is not available. Returning empty event log.
            need_update = False
            provision_steps = []

        context = {"provision_steps": provision_steps,
                   "need_update": need_update}

        return HttpResponse(json.dumps(context),
                            content_type='application/json')


class ClusterHealthChecksView(django_base.View):
    _date_format = "%Y-%m-%dT%H:%M:%S"
    _status_in_progress = 'CHECKING'

    def _get_checks(self, cluster):
        try:
            return cluster.verification['checks']
        except (AttributeError, KeyError):
            return []

    def get(self, request, *args, **kwargs):

        time_helpers = helpers.Helpers(request)
        cluster_id = kwargs.get("cluster_id")
        need_update, not_done_count, checks = False, 0, []
        mapping_to_label_type = {'red': 'danger', 'yellow': 'warning',
                                 'green': 'success', 'checking': 'info'}
        try:
            cluster = saharaclient.cluster_get(request, cluster_id)
            for check in self._get_checks(cluster):
                check['label'] = mapping_to_label_type.get(
                    check['status'].lower())

                if not check['description']:
                    check['description'] = _("No description")

                if check['status'] == self._status_in_progress:
                    not_done_count += 1
                check['duration'] = time_helpers.get_duration(
                    check['created_at'], check['updated_at'])
                checks.append(check)
        except APIException:
            need_update = False
            checks = []
        if not_done_count > 0:
            need_update = True
        context = {"checks": checks,
                   "need_update": need_update}

        return HttpResponse(json.dumps(context),
                            content_type='application/json')


class CreateClusterView(workflows.WorkflowView):
    workflow_class = create_flow.CreateCluster
    success_url = \
        "horizon:project:data_processing.clusters:create-cluster"
    classes = ("ajax-modal",)
    template_name = "clusters/create.html"
    page_title = _("Launch Cluster")


class ConfigureClusterView(workflows.WorkflowView):
    workflow_class = create_flow.ConfigureCluster
    success_url = "horizon:project:data_processing.clusters:index"
    template_name = "clusters/configure.html"
    page_title = _("Configure Cluster")

    def get_initial(self):
        initial = super(ConfigureClusterView, self).get_initial()
        initial.update(self.kwargs)
        return initial


class ScaleClusterView(workflows.WorkflowView):
    workflow_class = scale_flow.ScaleCluster
    success_url = "horizon:project:data_processing.clusters:index"
    classes = ("ajax-modal",)
    template_name = "clusters/scale.html"
    page_title = _("Scale Cluster")

    def get_context_data(self, **kwargs):
        context = super(ScaleClusterView, self)\
            .get_context_data(**kwargs)

        context["cluster_id"] = kwargs["cluster_id"]
        return context

    def get_object(self, *args, **kwargs):
        if not hasattr(self, "_object"):
            template_id = self.kwargs['cluster_id']
            try:
                template = saharaclient.cluster_template_get(self.request,
                                                             template_id)
            except Exception:
                template = None
                exceptions.handle(self.request,
                                  _("Unable to fetch cluster template."))
            self._object = template
        return self._object

    def get_initial(self):
        initial = super(ScaleClusterView, self).get_initial()
        initial.update({'cluster_id': self.kwargs['cluster_id']})
        return initial


class UpdateClusterSharesView(workflows.WorkflowView):
    workflow_class = update_flow.UpdateShares
    success_url = "horizon:project:data_processing.clusters"
    classes = ("ajax-modal",)
    template_name = "clusters/update.html"
    page_title = _("Update Cluster Shares")

    def get_context_data(self, **kwargs):
        context = super(UpdateClusterSharesView, self)\
            .get_context_data(**kwargs)
        context["cluster_id"] = kwargs["cluster_id"]
        return context

    def get_object(self, *args, **kwargs):
        if not hasattr(self, "_object"):
            cluster_id = self.kwargs['cluster_id']
            try:
                cluster = saharaclient.cluster_get(self.request, cluster_id)
            except Exception:
                cluster = None
                exceptions.handle(self.request,
                                  _("Unable to fetch cluster."))
            self._object = cluster
        return self._object

    def get_initial(self):
        initial = super(UpdateClusterSharesView, self).get_initial()
        initial.update({
            'cluster_id': self.kwargs['cluster_id'],
            'cluster': self.get_object()})
        return initial

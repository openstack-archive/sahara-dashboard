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

from django.utils.translation import ugettext_lazy as _
from saharaclient.api import base as api_base

from horizon import exceptions
from horizon import forms
from horizon import workflows

from sahara_dashboard.api import manila as manilaclient
from sahara_dashboard.api import sahara as saharaclient
import sahara_dashboard.content.data_processing. \
    utils.workflow_helpers as whelpers


class SelectSharesAction(workflows.Action):
    def __init__(self, request, *args, **kwargs):
        super(SelectSharesAction, self).__init__(
            request, *args, **kwargs)

        possible_shares = self.get_possible_shares(request)

        cluster_id = [x["cluster_id"] for x in args if "cluster_id" in x][0]
        self.fields["cluster_id"] = forms.CharField(
            widget=forms.HiddenInput(),
            initial=cluster_id)

        self.fields["shares"] = whelpers.MultipleShareChoiceField(
            label=_("Select Shares"),
            widget=whelpers.ShareWidget(choices=possible_shares),
            required=False,
            choices=possible_shares,
        )

        cluster = [x["cluster"] for x in args if "cluster" in x][0]
        self.fields["shares"].initial = (
            self._get_share_defaults(cluster.shares,
                                     self.fields["shares"]))

    def _get_share_defaults(self, cluster_shares, share_field):
        values = dict()
        choices = share_field.choices
        for i, choice in enumerate(choices):
            share_id = choice[0]
            s = [s for s in cluster_shares if s['id'] == share_id]
            if len(s) > 0:
                path = s[0]["path"] if "path" in s[0] else ""
                values["share_id_{0}".format(i)] = {
                    "id": s[0]["id"],
                    "path": path,
                    "access_level": s[0]["access_level"]
                }
            else:
                values["share_id_{0}".format(i)] = {
                    "id": None,
                    "path": None,
                    "access_level": None
                }
        return values

    def get_possible_shares(self, request):
        try:
            shares = manilaclient.share_list(request)
            choices = [(s.id, s.name) for s in shares]
        except Exception:
            exceptions.handle(request, _("Failed to get list of shares"))
            choices = []
        return choices

    def clean(self):
        cleaned_data = super(SelectSharesAction, self).clean()
        self._errors = dict()
        return cleaned_data

    class Meta(object):
        name = _("Shares")
        help_text = _("Select the manila shares for this cluster")


class SelectShares(workflows.Step):
    action_class = SelectSharesAction
    depends_on = ("cluster_id", "cluster")

    def contribute(self, data, context):
        post = self.workflow.request.POST
        shares_details = []
        for index in range(0, len(self.action.fields['shares'].choices) * 3):
            if index % 3 == 0:
                share = post.get("shares_{0}".format(index))
                if share:
                    path = post.get("shares_{0}".format(index + 1))
                    permissions = post.get("shares_{0}".format(index + 2))
                    shares_details.append({
                        "id": share,
                        "path": path,
                        "access_level": permissions
                    })
        context['cluster_shares'] = shares_details
        return context


class UpdateShares(workflows.Workflow):
    slug = "update_cluster_shares"
    name = _("Update Cluster Shares")
    success_message = _("Updated")
    failure_message = _("Could not update cluster shares")
    success_url = "horizon:project:data_processing.clusters:index"
    default_steps = (SelectShares,)

    def handle(self, request, context):
        try:
            saharaclient.cluster_update_shares(
                request, context["cluster_id"], context["cluster_shares"])
            return True
        except api_base.APIException as e:
            self.error_description = str(e)
            return False
        except Exception:
            exceptions.handle(request,
                              _("Cluster share update failed."))
            return False

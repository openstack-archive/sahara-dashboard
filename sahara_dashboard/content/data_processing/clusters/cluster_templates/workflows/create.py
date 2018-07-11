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

from django import urls
from django.utils.translation import ugettext_lazy as _
from saharaclient.api import base as api_base

from horizon import exceptions
from horizon import forms
from horizon import workflows

from sahara_dashboard.api import designate as designateclient
from sahara_dashboard.api import manila as manilaclient
from sahara_dashboard.api import sahara as saharaclient
from sahara_dashboard.content.data_processing.utils import helpers
from sahara_dashboard.content.data_processing. \
    utils import anti_affinity as aa
from sahara_dashboard.content.data_processing.utils \
    import acl as acl_utils
import sahara_dashboard.content.data_processing. \
    utils.workflow_helpers as whelpers
from sahara_dashboard import utils


class SelectPluginAction(workflows.Action,
                         whelpers.PluginAndVersionMixin):
    hidden_create_field = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={"class": "hidden_create_field"}))

    def __init__(self, request, *args, **kwargs):
        super(SelectPluginAction, self).__init__(request, *args, **kwargs)

        sahara = saharaclient.client(request)
        self._generate_plugin_version_fields(sahara)

    class Meta(object):
        name = _("Select plugin and hadoop version for cluster template")
        help_text_template = ("cluster_templates/"
                              "_create_general_help.html")


class SelectPlugin(workflows.Step):
    action_class = SelectPluginAction


class CreateClusterTemplate(workflows.Workflow):
    slug = "create_cluster_template"
    name = _("Create Cluster Template")
    finalize_button_name = _("Next")
    success_message = _("Created")
    failure_message = _("Could not create")
    success_url = "horizon:project:data_processing.clusters:clusters-tab"
    default_steps = (SelectPlugin, )

    def get_success_url(self):
        url = urls.reverse(self.success_url)
        return url


class GeneralConfigAction(workflows.Action):
    hidden_configure_field = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={"class": "hidden_configure_field"}))

    hidden_to_delete_field = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={"class": "hidden_to_delete_field"}))

    cluster_template_name = forms.CharField(label=_("Template Name"))

    description = forms.CharField(label=_("Description"),
                                  required=False,
                                  widget=forms.Textarea(attrs={'rows': 4}))

    use_autoconfig = forms.BooleanField(
        label=_("Auto-configure"),
        help_text=_("If selected, instances of a cluster will be "
                    "automatically configured during creation. Otherwise you "
                    "should manually specify configuration values"),
        required=False,
        widget=forms.CheckboxInput(),
        initial=True,
    )

    is_public = acl_utils.get_is_public_form(_("cluster template"))
    is_protected = acl_utils.get_is_protected_form(_("cluster template"))

    anti_affinity = aa.anti_affinity_field()

    def __init__(self, request, *args, **kwargs):
        super(GeneralConfigAction, self).__init__(request, *args, **kwargs)
        plugin, hadoop_version = whelpers.\
            get_plugin_and_hadoop_version(request)

        self.fields["plugin_name"] = forms.CharField(
            widget=forms.HiddenInput(),
            initial=plugin
        )
        self.fields["hadoop_version"] = forms.CharField(
            widget=forms.HiddenInput(),
            initial=hadoop_version
        )

    populate_anti_affinity_choices = aa.populate_anti_affinity_choices

    def get_help_text(self):
        extra = dict()
        plugin_name, hadoop_version = whelpers\
            .get_plugin_and_hadoop_version(self.request)

        extra["plugin_name"] = plugin_name
        extra["hadoop_version"] = hadoop_version

        plugin = saharaclient.plugin_get_version_details(
            self.request, plugin_name, hadoop_version)
        extra["deprecated"] = whelpers.is_version_of_plugin_deprecated(
            plugin, hadoop_version)
        return super(GeneralConfigAction, self).get_help_text(extra)

    def clean(self):
        cleaned_data = super(GeneralConfigAction, self).clean()
        if cleaned_data.get("hidden_configure_field", None) \
                == "create_nodegroup":
            self._errors = dict()
        return cleaned_data

    class Meta(object):
        name = _("Details")
        help_text_template = ("cluster_templates/_configure_general_help.html")


class GeneralConfig(workflows.Step):
    action_class = GeneralConfigAction
    contributes = ("hidden_configure_field", )

    def contribute(self, data, context):
        for k, v in data.items():
            context["general_" + k] = v

        post = self.workflow.request.POST
        context['anti_affinity_info'] = post.getlist("anti_affinity")
        return context


class ConfigureNodegroupsAction(workflows.Action):
    hidden_nodegroups_field = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={"class": "hidden_nodegroups_field"}))
    forms_ids = forms.CharField(
        required=False,
        widget=forms.HiddenInput())

    def __init__(self, request, *args, **kwargs):
        super(ConfigureNodegroupsAction, self). \
            __init__(request, *args, **kwargs)
        # when we copy or edit a cluster template then
        # request contains valuable info in both GET and POST methods
        req = request.GET.copy()
        req.update(request.POST)
        plugin = req.get("plugin_name")
        version = req.get("hadoop_version", None) or req["plugin_version"]
        if plugin and not version:
            version_name = plugin + "_version"
            version = req.get(version_name)

        if not plugin or not version:
            self.templates = saharaclient.nodegroup_template_find(request)
        else:
            self.templates = saharaclient.nodegroup_template_find(
                request, plugin_name=plugin, hadoop_version=version)

        deletable = req.get("deletable", dict())

        if 'forms_ids' in req:
            self.groups = []
            for id in json.loads(req['forms_ids']):
                group_name = "group_name_" + str(id)
                template_id = "template_id_" + str(id)
                count = "count_" + str(id)
                serialized = "serialized_" + str(id)
                self.groups.append({"name": req[group_name],
                                    "template_id": req[template_id],
                                    "count": req[count],
                                    "id": id,
                                    "deletable": deletable.get(
                                        req[group_name], "true"),
                                    "serialized": req[serialized]})

                whelpers.build_node_group_fields(self,
                                                 group_name,
                                                 template_id,
                                                 count,
                                                 serialized)

    def clean(self):
        cleaned_data = super(ConfigureNodegroupsAction, self).clean()
        if cleaned_data.get("hidden_nodegroups_field", None) \
                == "create_nodegroup":
            self._errors = dict()
        return cleaned_data

    class Meta(object):
        name = _("Node Groups")


class ConfigureNodegroups(workflows.Step):
    action_class = ConfigureNodegroupsAction
    contributes = ("hidden_nodegroups_field", )
    template_name = ("cluster_templates/cluster_node_groups_template.html")

    def contribute(self, data, context):
        for k, v in data.items():
            context["ng_" + k] = v
        return context


class SelectClusterSharesAction(workflows.Action):
    def __init__(self, request, *args, **kwargs):
        super(SelectClusterSharesAction, self).__init__(
            request, *args, **kwargs)

        possible_shares = self.get_possible_shares(request)

        self.fields["shares"] = whelpers.MultipleShareChoiceField(
            label=_("Select Shares"),
            widget=whelpers.ShareWidget(choices=possible_shares),
            required=False,
            choices=possible_shares
        )

    def get_possible_shares(self, request):
        try:
            shares = manilaclient.share_list(request)
            choices = [(s.id, s.name) for s in shares]
        except Exception:
            exceptions.handle(request, _("Failed to get list of shares"))
            choices = []
        return choices

    def clean(self):
        cleaned_data = super(SelectClusterSharesAction, self).clean()
        self._errors = dict()
        return cleaned_data

    class Meta(object):
        name = _("Shares")
        help_text = _("Select the manila shares for this cluster")


class SelectClusterShares(workflows.Step):
    action_class = SelectClusterSharesAction

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
        context['ct_shares'] = shares_details
        return context


class SelectDnsDomainsAction(workflows.Action):
    domain_name = forms.DynamicChoiceField(
        label=_("Domain Name"),
        required=False
    )

    def __init__(self, request, *args, **kwargs):
        super(SelectDnsDomainsAction, self).__init__(request, *args, **kwargs)

    def _get_domain_choices(self, request):
        domains = designateclient.get_domain_names(request)
        choices = [(None, _('No domain is specified'))]
        choices.extend(
            [(domain.get('name'), domain.get('name')) for domain in domains])
        return choices

    def populate_domain_name_choices(self, request, context):
        return self._get_domain_choices(request)

    class Meta(object):
        name = _("DNS Domain Names")
        help_text_template = (
            "cluster_templates/_config_domain_names_help.html")


class SelectDnsDomains(workflows.Step):
    action_class = SelectDnsDomainsAction

    def contribute(self, data, context):
        for k, v in data.items():
            context["dns_" + k] = v
        return context


class ConfigureClusterTemplate(whelpers.ServiceParametersWorkflow,
                               whelpers.StatusFormatMixin):
    slug = "configure_cluster_template"
    name = _("Create Cluster Template")
    finalize_button_name = _("Create")
    success_message = _("Created Cluster Template %s")
    name_property = "general_cluster_template_name"
    success_url = ("horizon:project:data_processing.clusters:"
                   "cluster-templates-tab")
    default_steps = (GeneralConfig,
                     ConfigureNodegroups)

    def __init__(self, request, context_seed, entry_point, *args, **kwargs):
        ConfigureClusterTemplate._cls_registry = []

        hlps = helpers.Helpers(request)
        plugin, hadoop_version = whelpers.\
            get_plugin_and_hadoop_version(request)
        general_parameters = hlps.get_cluster_general_configs(
            plugin,
            hadoop_version)
        service_parameters = hlps.get_targeted_cluster_configs(
            plugin,
            hadoop_version)

        if saharaclient.base.is_service_enabled(request, 'share'):
            ConfigureClusterTemplate._register_step(self, SelectClusterShares)

        if saharaclient.base.is_service_enabled(request, 'dns'):
            ConfigureClusterTemplate._register_step(self, SelectDnsDomains)

        self._populate_tabs(general_parameters, service_parameters)

        super(ConfigureClusterTemplate, self).__init__(request,
                                                       context_seed,
                                                       entry_point,
                                                       *args, **kwargs)

    def is_valid(self):
        steps_valid = True
        for step in self.steps:
            if not step.action.is_valid():
                steps_valid = False
                step.has_errors = True
                errors_fields = list(step.action.errors.keys())
                step.action.errors_fields = errors_fields
        if not steps_valid:
            return steps_valid
        return self.validate(self.context)

    def handle(self, request, context):
        try:
            node_groups = []
            configs_dict = whelpers.parse_configs_from_context(context,
                                                               self.defaults)

            ids = json.loads(context['ng_forms_ids'])
            for id in ids:
                name = context['ng_group_name_' + str(id)]
                template_id = context['ng_template_id_' + str(id)]
                count = context['ng_count_' + str(id)]

                raw_ng = context.get("ng_serialized_" + str(id))

                if raw_ng and raw_ng != 'null':
                    ng = json.loads(utils.deserialize(str(raw_ng)))
                else:
                    ng = dict()
                ng["name"] = name
                ng["count"] = count
                if template_id and template_id != u'None':
                    ng["node_group_template_id"] = template_id
                node_groups.append(ng)

            plugin, hadoop_version = whelpers.\
                get_plugin_and_hadoop_version(request)

            ct_shares = []
            if "ct_shares" in context:
                ct_shares = context["ct_shares"]

            domain = context.get('dns_domain_name', None)
            if domain == 'None':
                domain = None

            # TODO(nkonovalov): Fix client to support default_image_id
            saharaclient.cluster_template_create(
                request,
                context["general_cluster_template_name"],
                plugin,
                hadoop_version,
                context["general_description"],
                configs_dict,
                node_groups,
                context["anti_affinity_info"],
                use_autoconfig=context['general_use_autoconfig'],
                shares=ct_shares,
                is_public=context['general_is_public'],
                is_protected=context['general_is_protected'],
                domain_name=domain
            )

            hlps = helpers.Helpers(request)
            if hlps.is_from_guide():
                request.session["guide_cluster_template_name"] = (
                    context["general_cluster_template_name"])
                self.success_url = (
                    "horizon:project:data_processing.clusters:cluster_guide")
            return True
        except api_base.APIException as e:
            self.error_description = str(e)
            return False
        except Exception:
            exceptions.handle(request,
                              _("Cluster template creation failed"))
            return False

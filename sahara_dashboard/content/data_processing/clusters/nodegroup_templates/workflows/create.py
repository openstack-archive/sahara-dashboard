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

import itertools

from django.utils import encoding
from django.utils import html
from django.utils import safestring
from django.utils.translation import ugettext_lazy as _
from oslo_log import log as logging
from oslo_utils import uuidutils
from saharaclient.api import base as api_base

from horizon import exceptions
from horizon import forms
from horizon import workflows
from openstack_dashboard.api import cinder
from openstack_dashboard.api import neutron
from openstack_dashboard.api import nova
from openstack_dashboard.dashboards.project.instances \
    import utils as nova_utils

from sahara_dashboard.api import manila as manilaclient
from sahara_dashboard.api import sahara as saharaclient
from sahara_dashboard.content.data_processing.utils \
    import acl as acl_utils
from sahara_dashboard.content.data_processing.utils \
    import helpers
from sahara_dashboard.content.data_processing.utils \
    import workflow_helpers

LOG = logging.getLogger(__name__)

BASE_IMAGE_URL = "horizon:project:data_processing.clusters:register"


def is_cinder_enabled(request):
    for service in ['volumev3', 'volumev2', 'volume']:
        if saharaclient.base.is_service_enabled(request, service):
            return True
    return False


def storage_choices(request):
    choices = [("ephemeral_drive", _("Ephemeral Drive")), ]
    if is_cinder_enabled(request):
        choices.append(("cinder_volume", _("Cinder Volume")))
    else:
        LOG.warning(_("Cinder service is unavailable now"))
    return choices


def volume_availability_zone_list(request):
    """Utility method to retrieve a list of volume availability zones."""
    try:
        if cinder.extension_supported(request, 'AvailabilityZones'):
            return cinder.availability_zone_list(request)
        return []
    except Exception:
        exceptions.handle(request,
                          _('Unable to retrieve volumes availability zones.'))
        return []


def instance_availability_zone_list(request):
    """Utility method to retrieve a list of instance availability zones."""
    try:
        return nova.availability_zone_list(request)
    except Exception:
        exceptions.handle(request,
                          _('Unable to retrieve Nova availability zones.'))
        return []


class GeneralConfigAction(workflows.Action):
    nodegroup_name = forms.CharField(label=_("Template Name"))

    description = forms.CharField(label=_("Description"),
                                  required=False,
                                  widget=forms.Textarea(attrs={'rows': 4}))

    flavor = forms.ChoiceField(label=_("OpenStack Flavor"))

    availability_zone = forms.ChoiceField(
        label=_("Availability Zone"),
        help_text=_("Launch instances in this availability zone."),
        required=False,
        widget=forms.Select(attrs={"class": "availability_zone_field"})
    )

    storage = forms.ChoiceField(
        label=_("Attached storage location"),
        help_text=_("Choose a storage location"),
        choices=[],
        widget=forms.Select(attrs={
            "class": "storage_field switchable",
            'data-slug': 'storage_loc'
        }))

    volumes_per_node = forms.IntegerField(
        label=_("Volumes per node"),
        required=False,
        initial=1,
        widget=forms.TextInput(attrs={
            "class": "volume_per_node_field switched",
            "data-switch-on": "storage_loc",
            "data-storage_loc-cinder_volume": _('Volumes per node')
        })
    )

    volumes_size = forms.IntegerField(
        label=_("Volumes size (GB)"),
        required=False,
        initial=10,
        widget=forms.TextInput(attrs={
            "class": "volume_size_field switched",
            "data-switch-on": "storage_loc",
            "data-storage_loc-cinder_volume": _('Volumes size (GB)')
        })
    )

    volume_type = forms.ChoiceField(
        label=_("Volumes type"),
        required=False,
        widget=forms.Select(attrs={
            "class": "volume_type_field switched",
            "data-switch-on": "storage_loc",
            "data-storage_loc-cinder_volume": _('Volumes type')
        })
    )

    volume_local_to_instance = forms.BooleanField(
        label=_("Volume local to instance"),
        required=False,
        help_text=_("Instance and attached volumes will be created on the "
                    "same physical host"),
        widget=forms.CheckboxInput(attrs={
            "class": "volume_local_to_instance_field switched",
            "data-switch-on": "storage_loc",
            "data-storage_loc-cinder_volume": _('Volume local to instance')
        })
    )

    volumes_availability_zone = forms.ChoiceField(
        label=_("Volumes Availability Zone"),
        help_text=_("Create volumes in this availability zone."),
        required=False,
        widget=forms.Select(attrs={
            "class": "volumes_availability_zone_field switched",
            "data-switch-on": "storage_loc",
            "data-storage_loc-cinder_volume": _('Volumes Availability Zone')
        })
    )

    image = forms.DynamicChoiceField(label=_("Base Image"),
                                     required=False,
                                     add_item_link=BASE_IMAGE_URL)

    hidden_configure_field = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={"class": "hidden_configure_field"}))

    def __init__(self, request, *args, **kwargs):
        super(GeneralConfigAction, self).__init__(request, *args, **kwargs)

        hlps = helpers.Helpers(request)

        plugin, hadoop_version = (
            workflow_helpers.get_plugin_and_hadoop_version(request))

        if not saharaclient.SAHARA_FLOATING_IP_DISABLED:
            pools = neutron.floating_ip_pools_list(request)
            pool_choices = [(pool.id, pool.name) for pool in pools]
            pool_choices.insert(0, (None, "Do not assign floating IPs"))

            self.fields['floating_ip_pool'] = forms.ChoiceField(
                label=_("Floating IP Pool"),
                choices=pool_choices,
                required=False)

        self.fields["use_autoconfig"] = forms.BooleanField(
            label=_("Auto-configure"),
            help_text=_("If selected, instances of a node group will be "
                        "automatically configured during cluster "
                        "creation. Otherwise you should manually specify "
                        "configuration values."),
            required=False,
            widget=forms.CheckboxInput(),
            initial=True,
        )

        self.fields["proxygateway"] = forms.BooleanField(
            label=_("Proxy Gateway"),
            widget=forms.CheckboxInput(),
            help_text=_("Sahara will use instances of this node group to "
                        "access other cluster instances."),
            required=False)

        self.fields['is_public'] = acl_utils.get_is_public_form(
            _("node group template"))
        self.fields['is_protected'] = acl_utils.get_is_protected_form(
            _("node group template"))

        if saharaclient.VERSIONS.active == '2':
            self.fields['boot_storage'] = forms.ChoiceField(
                label=_("Boot storage location"),
                help_text=_("Choose a boot mode"),
                choices=storage_choices(request),
                widget=forms.Select(attrs={
                    "class": "boot_storage_field switchable",
                    'data-slug': 'boot_storage_loc'
                }))

            self.fields['boot_volume_type'] = forms.ChoiceField(
                label=_("Boot volume type"),
                required=False,
                widget=forms.Select(attrs={
                    "class": "boot_volume_type_field switched",
                    "data-switch-on": "boot_storage_loc",
                    "data-boot_storage_loc-cinder_volume":
                        _('Boot volume type')
                })
            )

            self.fields['boot_volume_local_to_instance'] = forms.BooleanField(
                label=_("Boot volume local to instance"),
                required=False,
                help_text=_("Boot volume locality"),
                widget=forms.CheckboxInput(attrs={
                    "class": "boot_volume_local_to_instance_field switched",
                    "data-switch-on": "boot_storage_loc",
                    "data-boot_storage_loc-cinder_volume":
                        _('Boot volume local to instance')
                })
            )

            self.fields['boot_volume_availability_zone'] = forms.ChoiceField(
                label=_("Boot volume availability Zone"),
                choices=self.populate_volumes_availability_zone_choices(
                    request, None),
                help_text=_("Create boot volume in this availability zone."),
                required=False,
                widget=forms.Select(attrs={
                    "class": "boot_volume_availability_zone_field switched",
                    "data-switch-on": "boot_storage_loc",
                    "data-boot_storage_loc-cinder_volume":
                        _('Boot volume availability zone')
                })
            )

        self.fields["plugin_name"] = forms.CharField(
            widget=forms.HiddenInput(),
            initial=plugin
        )
        self.fields["hadoop_version"] = forms.CharField(
            widget=forms.HiddenInput(),
            initial=hadoop_version
        )

        self.fields["storage"].choices = storage_choices(request)

        node_parameters = hlps.get_general_node_group_configs(plugin,
                                                              hadoop_version)
        for param in node_parameters:
            self.fields[param.name] = workflow_helpers.build_control(param)

        # when we copy or edit a node group template then
        # request contains valuable info in both GET and POST methods
        req = request.GET.copy()
        req.update(request.POST)
        if req.get("guide_template_type"):
            self.fields["guide_template_type"] = forms.CharField(
                required=False,
                widget=forms.HiddenInput(),
                initial=req.get("guide_template_type"))

        if is_cinder_enabled(request):
            volume_types = cinder.volume_type_list(request)
        else:
            volume_types = []

        self.fields['volume_type'].choices = [(None, _("No volume type"))] + \
                                             [(type.name, type.name)
                                              for type in volume_types]

        if saharaclient.VERSIONS.active == '2':
            self.fields['boot_volume_type'].choices = (
                self.fields['volume_type'].choices)

    def populate_flavor_choices(self, request, context):
        flavors = nova_utils.flavor_list(request)
        if flavors:
            return nova_utils.sort_flavor_list(request, flavors)
        return []

    def populate_availability_zone_choices(self, request, context):
        # The default is None, i.e. not specifying any availability zone
        az_list = [(None, _('No availability zone specified'))]
        az_list.extend([(az.zoneName, az.zoneName)
                        for az in instance_availability_zone_list(request)
                        if az.zoneState['available']])
        return az_list

    def populate_volumes_availability_zone_choices(self, request, context):
        az_list = [(None, _('No availability zone specified'))]
        if is_cinder_enabled(request):
            az_list.extend([(az.zoneName, az.zoneName)
                            for az in volume_availability_zone_list(
                                request) if az.zoneState['available']])
        return az_list

    def populate_image_choices(self, request, context):
        return workflow_helpers.populate_image_choices(self, request, context,
                                                       empty_choice=True)

    def get_help_text(self):
        extra = dict()
        plugin_name, hadoop_version = (
            workflow_helpers.get_plugin_and_hadoop_version(self.request))
        extra["plugin_name"] = plugin_name
        extra["hadoop_version"] = hadoop_version
        plugin = saharaclient.plugin_get_version_details(
            self.request, plugin_name, hadoop_version)
        extra["deprecated"] = workflow_helpers.is_version_of_plugin_deprecated(
            plugin, hadoop_version)
        return super(GeneralConfigAction, self).get_help_text(extra)

    class Meta(object):
        name = _("Configure Node Group Template")
        help_text_template = "nodegroup_templates/_configure_general_help.html"


class SecurityConfigAction(workflows.Action):
    def __init__(self, request, *args, **kwargs):
        super(SecurityConfigAction, self).__init__(request, *args, **kwargs)

        self.fields["security_autogroup"] = forms.BooleanField(
            label=_("Auto Security Group"),
            widget=forms.CheckboxInput(),
            help_text=_("Create security group for this Node Group."),
            required=False,
            initial=True)

        try:
            groups = neutron.security_group_list(request)
        except Exception:
            exceptions.handle(request,
                              _("Unable to get security group list."))
            raise

        security_group_list = [(sg.id, sg.name) for sg in groups]
        self.fields["security_groups"] = forms.MultipleChoiceField(
            label=_("Security Groups"),
            widget=forms.CheckboxSelectMultiple(),
            help_text=_("Launch instances in these security groups."),
            choices=security_group_list,
            required=False)

    class Meta(object):
        name = _("Security")
        help_text = _("Control access to instances of the node group.")


class CheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    # TODO(shuyingya): should rewrite this class using the
    # new method "get_context" when Django version less than 1.11
    # no longer support.
    def build_attrs(self, extra_attrs=None, **kwargs):
        "Helper function for building an attribute dictionary."
        attrs = dict(self.attrs, **kwargs)
        if extra_attrs:
            attrs.update(extra_attrs)
        return attrs

    def render(self, name, value, attrs=None, choices=(), renderer=None):
        if value is None:
            value = []
        has_id = attrs and 'id' in attrs
        final_attrs = self.build_attrs(attrs, name=name)
        output = []
        initial_service = uuidutils.generate_uuid()
        str_values = set([encoding.force_text(v) for v in value])
        for i, (option_value, option_label) in enumerate(
                itertools.chain(self.choices, choices)):
            current_service = option_value.split(':')[0]
            if current_service != initial_service:
                if i > 0:
                    output.append("</ul>")
                service_description = _("%s processes: ") % current_service
                service_description = html.conditional_escape(
                    encoding.force_text(service_description))
                output.append("<label>%s</label>" % service_description)
                initial_service = current_service
                output.append(encoding.force_text("<ul>"))
            if has_id:
                final_attrs = dict(final_attrs, id='%s_%s' % (attrs['id'], i))
                label_for = ' for="%s"' % final_attrs['id']
            else:
                label_for = ''

            cb = forms.CheckboxInput(
                final_attrs, check_test=lambda value: value in str_values)
            option_value = encoding.force_text(option_value)
            rendered_cb = cb.render(name, option_value)
            option_label = html.conditional_escape(
                encoding.force_text(option_label))
            output.append(
                '<li><label%s>%s %s</label></li>' %
                (label_for, rendered_cb, option_label))
        output.append('</ul>')
        return safestring.mark_safe('\n'.join(output))


class SelectNodeProcessesAction(workflows.Action):
    def __init__(self, request, *args, **kwargs):
        super(SelectNodeProcessesAction, self).__init__(
            request, *args, **kwargs)

        plugin, hadoop_version = (
            workflow_helpers.get_plugin_and_hadoop_version(request))
        node_processes = {}
        try:
            version_details = saharaclient.plugin_get_version_details(
                request, plugin, hadoop_version)
            node_processes = version_details.node_processes
        except Exception:
            exceptions.handle(request,
                              _("Unable to generate process choices."))
        process_choices = []
        for service, processes in node_processes.items():
            for process in processes:
                choice_label = str(service) + ":" + str(process)
                process_choices.append((choice_label, process))

        self.fields["processes"] = forms.MultipleChoiceField(
            label=_("Select Node Group Processes"),
            widget=CheckboxSelectMultiple(),
            choices=process_choices,
            required=True)

    class Meta(object):
        name = _("Node Processes")
        help_text = _("Select node processes for the node group")


class SelectNodeGroupSharesAction(workflows.Action):
    def __init__(self, request, *args, **kwargs):
        super(SelectNodeGroupSharesAction, self).__init__(
            request, *args, **kwargs)

        possible_shares = self.get_possible_shares(request)

        self.fields["shares"] = workflow_helpers.MultipleShareChoiceField(
            label=_("Select Shares"),
            widget=workflow_helpers.ShareWidget(choices=possible_shares),
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

    class Meta(object):
        name = _("Shares")
        help_text = _("Select the manila shares for this node group")


class GeneralConfig(workflows.Step):
    action_class = GeneralConfigAction
    contributes = ("general_nodegroup_name", )

    def contribute(self, data, context):
        for k, v in data.items():
            if "hidden" in k:
                continue
            context["general_" + k] = v if v != "None" else None
        return context


class SecurityConfig(workflows.Step):
    action_class = SecurityConfigAction
    contributes = ("security_autogroup", "security_groups")


class SelectNodeProcesses(workflows.Step):
    action_class = SelectNodeProcessesAction

    def contribute(self, data, context):
        post = self.workflow.request.POST
        context['general_processes'] = post.getlist('processes')
        return context


class SelectNodeGroupShares(workflows.Step):
    action_class = SelectNodeGroupSharesAction

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
        context['ngt_shares'] = shares_details
        return context


class ConfigureNodegroupTemplate(workflow_helpers.ServiceParametersWorkflow,
                                 workflow_helpers.StatusFormatMixin):
    slug = "configure_nodegroup_template"
    name = _("Create Node Group Template")
    finalize_button_name = _("Create")
    success_message = _("Created Node Group Template %s")
    name_property = "general_nodegroup_name"
    success_url = ("horizon:project:data_processing.clusters:"
                   "nodegroup-templates-tab")
    default_steps = (GeneralConfig, SelectNodeProcesses, SecurityConfig, )

    def __init__(self, request, context_seed, entry_point, *args, **kwargs):
        hlps = helpers.Helpers(request)

        plugin, hadoop_version = (
            workflow_helpers.get_plugin_and_hadoop_version(request))

        general_parameters, service_parameters = \
            hlps.get_general_and_service_nodegroups_parameters(plugin,
                                                               hadoop_version)

        if saharaclient.base.is_service_enabled(request, 'share'):
            ConfigureNodegroupTemplate._register_step(self,
                                                      SelectNodeGroupShares)

        self._populate_tabs(general_parameters, service_parameters)

        super(ConfigureNodegroupTemplate, self).__init__(request,
                                                         context_seed,
                                                         entry_point,
                                                         *args, **kwargs)

    def is_valid(self):
        missing = self.depends_on - set(self.context.keys())
        if missing:
            raise exceptions.WorkflowValidationError(
                "Unable to complete the workflow. The values %s are "
                "required but not present." % ", ".join(missing))
        checked_steps = []

        if "general_processes" in self.context:
            checked_steps = self.context["general_processes"]
        enabled_services = set([])
        for process_name in checked_steps:
            enabled_services.add(str(process_name).split(":")[0])

        steps_valid = True
        for step in self.steps:
            process_name = str(getattr(step, "process_name", None))
            if process_name not in enabled_services and \
                    not isinstance(step, GeneralConfig):
                continue
            if not step.action.is_valid():
                steps_valid = False
                step.has_errors = True
        if not steps_valid:
            return steps_valid
        return self.validate(self.context)

    def handle(self, request, context):
        try:
            processes = []
            for service_process in context["general_processes"]:
                processes.append(str(service_process).split(":")[1])

            configs_dict = (
                workflow_helpers.parse_configs_from_context(
                    context, self.defaults))

            plugin, hadoop_version = (
                workflow_helpers.get_plugin_and_hadoop_version(request))

            volumes_per_node = None
            volumes_size = None
            volumes_availability_zone = None
            volume_type = None
            volume_local_to_instance = False

            if context["general_storage"] == "cinder_volume":
                volumes_per_node = context["general_volumes_per_node"]
                volumes_size = context["general_volumes_size"]
                volumes_availability_zone = \
                    context["general_volumes_availability_zone"]
                volume_type = context["general_volume_type"]
                volume_local_to_instance = \
                    context["general_volume_local_to_instance"]

            ngt_shares = context.get('ngt_shares', [])

            image_id = context["general_image"] or None

            if (saharaclient.VERSIONS.active == '2'
                    and context["general_boot_storage"] == "cinder_volume"):
                boot_from_volume = True
                boot_volume_type = (
                    context["general_boot_volume_type"] or None
                )
                boot_volume_availability_zone = (
                    context["general_boot_volume_availability_zone"] or None
                )
                boot_volume_local_to_instance = (
                    context["general_boot_volume_local_to_instance"]
                )
            else:
                boot_from_volume = None
                boot_volume_type = None
                boot_volume_availability_zone = None
                boot_volume_local_to_instance = None

            ngt = saharaclient.nodegroup_template_create(
                request,
                name=context["general_nodegroup_name"],
                plugin_name=plugin,
                hadoop_version=hadoop_version,
                description=context["general_description"],
                flavor_id=context["general_flavor"],
                volumes_per_node=volumes_per_node,
                volumes_size=volumes_size,
                volumes_availability_zone=volumes_availability_zone,
                volume_type=volume_type,
                volume_local_to_instance=volume_local_to_instance,
                node_processes=processes,
                node_configs=configs_dict,
                floating_ip_pool=context.get("general_floating_ip_pool"),
                security_groups=context["security_groups"],
                auto_security_group=context["security_autogroup"],
                is_proxy_gateway=context["general_proxygateway"],
                availability_zone=context["general_availability_zone"],
                use_autoconfig=context['general_use_autoconfig'],
                shares=ngt_shares,
                is_public=context['general_is_public'],
                is_protected=context['general_is_protected'],
                boot_from_volume=boot_from_volume,
                boot_volume_type=boot_volume_type,
                boot_volume_availability_zone=boot_volume_availability_zone,
                boot_volume_local_to_instance=boot_volume_local_to_instance,
                image_id=image_id)

            hlps = helpers.Helpers(request)
            if hlps.is_from_guide():
                guide_type = context["general_guide_template_type"]
                request.session[guide_type + "_name"] = (
                    context["general_nodegroup_name"])
                request.session[guide_type + "_id"] = ngt.id
                self.success_url = (
                    "horizon:project:data_processing.clusters:cluster_guide")

            return True
        except api_base.APIException as e:
            self.error_description = str(e)
            return False
        except Exception:
            exceptions.handle(request)


class SelectPluginAction(workflows.Action,
                         workflow_helpers.PluginAndVersionMixin):
    hidden_create_field = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={"class": "hidden_create_field"}))

    def __init__(self, request, *args, **kwargs):
        super(SelectPluginAction, self).__init__(request, *args, **kwargs)

        sahara = saharaclient.client(request)
        self._generate_plugin_version_fields(sahara)

    class Meta(object):
        name = _("Select plugin and hadoop version")
        help_text_template = "nodegroup_templates/_create_general_help.html"


class SelectPlugin(workflows.Step):
    action_class = SelectPluginAction
    contributes = ("plugin_name", "hadoop_version")

    def contribute(self, data, context):
        context = super(SelectPlugin, self).contribute(data, context)
        context["plugin_name"] = data.get('plugin_name', None)
        context["hadoop_version"] = \
            data.get(context["plugin_name"] + "_version", None)
        return context


class CreateNodegroupTemplate(workflows.Workflow):
    slug = "create_nodegroup_template"
    name = _("Create Node Group Template")
    finalize_button_name = _("Next")
    success_message = _("Created")
    failure_message = _("Could not create")
    success_url = ("horizon:project:data_processing.clusters:"
                   "nodegroup-templates-tab")
    default_steps = (SelectPlugin,)

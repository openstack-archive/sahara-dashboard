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

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import workflows

from sahara_dashboard.api import sahara as saharaclient
import sahara_dashboard.content.data_processing.clusters. \
    cluster_templates.workflows.create as t_flows
import sahara_dashboard.content.data_processing. \
    clusters.clusters.workflows.create as c_flow
from sahara_dashboard.content.data_processing.utils \
    import acl as acl_utils
from sahara_dashboard.content.data_processing.utils import helpers
import sahara_dashboard.content.data_processing. \
    utils.workflow_helpers as whelpers


DATA_SOURCE_CREATE_URL = ("horizon:project:data_processing.jobs"
                          ":create-data-source")


class JobExecutionGeneralConfigAction(workflows.Action):
    job_input = forms.DynamicChoiceField(
        label=_("Input"),
        initial=(None, "None"),
        add_item_link=DATA_SOURCE_CREATE_URL,
        required=False)

    job_output = forms.DynamicChoiceField(
        label=_("Output"),
        initial=(None, "None"),
        add_item_link=DATA_SOURCE_CREATE_URL,
        required=False)

    is_public = acl_utils.get_is_public_form(_("job"))
    is_protected = acl_utils.get_is_protected_form(_("job"))

    def __init__(self, request, *args, **kwargs):
        super(JobExecutionGeneralConfigAction, self).__init__(request,
                                                              *args,
                                                              **kwargs)
        req = request.GET or request.POST
        if req.get("job_id", None) is None:
            self.fields["job"] = forms.ChoiceField(
                label=_("Job"))
            self.fields["job"].choices = self.populate_job_choices(request)
        else:
            self.fields["job"] = forms.CharField(
                widget=forms.HiddenInput(),
                initial=req.get("job_id", None))

    def populate_job_input_choices(self, request, context):
        return self.get_data_source_choices(request, context)

    def populate_job_output_choices(self, request, context):
        return self.get_data_source_choices(request, context)

    def get_data_source_choices(self, request, context):
        try:
            data_sources = saharaclient.data_source_list(request)
        except Exception:
            data_sources = []
            exceptions.handle(request,
                              _("Unable to fetch data sources."))

        choices = [(data_source.id, data_source.name)
                   for data_source in data_sources]
        choices.insert(0, (None, 'None'))

        return choices

    def populate_job_choices(self, request):
        try:
            jobs = saharaclient.job_list(request)
        except Exception:
            jobs = []
            exceptions.handle(request,
                              _("Unable to fetch jobs."))

        choices = [(job.id, job.name)
                   for job in jobs]

        return choices

    class Meta(object):
        name = _("Job")
        help_text_template = "job_templates/_launch_job_help.html"


class JobExecutionExistingGeneralConfigAction(JobExecutionGeneralConfigAction):
    cluster = forms.ChoiceField(
        label=_("Cluster"),
        initial=(None, "None"),
        widget=forms.Select(attrs={"class": "cluster_choice"}))

    is_public = acl_utils.get_is_public_form(_("job"))
    is_protected = acl_utils.get_is_protected_form(_("job"))

    def populate_cluster_choices(self, request, context):
        try:
            clusters = saharaclient.cluster_list(request)
        except Exception:
            clusters = []
            exceptions.handle(request,
                              _("Unable to fetch clusters."))
        choices = [(cl.id, "%s %s" % (cl.name,
                                      helpers.ALLOWED_STATUSES.get(cl.status)))
                   for cl in clusters if cl.status in helpers.ALLOWED_STATUSES]
        if not choices:
            choices = [(None, _("No clusters available"))]
        return choices

    class Meta(object):
        name = _("Job")
        help_text_template = "job_templates/_launch_job_help.html"


def _merge_interface_with_configs(interface, job_configs):
    interface_by_mapping = {(arg['mapping_type'], arg['location']): arg
                            for arg in interface}
    mapped_types = ("configs", "params")
    mapped_configs = {
        (mapping_type, key): value for mapping_type in mapped_types
        for key, value in job_configs.get(mapping_type, {}).items()
    }
    for index, arg in enumerate(job_configs.get('args', [])):
        mapped_configs['args', str(index)] = arg
    free_arguments, interface_arguments = {}, {}
    for mapping, value in mapped_configs.items():
        if mapping in interface_by_mapping:
            arg = interface_by_mapping[mapping]
            interface_arguments[arg['id']] = value
        else:
            free_arguments[mapping] = value
    configs = {"configs": {}, "params": {}, "args": {}}
    for mapping, value in free_arguments.items():
        mapping_type, location = mapping
        configs[mapping_type][location] = value
    configs["args"] = [
        value for key, value in sorted(configs["args"].items(),
                                       key=lambda x: int(x[0]))]
    return configs, interface_arguments


class JobConfigAction(workflows.Action):
    MAIN_CLASS = "edp.java.main_class"
    STORM_PYLEUS_TOPOLOGY_NAME = "topology_name"
    JAVA_OPTS = "edp.java.java_opts"
    EDP_MAPPER = "edp.streaming.mapper"
    EDP_REDUCER = "edp.streaming.reducer"
    EDP_PREFIX = "edp."
    EDP_HBASE_COMMON_LIB = "edp.hbase_common_lib"
    EDP_ADAPT_FOR_OOZIE = "edp.java.adapt_for_oozie"
    EDP_ADAPT_SPARK_SWIFT = "edp.spark.adapt_for_swift"
    EDP_SUBST_DATASOURCE_NAME = "edp.substitute_data_source_for_name"
    EDP_SUBST_DATASOURCE_UUID = "edp.substitute_data_source_for_uuid"

    property_name = forms.ChoiceField(
        required=False,
    )

    job_configs = forms.CharField(
        required=False,
        widget=forms.HiddenInput())

    job_params = forms.CharField(
        required=False,
        widget=forms.HiddenInput())

    job_args_array = forms.CharField(
        required=False,
        widget=forms.HiddenInput())

    job_type = forms.CharField(
        required=False,
        widget=forms.HiddenInput())

    main_class = forms.CharField(label=_("Main Class"),
                                 required=False)

    topology_name = forms.CharField(
        label=_("Topology Name"),
        help_text=_("Use the same topology name as defined in your "
                    ".yaml file"),
        required=False)

    java_opts = forms.CharField(label=_("Java Opts"),
                                required=False)

    streaming_mapper = forms.CharField(label=_("Mapper"),
                                       required=False)

    streaming_reducer = forms.CharField(label=_("Reducer"),
                                        required=False)

    hbase_common_lib = forms.BooleanField(
        label=_("Use HBase Common library"),
        help_text=_("Run HBase EDP Jobs with common HBase library on HDFS"),
        required=False, initial=True)

    adapt_oozie = forms.BooleanField(
        label=_("Adapt For Oozie"),
        help_text=_("Automatically modify the Hadoop configuration"
                    " so that job config values are set and so that"
                    " Oozie will handle exit codes correctly."),
        required=False, initial=True)

    adapt_spark_swift = forms.BooleanField(
        label=_("Enable Swift Paths"),
        help_text=_("Modify the configuration so that swift URLs can "
                    "be dereferenced through HDFS at runtime."),
        required=False, initial=True)

    datasource_substitute = forms.BooleanField(
        label=_("Use Data Source Substitution for Names and UUIDs"),
        help_text=_("Substitute data source objects for URLs of "
                    "the form datasource://name or uuid."),
        required=False, initial=True)

    def __init__(self, request, *args, **kwargs):
        super(JobConfigAction, self).__init__(request, *args, **kwargs)
        req = request.GET or request.POST
        job_ex_id = req.get("job_execution_id")
        if job_ex_id is not None:
            job_ex = saharaclient.job_execution_get(request, job_ex_id)
            try:
                jt_id = job_ex.job_template_id  # typical APIv2
            except AttributeError:
                jt_id = job_ex.job_id  # APIv1.1, older APIv2
            job = saharaclient.job_get(request, jt_id)
            job_configs, interface_args = _merge_interface_with_configs(
                job.interface, job_ex.job_configs)
            edp_configs = {}

            if 'configs' in job_configs:
                configs, edp_configs = (
                    self.clean_edp_configs(job_configs['configs']))
                self.fields['job_configs'].initial = (
                    json.dumps(configs))

            if 'params' in job_configs:
                self.fields['job_params'].initial = (
                    json.dumps(job_configs['params']))

            if 'args' in job_configs:
                self.fields['job_args_array'].initial = (
                    json.dumps(job_configs['args']))

            if self.MAIN_CLASS in edp_configs:
                self.fields['main_class'].initial = (
                    edp_configs[self.MAIN_CLASS])
            if self.STORM_PYLEUS_TOPOLOGY_NAME in edp_configs:
                self.fields['topology_name'].initial = (
                    edp_configs[self.STORM_PYLEUS_TOPOLOGY_NAME])
            if self.JAVA_OPTS in edp_configs:
                self.fields['java_opts'].initial = (
                    edp_configs[self.JAVA_OPTS])

            if self.EDP_MAPPER in edp_configs:
                self.fields['streaming_mapper'].initial = (
                    edp_configs[self.EDP_MAPPER])
            if self.EDP_REDUCER in edp_configs:
                self.fields['streaming_reducer'].initial = (
                    edp_configs[self.EDP_REDUCER])
            if self.EDP_HBASE_COMMON_LIB in edp_configs:
                self.fields['hbase_common_lib'].initial = (
                    edp_configs[self.EDP_HBASE_COMMON_LIB])
            if self.EDP_ADAPT_FOR_OOZIE in edp_configs:
                self.fields['adapt_oozie'].initial = (
                    edp_configs[self.EDP_ADAPT_FOR_OOZIE])
            if self.EDP_ADAPT_SPARK_SWIFT in edp_configs:
                self.fields['adapt_spark_swift'].initial = (
                    edp_configs[self.EDP_ADAPT_SPARK_SWIFT])
            if (self.EDP_SUBST_DATASOURCE_NAME in edp_configs or
                    self.EDP_SUBST_DATASOURCE_UUID in edp_configs):
                self.fields['datasource_substitute'].initial = (
                    edp_configs.get(self.EDP_SUBST_DATASOURCE_UUID, True)
                    or
                    edp_configs.get(self.EDP_SUBST_DATASOURCE_NAME, True))

    def clean(self):
        cleaned_data = super(workflows.Action, self).clean()
        job_type = cleaned_data.get("job_type", None)

        if job_type != "MapReduce.Streaming":
            if "streaming_mapper" in self._errors:
                del self._errors["streaming_mapper"]
            if "streaming_reducer" in self._errors:
                del self._errors["streaming_reducer"]

        return cleaned_data

    def populate_property_name_choices(self, request, context):
        req = request.GET or request.POST
        job_id = req.get("job_id") or req.get("job")
        job_type = saharaclient.job_get(request, job_id).type
        job_configs = (
            saharaclient.job_get_configs(request, job_type).job_config)
        choices = [(param['value'], param['name'])
                   for param in job_configs['configs']]
        return choices

    def clean_edp_configs(self, configs):
        edp_configs = {}
        for key, value in configs.items():
            if key.startswith(self.EDP_PREFIX):
                edp_configs[key] = value
        for rmkey in edp_configs.keys():
            # remove all configs handled via other controls
            # so they do not show up in the free entry inputs
            if rmkey in [self.EDP_HBASE_COMMON_LIB,
                         self.EDP_MAPPER,
                         self.EDP_REDUCER,
                         self.MAIN_CLASS,
                         self.STORM_PYLEUS_TOPOLOGY_NAME,
                         self.JAVA_OPTS,
                         self.EDP_ADAPT_FOR_OOZIE,
                         self.EDP_ADAPT_SPARK_SWIFT,
                         self.EDP_SUBST_DATASOURCE_UUID,
                         self.EDP_SUBST_DATASOURCE_NAME, ]:
                del configs[rmkey]
        return (configs, edp_configs)

    class Meta(object):
        name = _("Configure")
        help_text_template = "job_templates/_launch_job_configure_help.html"


class JobExecutionGeneralConfig(workflows.Step):
    action_class = JobExecutionGeneralConfigAction

    def contribute(self, data, context):
        for k, v in data.items():
            if k in ["job_input", "job_output"]:
                context["job_general_" + k] = None if (v in [None, ""]) else v
            else:
                context["job_general_" + k] = v

        return context


class JobExecutionExistingGeneralConfig(workflows.Step):
    action_class = JobExecutionExistingGeneralConfigAction

    def contribute(self, data, context):
        for k, v in data.items():
            if k in ["job_input", "job_output"]:
                context["job_general_" + k] = None if (v in [None, ""]) else v
            else:
                context["job_general_" + k] = v

        return context


class JobConfig(workflows.Step):
    action_class = JobConfigAction
    template_name = 'job_templates/config_template.html'

    def contribute(self, data, context):
        job_config = self.clean_configs(
            json.loads(data.get("job_configs", '{}')))
        job_params = self.clean_configs(
            json.loads(data.get("job_params", '{}')))
        job_args_array = self.clean_configs(
            json.loads(data.get("job_args_array", '[]')))
        job_type = data.get("job_type", '')

        context["job_type"] = job_type
        context["job_config"] = {"configs": job_config}
        context["job_config"]["args"] = job_args_array

        context["job_config"]["configs"][
            JobConfigAction.EDP_SUBST_DATASOURCE_UUID] = (
                data.get("datasource_substitute", True))
        context["job_config"]["configs"][
            JobConfigAction.EDP_SUBST_DATASOURCE_NAME] = (
                data.get("datasource_substitute", True))

        if job_type in ["Java", "Spark", "Storm"]:
            context["job_config"]["configs"][JobConfigAction.MAIN_CLASS] = (
                data.get("main_class", ""))
            context["job_config"]["configs"][JobConfigAction.JAVA_OPTS] = (
                data.get("java_opts", ""))
            context["job_config"]["configs"][
                JobConfigAction.EDP_HBASE_COMMON_LIB] = (
                    data.get("hbase_common_lib", True))
            if job_type == "Java":
                context["job_config"]["configs"][
                    JobConfigAction.EDP_ADAPT_FOR_OOZIE] = (
                        data.get("adapt_oozie", True))
            if job_type == "Spark":
                context["job_config"]["configs"][
                    JobConfigAction.EDP_ADAPT_SPARK_SWIFT] = (
                    data.get("adapt_spark_swift", True))
        elif job_type == "Storm.Pyleus":
            context["job_config"]["configs"][
                JobConfigAction.STORM_PYLEUS_TOPOLOGY_NAME] = (
                data.get("topology_name", ""))
        elif job_type == "MapReduce.Streaming":
            context["job_config"]["configs"][JobConfigAction.EDP_MAPPER] = (
                data.get("streaming_mapper", ""))
            context["job_config"]["configs"][JobConfigAction.EDP_REDUCER] = (
                data.get("streaming_reducer", ""))
        else:
            context["job_config"]["params"] = job_params

        return context

    @staticmethod
    def clean_configs(configs):
        cleaned_conf = None
        if isinstance(configs, dict):
            cleaned_conf = dict([(k.strip(), v.strip())
                                 for k, v in configs.items()
                                 if len(v.strip()) > 0 and len(k.strip()) > 0])
        elif isinstance(configs, list):
            cleaned_conf = list([v.strip() for v in configs
                                 if len(v.strip()) > 0])
        return cleaned_conf


class NewClusterConfigAction(c_flow.GeneralConfigAction):
    persist_cluster = forms.BooleanField(
        label=_("Persist cluster after job exit"),
        required=False)

    class Meta(object):
        name = _("Configure Cluster")
        help_text_template = "clusters/_configure_general_help.html"


class ClusterGeneralConfig(workflows.Step):
    action_class = NewClusterConfigAction
    contributes = ("hidden_configure_field", )

    def contribute(self, data, context):
        for k, v in data.items():
            context["cluster_general_" + k] = v

        return context


class JobExecutionInterfaceConfigAction(workflows.Action):

    def __init__(self, request, *args, **kwargs):
        super(JobExecutionInterfaceConfigAction, self).__init__(
            request, *args, **kwargs)
        job_id = (request.GET.get("job_id")
                  or request.POST.get("job"))
        job = saharaclient.job_get(request, job_id)
        interface = job.interface or []
        interface_args = {}
        req = request.GET or request.POST
        job_ex_id = req.get("job_execution_id")
        if job_ex_id is not None:
            job_ex = saharaclient.job_execution_get(request, job_ex_id)
            try:
                jt_id = job_ex.job_template_id  # typical APIv2
            except AttributeError:
                jt_id = job_ex.job_id  # APIv1.1, older APIv2
            job = saharaclient.job_get(request, jt_id)
            job_configs, interface_args = _merge_interface_with_configs(
                job.interface, job_ex.job_configs)

        for argument in interface:
            field = forms.CharField(
                required=argument.get('required'),
                label=argument['name'],
                initial=(interface_args.get(argument['id']) or
                         argument.get('default')),
                help_text=argument.get('description'),
                widget=forms.TextInput()
            )
            self.fields['argument_%s' % argument['id']] = field
        self.fields['argument_ids'] = forms.CharField(
            initial=json.dumps({argument['id']: argument['name']
                                for argument in interface}),
            widget=forms.HiddenInput()
        )

    def clean(self):
        cleaned_data = super(JobExecutionInterfaceConfigAction, self).clean()
        return cleaned_data

    class Meta(object):
        name = _("Interface Arguments")


class JobExecutionInterfaceConfig(workflows.Step):
    action_class = JobExecutionInterfaceConfigAction

    def contribute(self, data, context):
        for k, v in data.items():
            context[k] = v
        return context


class LaunchJob(workflows.Workflow):
    slug = "launch_job"
    name = _("Launch Job")
    finalize_button_name = _("Launch")
    success_message = _("Job launched")
    failure_message = _("Could not launch job")
    success_url = "horizon:project:data_processing.jobs:jobs-tab"
    default_steps = (JobExecutionExistingGeneralConfig, JobConfig,
                     JobExecutionInterfaceConfig)

    def handle(self, request, context):
        argument_ids = json.loads(context['argument_ids'])
        interface = {name: context["argument_" + str(arg_id)]
                     for arg_id, name in argument_ids.items()}

        saharaclient.job_execution_create(
            request,
            context["job_general_job"],
            context["job_general_cluster"],
            context["job_general_job_input"],
            context["job_general_job_output"],
            context["job_config"],
            interface,
            is_public=context['job_general_is_public'],
            is_protected=context['job_general_is_protected']
        )
        return True


class SelectPluginForJobLaunchAction(t_flows.SelectPluginAction):
    def __init__(self, request, *args, **kwargs):
        super(SelectPluginForJobLaunchAction, self).__init__(request,
                                                             *args,
                                                             **kwargs)
        self.fields["job_id"] = forms.ChoiceField(
            label=_("Plugin name"),
            initial=request.GET.get("job_id") or request.POST.get("job_id"),
            widget=forms.HiddenInput(attrs={"class": "hidden_create_field"}))

        self.fields["job_configs"] = forms.ChoiceField(
            label=_("Job configs"),
            widget=forms.HiddenInput(attrs={"class": "hidden_create_field"}))

        self.fields["job_args"] = forms.ChoiceField(
            label=_("Job args"),
            widget=forms.HiddenInput(attrs={"class": "hidden_create_field"}))

        self.fields["job_params"] = forms.ChoiceField(
            label=_("Job params"),
            widget=forms.HiddenInput(attrs={"class": "hidden_create_field"}))
        req = request.GET or request.POST
        job_ex_id = req.get("job_execution_id")
        if job_ex_id is not None:
            self.fields["job_execution_id"] = forms.ChoiceField(
                label=_("Job Execution ID"),
                initial=job_ex_id,
                widget=forms.HiddenInput(
                    attrs={"class": "hidden_create_field"}))

            job_configs = (
                saharaclient.job_execution_get(request,
                                               job_ex_id).job_configs)

            if "configs" in job_configs:
                self.fields["job_configs"].initial = (
                    json.dumps(job_configs["configs"]))
            if "params" in job_configs:
                self.fields["job_params"].initial = (
                    json.dumps(job_configs["params"]))
            if "args" in job_configs:
                self.fields["job_args"].initial = (
                    json.dumps(job_configs["args"]))

    class Meta(object):
        name = _("Select plugin and hadoop version for cluster")
        help_text_template = "clusters/_create_general_help.html"


class SelectHadoopPlugin(workflows.Step):
    action_class = SelectPluginForJobLaunchAction


class ChosePluginVersion(workflows.Workflow):
    slug = "launch_job"
    name = _("Launch Job")
    finalize_button_name = _("Create")
    success_message = _("Created")
    failure_message = _("Could not create")
    success_url = "horizon:project:data_processing.cluster_templates:index"
    default_steps = (SelectHadoopPlugin,)


class LaunchJobNewCluster(workflows.Workflow):
    slug = "launch_job"
    name = _("Launch Job")
    finalize_button_name = _("Launch")
    success_message = _("Job launched")
    failure_message = _("Could not launch job")
    success_url = "horizon:project:data_processing.jobs:index"
    default_steps = (ClusterGeneralConfig,
                     JobExecutionGeneralConfig,
                     JobConfig,
                     JobExecutionInterfaceConfig)

    def handle(self, request, context):
        node_groups = None

        plugin, hadoop_version = (
            whelpers.get_plugin_and_hadoop_version(request))

        ct_id = context["cluster_general_cluster_template"] or None
        user_keypair = context["cluster_general_keypair"] or None

        argument_ids = json.loads(context['argument_ids'])
        interface = {name: context["argument_" + str(arg_id)]
                     for arg_id, name in argument_ids.items()}

        try:
            cluster = saharaclient.cluster_create(
                request,
                context["cluster_general_cluster_name"],
                plugin, hadoop_version,
                cluster_template_id=ct_id,
                default_image_id=context["cluster_general_image"],
                description=context["cluster_general_description"],
                node_groups=node_groups,
                user_keypair_id=user_keypair,
                is_transient=not(context["cluster_general_persist_cluster"]),
                net_id=context.get(
                    "cluster_general_neutron_management_network",
                    None))
        except Exception:
            exceptions.handle(request,
                              _("Unable to create new cluster for job."))
            return False

        try:
            saharaclient.job_execution_create(
                request,
                context["job_general_job"],
                cluster.id,
                context["job_general_job_input"],
                context["job_general_job_output"],
                context["job_config"],
                interface,
                is_public=context['job_general_is_public'],
                is_protected=context['job_general_is_protected']
            )
        except Exception:
            exceptions.handle(request,
                              _("Unable to launch job."))
            return False
        return True

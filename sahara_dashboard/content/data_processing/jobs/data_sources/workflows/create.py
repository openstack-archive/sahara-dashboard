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

from horizon import exceptions
from horizon import forms
from horizon import workflows

from sahara_dashboard.api import manila as manilaclient
from sahara_dashboard.api import sahara as saharaclient
from sahara_dashboard.content.data_processing.utils \
    import acl as acl_utils
from sahara_dashboard.content.data_processing \
    .utils import helpers


class GeneralConfigAction(workflows.Action):
    data_source_name = forms.CharField(label=_("Name"))

    data_source_type = forms.ChoiceField(
        label=_("Data Source Type"),
        widget=forms.Select(attrs={
            "class": "switchable",
            "data-slug": "ds_type"
        }))

    data_source_manila_share = forms.ChoiceField(
        label=_("Manila share"),
        required=False,
        widget=forms.Select(attrs={
            "class": "switched",
            "data-switch-on": "ds_type",
            "data-ds_type-manila": _("Manila share")
        }))

    data_source_url = forms.CharField(
        label=_("URL"),
        widget=forms.TextInput(attrs={
            "class": "switched",
            "data-switch-on": "ds_type",
            "data-ds_type-manila": _("Path on share"),
            "data-ds_type-swift": _("URL"),
            "data-ds_type-hdfs": _("URL"),
            "data-ds_type-maprfs": _("URL"),
            "data-ds_type-s3": _("URL"),
        }))

    data_source_credential_user = forms.CharField(
        label=_("Source username"),
        required=False,
        widget=forms.TextInput(attrs={
            "class": "switched",
            "data-switch-on": "ds_type",
            "data-ds_type-swift": _("Source username")
        }))

    data_source_credential_pass = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'switched',
            'data-switch-on': 'ds_type',
            'data-ds_type-swift': _("Source password"),
            'autocomplete': 'off'
        }),
        label=_("Source password"),
        required=False)

    data_source_credential_accesskey = forms.CharField(
        label=_("S3 accsss key"),
        required=False,
        widget=forms.TextInput(attrs={
            "class": "switched",
            "data-switch-on": "ds_type",
            "data-ds_type-s3": _("S3 access key")
        }))

    data_source_credential_secretkey = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'switched',
            'data-switch-on': 'ds_type',
            'data-ds_type-s3': _("S3 secret key"),
            'autocomplete': 'off'
        }),
        label=_("S3 secret key"),
        required=False)

    data_source_credential_endpoint = forms.CharField(
        label=_("S3 endpoint"),
        required=False,
        help_text=_("Endpoint should be specified without protocol"),
        widget=forms.TextInput(attrs={
            "class": "switched",
            "data-switch-on": "ds_type",
            "data-ds_type-s3": _("S3 endpoint")
        }))

    data_source_credential_s3_ssl = forms.BooleanField(
        label=_("Use SSL"),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            "class": "switched",
            "data-switch-on": "ds_type",
            "data-ds_type-s3": _("Use SSL")
        }))

    data_source_credential_s3_bucket_in_path = forms.BooleanField(
        label=_("Use bucket in path"),
        required=False,
        initial=True,
        help_text=_("If checked, bucket will be in path instead of host"),
        widget=forms.CheckboxInput(attrs={
            "class": "switched",
            "data-switch-on": "ds_type",
            "data-ds_type-s3": _("Use bucket in path")
        }))

    data_source_description = forms.CharField(
        label=_("Description"),
        required=False,
        widget=forms.Textarea(attrs={'rows': 4}))

    is_public = acl_utils.get_is_public_form(_("data source"))
    is_protected = acl_utils.get_is_protected_form(_("data source"))

    def __init__(self, request, *args, **kwargs):
        super(GeneralConfigAction, self).__init__(request, *args, **kwargs)

        self.fields["data_source_type"].choices = [("swift", "Swift"),
                                                   ("hdfs", "HDFS"),
                                                   ("maprfs", "MapR FS"),
                                                   ("s3", "S3")]
        # If Manila is running, enable it as a choice for a data source
        if saharaclient.base.is_service_enabled(request, 'share'):
            self.fields["data_source_type"].choices.append(
                ("manila", "Manila"))
            self.fields["data_source_manila_share"].choices = (
                self.populate_manila_share_choices(request)
            )

    def populate_manila_share_choices(self, request):
        try:
            shares = manilaclient.share_list(request)
            choices = [(s.id, s.name) for s in shares]
        except Exception:
            exceptions.handle(request, _("Failed to get list of shares"))
            choices = []
        return choices

    class Meta(object):
        name = _("Create Data Source")
        help_text_template = "data_sources/_create_data_source_help.html"


class GeneralConfig(workflows.Step):
    action_class = GeneralConfigAction

    def contribute(self, data, context):
        for k, v in data.items():
            context["general_" + k] = v

        context["source_url"] = context["general_data_source_url"]
        ds_type = context["general_data_source_type"]

        if ds_type == "swift":
            if not context["general_data_source_url"].startswith("swift://"):
                context["source_url"] = "swift://{0}".format(
                    context["general_data_source_url"])
        elif ds_type == "manila":
            context["source_url"] = "{0}://{1}{2}".format(
                ds_type,
                context["general_data_source_manila_share"],
                context["general_data_source_url"])
        return context


class CreateDataSource(workflows.Workflow):
    slug = "create_data_source"
    name = _("Create Data Source")
    finalize_button_name = _("Create")
    success_message = _("Data source created")
    failure_message = _("Could not create data source")
    success_url = "horizon:project:data_processing.jobs:index"
    default_steps = (GeneralConfig, )

    def handle(self, request, context):
        s3_credentials = {}
        if context["general_data_source_type"] == "s3":
            if context.get("general_data_source_credential_accesskey", None):
                s3_credentials["accesskey"] = context[
                    "general_data_source_credential_accesskey"]
            if context.get("general_data_source_credential_secretkey", None):
                s3_credentials["secretkey"] = context[
                    "general_data_source_credential_secretkey"]
            if context.get("general_data_source_credential_endpoint", None):
                s3_credentials["endpoint"] = context[
                    "general_data_source_credential_endpoint"]
            s3_credentials["bucket_in_path"] = context[
                "general_data_source_credential_s3_bucket_in_path"]
            s3_credentials["ssl"] = context[
                "general_data_source_credential_s3_ssl"]
        s3_credentials = s3_credentials or None
        try:
            self.object = saharaclient.data_source_create(
                request,
                context["general_data_source_name"],
                context["general_data_source_description"],
                context["general_data_source_type"],
                context["source_url"],
                context.get("general_data_source_credential_user", None),
                context.get("general_data_source_credential_pass", None),
                is_public=context['general_is_public'],
                is_protected=context['general_is_protected'],
                s3_credentials=s3_credentials
            )

            hlps = helpers.Helpers(request)
            if hlps.is_from_guide():
                request.session["guide_datasource_id"] = self.object.id
                request.session["guide_datasource_name"] = self.object.name
                self.success_url = (
                    "horizon:project:data_processing.wizard:jobex_guide")
            return True
        except Exception:
            exceptions.handle(request)
            return False

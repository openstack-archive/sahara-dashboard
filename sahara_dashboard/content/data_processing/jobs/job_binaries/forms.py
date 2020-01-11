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

from urllib import parse
import uuid

from django.forms import widgets
from django import template
from django.template import defaultfilters
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from sahara_dashboard.api import manila as manilaclient
from sahara_dashboard.api import sahara as saharaclient
from sahara_dashboard.content.data_processing.utils \
    import acl as acl_utils
from saharaclient.api import base


class LabeledInput(widgets.TextInput):

    def __init__(self, jb_type, *args, **kwargs):
        self.jb_type = jb_type
        super(LabeledInput, self).__init__(*args, **kwargs)

    def render(self, name, value, attrs=None):
        input = super(LabeledInput, self).render(name, value, attrs)
        label = "<span id='%s'>%s</span>" %\
            ("id_%s_label" % name,
             "%s://" % self.jb_type)
        result = "%s%s" % (label, input)
        return mark_safe(result)


class JobBinaryCreateForm(forms.SelfHandlingForm):
    NEW_SCRIPT = "newscript"
    UPLOAD_BIN = "uploadfile"
    action_url = ('horizon:project:data_processing.'
                  'jobs:create-job-binary')

    def __init__(self, request, *args, **kwargs):
        super(JobBinaryCreateForm, self).__init__(request, *args, **kwargs)

        self.help_text_template = "job_binaries/_create_job_binary_help.html"

        self.fields["job_binary_name"] = forms.CharField(label=_("Name"))

        self.fields["job_binary_type"] = forms.ChoiceField(
            label=_("Storage type"),
            widget=forms.Select(
                attrs={
                    'class': 'switchable',
                    'data-slug': 'jb_type'
                }))

        self.fields["job_binary_url"] = forms.CharField(
            label=_("URL"),
            required=False,
            widget=LabeledInput(
                "swift",
                attrs={
                    'class': 'switched',
                    'data-switch-on': 'jb_type',
                    'data-jb_type-swift': _('URL')
                }))

        self.fields["job_binary_manila_share"] = forms.ChoiceField(
            label=_("Share"),
            required=False,
            widget=forms.Select(
                attrs={
                    'class': 'switched',
                    'data-switch-on': 'jb_type',
                    'data-jb_type-manila': _('Share')
                }))

        self.fields["job_binary_manila_path"] = forms.CharField(
            label=_("Path"),
            required=False,
            widget=forms.TextInput(
                attrs={
                    'class': 'switched',
                    'data-switch-on': 'jb_type',
                    'data-jb_type-manila': _('Path')
                }))

        self.fields["job_binary_internal"] = forms.ChoiceField(
            label=_("Internal binary"),
            required=False,
            widget=forms.Select(
                attrs={
                    'class': 'switched switchable',
                    'data-slug': 'jb_internal',
                    'data-switch-on': 'jb_type',
                    'data-jb_type-internal-db': _('Internal Binary')
                }))

        self.fields["job_binary_file"] = forms.FileField(
            label=_("Upload File"),
            required=False,
            widget=forms.ClearableFileInput(
                attrs={
                    'class': 'switched',
                    'data-switch-on': 'jb_internal',
                    'data-jb_internal-uploadfile': _("Upload File")
                }))

        self.fields["job_binary_script_name"] = forms.CharField(
            label=_("Script name"),
            required=False,
            widget=forms.TextInput(
                attrs={
                    'class': 'switched',
                    'data-switch-on': 'jb_internal',
                    'data-jb_internal-newscript': _("Script name")
                }))

        self.fields["job_binary_script"] = forms.CharField(
            label=_("Script text"),
            required=False,
            widget=forms.Textarea(
                attrs={
                    'rows': 4,
                    'class': 'switched',
                    'data-switch-on': 'jb_internal',
                    'data-jb_internal-newscript': _("Script text")
                }))

        self.fields["job_binary_username"] = forms.CharField(
            label=_("Username"),
            required=False,
            widget=forms.TextInput(
                attrs={
                    'class': 'switched',
                    'data-switch-on': 'jb_type',
                    'data-jb_type-swift': _('Username')
                }))

        self.fields["job_binary_password"] = forms.CharField(
            label=_("Password"),
            required=False,
            widget=forms.PasswordInput(
                attrs={
                    'autocomplete': 'off',
                    'class': 'switched',
                    'data-switch-on': 'jb_type',
                    'data-jb_type-swift': _('Password')
                }))

        self.fields["job_binary_s3_url"] = forms.CharField(
            label=_("URL"),
            required=False,
            widget=LabeledInput(
                "s3",
                attrs={
                    'class': 'switched',
                    'data-switch-on': 'jb_type',
                    'data-jb_type-s3': _('URL')
                }))

        self.fields["job_binary_s3_endpoint"] = forms.CharField(
            label=_("S3 Endpoint"),
            required=False,
            widget=forms.TextInput(
                attrs={
                    'class': 'switched',
                    'data-switch-on': 'jb_type',
                    'data-jb_type-s3': _('S3 Endpoint')
                }))

        self.fields["job_binary_access_key"] = forms.CharField(
            label=_("Access Key"),
            required=False,
            widget=forms.TextInput(
                attrs={
                    'class': 'switched',
                    'data-switch-on': 'jb_type',
                    'data-jb_type-s3': _('Access Key')
                }))

        self.fields["job_binary_secret_key"] = forms.CharField(
            label=_("Secret Key"),
            required=False,
            widget=forms.PasswordInput(
                attrs={
                    'autocomplete': 'off',
                    'class': 'switched',
                    'data-switch-on': 'jb_type',
                    'data-jb_type-s3': _('Secret Key')
                }))

        self.fields["job_binary_description"] = (
            forms.CharField(label=_("Description"),
                            required=False,
                            widget=forms.Textarea()))

        self.fields["is_public"] = acl_utils.get_is_public_form(
            _("job binary"))
        self.fields["is_protected"] = acl_utils.get_is_protected_form(
            _("job binary"))

        self.fields["job_binary_type"].choices =\
            [("swift", "Swift"),
             ("s3", "S3")]

        if saharaclient.VERSIONS.active == '1.1':
            self.fields["job_binary_type"].choices.append(
                ("internal-db", "Internal database")
            )
            self.fields["job_binary_internal"].choices =\
                self.populate_job_binary_internal_choices(request)

        if saharaclient.base.is_service_enabled(request, 'share'):
            self.fields["job_binary_type"].choices.append(("manila", "Manila"))
            self.fields["job_binary_manila_share"].choices = (
                self.populate_job_binary_manila_share_choices(request))

        self.load_form_values()

    def load_form_values(self):
        if "job_binary" in self.initial:
            jb = self.initial["job_binary"]
            for field in self.fields:
                if self.FIELD_MAP[field]:
                    if field in ["job_binary_url", "job_binary_s3_url"]:
                        url = getattr(jb, self.FIELD_MAP[field], None)
                        self.set_initial_values_by_type(url)
                    else:
                        self.fields[field].initial = (
                            getattr(jb, self.FIELD_MAP[field], None))

    def set_initial_values_by_type(self, url):
        parsed = parse.urlparse(url)
        self.fields["job_binary_type"].initial = parsed.scheme
        if parsed.scheme == "manila":
            self.fields["job_binary_manila_share"].initial = parsed.netloc
            self.fields["job_binary_manila_path"].initial = parsed.path
        elif parsed.scheme == "swift":
            self.fields["job_binary_url"].initial = (
                "{0}{1}".format(parsed.netloc, parsed.path))
        elif parsed.scheme == "s3":
            self.fields["job_binary_s3_url"].initial = (
                "{0}{1}".format(parsed.netloc, parsed.path))
        else:
            self.fields["job_binary_url"].initial = "{0}".format(parsed.netloc)

    def populate_job_binary_manila_share_choices(self, request):
        try:
            shares = manilaclient.share_list(request)
            choices = [(s.id, s.name) for s in shares]
        except Exception:
            exceptions.handle(request, _("Failed to get list of shares"))
            choices = []
        return choices

    def populate_job_binary_internal_choices(self, request):
        try:
            job_binaries = saharaclient.job_binary_internal_list(request)
        except Exception:
            exceptions.handle(request,
                              _("Failed to get list of internal binaries."))
            job_binaries = []

        choices = [(job_binary.id, job_binary.name)
                   for job_binary in job_binaries]
        choices.insert(0, (self.NEW_SCRIPT, '*Create a script'))
        choices.insert(0, (self.UPLOAD_BIN, '*Upload a new file'))

        return choices

    def handle(self, request, context):
        try:
            extra = {}
            jb_type = context.get("job_binary_type")

            if jb_type != "s3":
                bin_url = "%s://%s" % (context["job_binary_type"],
                                       context["job_binary_url"])
            else:
                bin_url = "%s://%s" % (context["job_binary_type"],
                                       context["job_binary_s3_url"])
            if(jb_type == "internal-db"):
                bin_url = self.handle_internal(request, context)
            elif(jb_type == "swift"):
                extra = self.handle_swift(request, context)
            elif(jb_type == "s3"):
                extra = self.handle_s3(request, context)
            elif(jb_type == "manila"):
                bin_url = "%s://%s%s" % (context["job_binary_type"],
                                         context["job_binary_manila_share"],
                                         context["job_binary_manila_path"])

            bin_object = saharaclient.job_binary_create(
                request,
                context["job_binary_name"],
                bin_url,
                context["job_binary_description"],
                extra,
                is_public=context['is_public'],
                is_protected=context['is_protected']
            )
            messages.success(request, "Successfully created job binary")
            return bin_object
        except base.APIException as ex:

            exceptions.handle(request, _("Unable to create job binary: %s") %
                              ex.error_message)
            return False

        except Exception:
            exceptions.handle(request, _("Unable to create job binary"))
            return False

    def get_help_text(self, extra_context=None):
        text = ""
        extra_context = extra_context or {}
        if self.help_text_template:
            tmpl = template.loader.get_template(self.help_text_template)
            text += tmpl.render(extra_context, self.request)
        else:
            text += defaultfilters.linebreaks(force_text(self.help_text))
        return defaultfilters.safe(text)

    class Meta(object):
        name = _("Create Job Binary")
        help_text_template = "job_binaries/_create_job_binary_help.html"

    def handle_internal(self, request, context):
        result = ""

        bin_id = context["job_binary_internal"]
        if(bin_id == self.UPLOAD_BIN):
            try:
                result = saharaclient.job_binary_internal_create(
                    request,
                    self.get_unique_binary_name(
                        request, request.FILES["job_binary_file"].name),
                    request.FILES["job_binary_file"].read())
                bin_id = result.id
            except Exception:
                exceptions.handle(request,
                                  _("Unable to upload job binary"))
                return None
        elif(bin_id == self.NEW_SCRIPT):
            try:
                result = saharaclient.job_binary_internal_create(
                    request,
                    self.get_unique_binary_name(
                        request, context["job_binary_script_name"]),
                    context["job_binary_script"])
                bin_id = result.id
            except base.APIException as ex:

                exceptions.handle(
                    request,
                    _("Unable to create job binary: %s") % ex.error_message)
                return None

            except Exception:
                exceptions.handle(request, _("Unable to create job binary"))
                return None

        return "internal-db://%s" % bin_id

    def handle_swift(self, request, context):
        username = context["job_binary_username"]
        password = context["job_binary_password"]

        extra = {
            "user": username,
            "password": password
        }
        return extra

    def handle_s3(self, request, context):
        accesskey = context['job_binary_access_key']
        secretkey = context['job_binary_secret_key']
        endpoint = context['job_binary_s3_endpoint']

        extra = {}
        if accesskey != "":
            extra["accesskey"] = accesskey
        if secretkey != "":
            extra["secretkey"] = secretkey
        if endpoint != "":
            extra["endpoint"] = endpoint

        return extra

    def get_unique_binary_name(self, request, base_name):
        try:
            internals = saharaclient.job_binary_internal_list(request)
        except Exception:
            internals = []
            exceptions.handle(request,
                              _("Failed to fetch internal binary list"))
        names = [internal.name for internal in internals]
        if base_name in names:
            return "%s_%s" % (base_name, uuid.uuid1())
        return base_name


class JobBinaryEditForm(JobBinaryCreateForm):
    FIELD_MAP = {
        'job_binary_description': 'description',
        'job_binary_file': None,
        'job_binary_internal': None,
        'job_binary_name': 'name',
        'job_binary_password': None,
        'job_binary_script': None,
        'job_binary_script_name': None,
        'job_binary_type': None,
        'job_binary_url': 'url',
        'job_binary_s3_url': 'url',
        'job_binary_username': None,
        'job_binary_manila_share': None,
        'job_binary_manila_path': None,
        'job_binary_access_key': None,
        'job_binary_secret_key': None,
        'job_binary_s3_endpoint': None,
        'is_public': 'is_public',
        'is_protected': 'is_protected',
    }

    def handle(self, request, context):
        try:
            extra = {}
            if context["job_binary_type"] != "s3":
                bin_url = "%s://%s" % (context["job_binary_type"],
                                       context["job_binary_url"])
            else:
                bin_url = "%s://%s" % (context["job_binary_type"],
                                       context["job_binary_s3_url"])

            if (context["job_binary_type"] == "swift"):
                extra = self.handle_swift(request, context)

            if (context["job_binary_type"] == "s3"):
                extra = self.handle_s3(request, context)

            update_data = {
                "name": context["job_binary_name"],
                "description": context["job_binary_description"],
                "extra": extra,
                "url": bin_url,
                'is_public': context['is_public'],
                'is_protected': context['is_protected']
            }

            bin_object = saharaclient.job_binary_update(
                request, self.initial["job_binary"].id, update_data)

            messages.success(request, "Successfully updated job binary")
            return bin_object
        except base.APIException as ex:

            exceptions.handle(request, _("Unable to update job binary: %s") %
                              ex.error_message)
            return False

        except Exception:
            exceptions.handle(request, _("Unable to update job binary"))

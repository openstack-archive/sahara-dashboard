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

from django.forms.util import flatatt
from django.forms import widgets

from django import template
from django.template.defaultfilters import linebreaks
from django.template.defaultfilters import safe
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from horizon import forms
from horizon import messages

from saharaclient.api import base as api_base
from saharadashboard.api import client as saharaclient

import uuid

LOG = logging.getLogger(__name__)


class LabeledInput(widgets.Input):
    def render(self, name, values, attrs=None):
        final_attrs = self.build_attrs(attrs, type=self.input_type, name=name)
        output = "<span id='%s'>%s</span>%s" %\
            ("id_%s_label" % name,
             "savanna-db://",
             ('<input%s />' % flatatt(final_attrs)))
        return mark_safe(output)


class JobBinaryCreateForm(forms.SelfHandlingForm):
    NEW_SCRIPT = "%%%NEWSCRIPT%%%"
    UPLOAD_BIN = "%%%UPLOADFILE%%%"

    job_binary_name = forms.CharField(label=_("Name"),
                                      required=True)

    job_binary_type = forms.ChoiceField(label=_("Storage type"),
                                        required=True)

    job_binary_url = forms.CharField(label=_("URL"),
                                     required=False,
                                     widget=LabeledInput())
    job_binary_internal = forms.ChoiceField(label=_("Internal binary"),
                                            required=False)

    job_binary_file = forms.FileField(label=_("Upload File"),
                                      required=False)

    job_binary_script_name = forms.CharField(label=_("Script name"),
                                             required=False)

    job_binary_script = forms.CharField(label=_("Script text"),
                                        required=False,
                                        widget=forms.Textarea())

    job_binary_username = forms.CharField(label=_("Username"),
                                          required=False)

    job_binary_password = forms.CharField(label=_("Password"),
                                          required=False,
                                          widget=forms.PasswordInput(
                                              attrs={'autocomplete': 'off'}))

    job_binary_description = forms.CharField(label=_("Description"),
                                             required=False,
                                             widget=forms.Textarea())

    def __init__(self, request, *args, **kwargs):
        super(JobBinaryCreateForm, self).__init__(request, *args, **kwargs)

        self.help_text_template = "job_binaries/_create_job_binary_help.html"

        self.fields["job_binary_type"].choices =\
            [("savanna-db", "Internal database"),
             ("swift", "Swift")]

        self.fields["job_binary_internal"].choices =\
            self.populate_job_binary_internal_choices(request)

    def populate_job_binary_internal_choices(self, request):
        sahara = saharaclient.client(request)
        job_binaries = sahara.job_binary_internals.list()

        choices = [(job_binary.id, job_binary.name)
                   for job_binary in job_binaries]
        choices.insert(0, (self.NEW_SCRIPT, '*Create a script'))
        choices.insert(0, (self.UPLOAD_BIN, '*Upload a new file'))

        return choices

    def handle(self, request, context):
        try:
            sahara = saharaclient.client(request)
            extra = {}
            bin_url = "%s://%s" % (context["job_binary_type"],
                                   context["job_binary_url"])
            if(context["job_binary_type"] == "savanna-db"):
                bin_url = self.handle_internal(request, context)
            elif(context["job_binary_type"] == "swift"):
                extra = self.handle_swift(request, context)

            sahara.job_binaries.create(
                context["job_binary_name"],
                bin_url,
                context["job_binary_description"],
                extra)
            messages.success(request, "Successfully created job binary")
            return True
        except api_base.APIException as e:
            messages.error(request, str(e))
            return False
        except Exception as e:
            messages.error(request, str(e))
            return False

    def get_help_text(self, extra_context=None):
        text = ""
        extra_context = extra_context or {}
        if self.help_text_template:
            tmpl = template.loader.get_template(self.help_text_template)
            context = template.RequestContext(self.request, extra_context)
            text += tmpl.render(context)
        else:
            text += linebreaks(force_unicode(self.help_text))
        return safe(text)

    class Meta:
        name = _("Create Job Binary")
        help_text_template = \
            ("job_binaries/_create_job_binary_help.html")

    def handle_internal(self, request, context):
        result = ""
        sahara = saharaclient.client(request)

        bin_id = context["job_binary_internal"]
        if(bin_id == self.UPLOAD_BIN):
            result = sahara.job_binary_internals.create(
                self.get_unique_binary_name(
                    request, request.FILES["job_binary_file"].name),
                request.FILES["job_binary_file"].read())
        elif(bin_id == self.NEW_SCRIPT):
            result = sahara.job_binary_internals.create(
                self.get_unique_binary_name(
                    request, context["job_binary_script_name"]),
                context["job_binary_script"])

        bin_id = result.id
        return "savanna-db://%s" % bin_id

    def handle_swift(self, request, context):
        username = context["job_binary_username"]
        password = context["job_binary_password"]

        extra = {
            "user": username,
            "password": password
        }
        return extra

    def get_unique_binary_name(self, request, base_name):
        sahara = saharaclient.client(request)
        internals = sahara.job_binary_internals.list()
        names = [internal.name for internal in internals]
        if base_name in names:
            return "%s_%s" % (base_name, uuid.uuid1())
        return base_name

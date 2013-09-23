# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from horizon import forms
from horizon import messages

import savannadashboard.api.base as api_base
from savannadashboard.api import client as savannaclient

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
    job_binary_name = forms.CharField(label=_("Name"),
                                      required=True)

    job_binary_type = forms.ChoiceField(label=_("Type"),
                                        required=True)

    job_binary_url = forms.CharField(label=_("URL"),
                                     required=False,
                                     widget=LabeledInput())
    job_binary_savanna_internal = forms.ChoiceField(label=_("Savanna binary"),
                                                    required=False)

    job_binary_file = forms.FileField(label=_("Upload File"),
                                      required=False)

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

        self.fields["job_binary_type"].choices =\
            [("savanna-db", "Savanna internal database"),
             ("swift-internal", "Swift internal"),
             ("swift-external", "Swift external")]

        self.fields["job_binary_savanna_internal"].choices =\
            self.populate_job_binary_savanna_internal_choices(request)

    def populate_job_binary_savanna_internal_choices(self, request):
        savanna = savannaclient.Client(request)
        job_binaries = savanna.job_binaries_internal.list()

        choices = [(job_binary.id, job_binary.name)
                   for job_binary in job_binaries]
        choices.insert(0, ('', 'Upload a new file'))

        return choices

    def handle(self, request, context):
        try:
            savanna = savannaclient.Client(request)
            extra = {}
            bin_url = "%s://%s" % (context["job_binary_type"],
                                   context["job_binary_url"])
            if(context["job_binary_type"] == "savanna-db"):
                bin_url = self.handle_savanna(request, context)
            if(context["job_binary_type"] == "swift-internal"):
                extra = self.handle_swift_internal(request, context)

            savanna.job_binaries.create(
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

    class Meta:
        name = _("Create Job Binary")
        help_text_template = \
            ("job_binaries/_create_job_binary_help.html")

    def handle_savanna(self, request, context):
        savanna = savannaclient.Client(request)

        bin_id = context["job_binary_savanna_internal"]
        if(bin_id == ""):
            result = savanna.job_binaries_internal.create(
                self.get_unique_binary_name(
                    request, request.FILES["job_binary_file"].name),
                request.FILES["job_binary_file"].read())
            bin_id = result["job_binary_internal"]["id"]

        return "savanna-db://%s" % bin_id

    def handle_swift_internal(self, request, context):
        username = context["job_binary_username"]
        password = context["job_binary_password"]

        extra = {
            "user": username,
            "password": password
        }
        return extra

    def get_unique_binary_name(self, request, base_name):
        savanna = savannaclient.Client(request)
        internals = savanna.job_binaries_internal.list()
        names = [internal.name for internal in internals]
        if base_name in names:
            return "%s_%s" % (base_name, uuid.uuid1())
        return base_name

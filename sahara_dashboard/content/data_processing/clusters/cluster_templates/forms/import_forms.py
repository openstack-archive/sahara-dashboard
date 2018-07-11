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
from oslo_serialization import jsonutils as json

from horizon import exceptions
from horizon import forms
from saharaclient.api import base as api_base

from sahara_dashboard.api import sahara as saharaclient
import sahara_dashboard.content.data_processing. \
    utils.workflow_helpers as whelpers
from sahara_dashboard import utils

BASE_IMAGE_URL = "horizon:project:data_processing.clusters:register"


class ImportClusterTemplateFileForm(forms.SelfHandlingForm):

    class Meta(object):
        name = _("Import Cluster Template")

    def __init__(self, *args, **kwargs):
        self.next_view = kwargs.pop("next_view")
        super(ImportClusterTemplateFileForm, self).__init__(
            *args, **kwargs)

    template_upload = forms.FileField(
        label=_("Template File"),
        required=True)

    def handle(self, request, data):
        kwargs = {"template_upload": data["template_upload"]}
        request.method = "GET"
        return self.next_view.as_view()(request, **kwargs)


class ImportClusterTemplateNameForm(forms.SelfHandlingForm):

    class Meta(object):
        name = _("Import Cluster Template")

    template_upload = forms.CharField(
        widget=forms.widgets.HiddenInput)

    name = forms.CharField(label=_("Name"),
                           required=False,
                           help_text=_("Name must be provided "
                                       "either here or in the template. If "
                                       "provided in both places, this one "
                                       "will be used."))

    def __init__(self, *args, **kwargs):
        try:
            request = args[0]
            template_string = ""
            self.next_view = kwargs.pop("next_view")

            if "template_upload" in kwargs:
                template_upload = kwargs.pop("template_upload")
                super(ImportClusterTemplateNameForm, self).__init__(
                    *args, **kwargs)

                template_string = template_upload.read()
                self.fields["template_upload"].initial = template_string

            else:
                super(ImportClusterTemplateNameForm, self).__init__(
                    *args, **kwargs)
        except (ValueError, KeyError):
            raise exceptions.BadRequest(_("Could not parse template"))
        except Exception:
            exceptions.handle(request)

    def handle(self, request, data):
        template = data["template_upload"]
        if data["name"]:
            template = json.loads(template)
            template["cluster_template"]["name"] = data["name"]
            template = json.dumps(template)
        kwargs = {"template_upload": template}
        request.method = "GET"
        return self.next_view.as_view()(request, **kwargs)


class ImportClusterTemplateNodegroupsForm(forms.SelfHandlingForm):

    class Meta(object):
        name = _("Import Cluster Template")

    template_upload = forms.CharField(
        widget=forms.widgets.HiddenInput)
    hidden_nodegroups_field = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={"class": "hidden_nodegroups_field"}))
    forms_ids = forms.CharField(
        required=False,
        widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        try:
            request = args[0]
            template_string = ""

            if "template_upload" in kwargs:
                template_string = kwargs.pop("template_upload")
                super(ImportClusterTemplateNodegroupsForm, self).__init__(
                    *args, **kwargs)

                self.fields["template_upload"].initial = template_string

            else:
                super(ImportClusterTemplateNodegroupsForm, self).__init__(
                    *args, **kwargs)
                template_string = self.data["template_upload"]

            template_json = json.loads(template_string)
            template_json = template_json["cluster_template"]

            req = request.GET.copy()
            req.update(request.POST)

            plugin = template_json["plugin_name"]
            version = (template_json.get("hadoop_version", None) or
                       template_json["plugin_version"])

            if not plugin or not version:
                self.templates = saharaclient.nodegroup_template_find(request)
            else:
                self.templates = saharaclient.nodegroup_template_find(
                    request, plugin_name=plugin, hadoop_version=version)

            deletable = req.get("deletable", dict())

            if "forms_ids" in req:
                self.groups = []
                for id in json.loads(req["forms_ids"]):
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

        except (ValueError, KeyError):
            raise exceptions.BadRequest(_("Could not parse template"))
        except Exception:
            exceptions.handle(request)

    def handle(self, request, data):
        try:
            template = data["template_upload"]
            template = json.loads(template)
            template = template["cluster_template"]

            if "name" not in template.keys():
                return False

            if "neutron_management_network" in template:
                template["net_id"] = (
                    template.pop("neutron_management_network"))

            # default_image_id is not supported by the client now
            if "default_image_id" in template:
                template.pop("default_image_id")

            node_groups = []
            ids = json.loads(data['forms_ids'])
            for id in ids:
                name = data['group_name_' + str(id)]
                template_id = data['template_id_' + str(id)]
                count = data['count_' + str(id)]

                raw_ng = data.get("serialized_" + str(id))

                if raw_ng and raw_ng != 'null':
                    ng = json.loads(utils.deserialize(str(raw_ng)))
                else:
                    ng = dict()
                ng["name"] = name
                ng["count"] = count
                if template_id and template_id != u'None':
                    ng["node_group_template_id"] = template_id
                node_groups.append(ng)

            template["node_groups"] = node_groups

            saharaclient.cluster_template_create(request, **template)
            return True
        except api_base.APIException as e:
            self.error_description = str(e)
            return False
        except Exception as e:
            if isinstance(e, TypeError):
                raise exceptions.BadRequest(
                    _("Template JSON contained invalid key"))
            else:
                raise exceptions.BadRequest(_("Could not parse template"))

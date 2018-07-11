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
from openstack_dashboard.api import neutron
from openstack_dashboard.dashboards.project.instances \
    import utils as nova_utils
from oslo_serialization import jsonutils as json
from saharaclient.api import base as api_base

from sahara_dashboard.api import sahara as saharaclient

BASE_IMAGE_URL = "horizon:project:data_processing.clusters:register"


class ImportNodegroupTemplateFileForm(forms.SelfHandlingForm):

    class Meta(object):
        name = _("Import Node Group Template")

    def __init__(self, *args, **kwargs):
        self.next_view = kwargs.pop('next_view')
        super(ImportNodegroupTemplateFileForm, self).__init__(
            *args, **kwargs)

    template_upload = forms.FileField(
        label=_('Template File'),
        required=True)

    def handle(self, request, data):
        kwargs = {'template_upload': data['template_upload']}
        request.method = 'GET'
        return self.next_view.as_view()(request, **kwargs)


class ImportNodegroupTemplateDetailsForm(forms.SelfHandlingForm):

    class Meta(object):
        name = _("Import Node Group Template")

    template = forms.CharField(
        widget=forms.widgets.HiddenInput)

    name = forms.CharField(label=_("Name"),
                           required=False,
                           help_text=_("Name must be provided "
                                       "either here or in the template. If "
                                       "provided in both places, this one "
                                       "will be used."))

    security_groups = forms.MultipleChoiceField(
        label=_("Security Groups"),
        widget=forms.CheckboxSelectMultiple(),
        help_text=_("Launch instances in these security groups. "
                    "Auto security group will be determined by the "
                    "value present in the imported template."),
        required=False)

    floating_ip_pool = forms.ChoiceField(
        label=_("Floating IP Pool"),
        required=False)

    flavor = forms.ChoiceField(label=_("OpenStack Flavor"))

    image_id = forms.DynamicChoiceField(label=_("Base Image"),
                                        add_item_link=BASE_IMAGE_URL)

    def _populate_image_choices(self, request, plugin, hadoop_version):
        all_images = saharaclient.image_list(request)
        details = saharaclient.plugin_get_version_details(request,
                                                          plugin,
                                                          hadoop_version)
        return [(image.id, image.name) for image in all_images
                if (set(details.required_image_tags).
                issubset(set(image.tags)))]

    def __init__(self, *args, **kwargs):
        try:
            request = args[0]
            template_string = ""

            if "template_upload" in kwargs:
                template_upload = kwargs.pop('template_upload')
                super(ImportNodegroupTemplateDetailsForm, self).__init__(
                    *args, **kwargs)

                template_string = template_upload.read()
                self.fields["template"].initial = template_string

            else:
                super(ImportNodegroupTemplateDetailsForm, self).__init__(
                    *args, **kwargs)
                template_string = self.data["template"]

            template_json = json.loads(template_string)
            template_json = template_json["node_group_template"]

            security_group_list = neutron.security_group_list(request)
            security_group_choices = \
                [(sg.id, sg.name) for sg in security_group_list]
            self.fields["security_groups"].choices = security_group_choices

            pools = neutron.floating_ip_pools_list(request)
            pool_choices = [(pool.id, pool.name) for pool in pools]
            pool_choices.insert(0, (None, "Do not assign floating IPs"))
            self.fields["floating_ip_pool"].choices = pool_choices

            flavors = nova_utils.flavor_list(request)
            if flavors:
                self.fields["flavor"].choices = nova_utils.sort_flavor_list(
                    request, flavors)
            else:
                self.fields["flavor"].choices = []

            version = (template_json.get("hadoop_version", None) or
                       template_json["plugin_version"])
            self.fields["image_id"].choices = \
                self._populate_image_choices(request,
                                             template_json["plugin_name"],
                                             version)
        except (ValueError, KeyError):
            raise exceptions.BadRequest(_("Could not parse template"))
        except Exception:
            exceptions.handle(request)

    def handle(self, request, data):
        try:
            template = data["template"]
            template = json.loads(template)
            template = template["node_group_template"]

            if not data["name"] and "name" not in template.keys():
                return False
            if data["name"]:
                template["name"] = data["name"]

            template["security_groups"] = data["security_groups"]
            template["floating_ip_pool"] = data["floating_ip_pool"]
            template["flavor_id"] = data["flavor"]
            template["image_id"] = data["image_id"]

            saharaclient.nodegroup_template_create(request, **template)
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

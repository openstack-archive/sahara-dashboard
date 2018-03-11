# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django import http
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views import generic

from horizon import forms
from horizon import views as horizon_views

from sahara_dashboard.api import sahara as saharaclient
from sahara_dashboard.content.data_processing.utils \
    import helpers
import sahara_dashboard.content. \
    data_processing.clusters.image_registry.views as imgviews
import sahara_dashboard.content.data_processing.clusters.wizard \
    .forms as wizforms


class ClusterGuideView(horizon_views.APIView):
    template_name = 'cluster_wizard/cluster_guide.html'
    page_title = _("Guided Cluster Creation")

    def show_existing_templates(self):
        try:
            plugin = self.request.session.get("plugin_name", None)
            version = self.request.session.get("plugin_version", None)
            data = saharaclient.nodegroup_template_find(
                self.request, plugin_name=plugin, hadoop_version=version)
            if len(data) < 1:
                return False
            return True
        except Exception:
            return True


class ResetClusterGuideView(generic.RedirectView):
    pattern_name = 'horizon:project:data_processing.clusters:cluster_guide'
    permanent = True

    def get(self, request, *args, **kwargs):
        if kwargs["reset_cluster_guide"]:
            hlps = helpers.Helpers(request)
            hlps.reset_guide()
        return http.HttpResponseRedirect(reverse_lazy(self.pattern_name))


class ImageRegisterView(imgviews.RegisterImageView):
    success_url = reverse_lazy(
        'horizon:project:data_processing.clusters:cluster_guide')

    def get_context_data(self, **kwargs):
        context = super(ImageRegisterView, self).get_context_data(**kwargs)
        context['action_url'] = ('horizon:project'
                                 ':data_processing.clusters:image_register')
        return context


class PluginSelectView(forms.ModalFormView):
    form_class = wizforms.ChoosePluginForm
    success_url = reverse_lazy(
        'horizon:project:data_processing.clusters:cluster_guide')
    classes = ("ajax-modal")
    template_name = "cluster_wizard/plugin_select.html"
    page_title = _("Choose plugin and version")


class NodeGroupSelectView(forms.ModalFormView):
    form_class = wizforms.ChooseTemplateForm
    success_url = reverse_lazy(
        'horizon:project:data_processing.clusters:cluster_guide')
    classes = ("ajax-modal")
    template_name = "cluster_wizard/ngt_select.html"
    page_title = _("Choose node group template")

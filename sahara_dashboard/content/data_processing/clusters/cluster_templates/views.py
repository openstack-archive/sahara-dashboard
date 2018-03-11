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

from django.urls import reverse
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tabs
from horizon.utils import memoized
from horizon import workflows

from sahara_dashboard.api import sahara as saharaclient
import sahara_dashboard.content.data_processing.clusters. \
    cluster_templates.tables as ct_tables
import sahara_dashboard.content.data_processing.clusters. \
    cluster_templates.tabs as _tabs
import sahara_dashboard.content.data_processing.clusters. \
    cluster_templates.workflows.copy as copy_flow
import sahara_dashboard.content.data_processing.clusters. \
    cluster_templates.workflows.create as create_flow
import sahara_dashboard.content.data_processing.clusters. \
    cluster_templates.workflows.edit as edit_flow
import sahara_dashboard.content.data_processing.clusters. \
    cluster_templates.forms.import_forms as import_forms


class ClusterTemplateDetailsView(tabs.TabView):
    tab_group_class = _tabs.ClusterTemplateDetailsTabs
    template_name = 'horizon/common/_detail.html'
    page_title = "{{ template.name|default:template.id }}"

    @memoized.memoized_method
    def get_object(self):
        ct_id = self.kwargs["template_id"]
        try:
            return saharaclient.cluster_template_get(self.request, ct_id)
        except Exception:
            msg = _('Unable to retrieve details for '
                    'cluster template "%s".') % ct_id
            redirect = self.get_redirect_url()
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super(ClusterTemplateDetailsView, self)\
            .get_context_data(**kwargs)
        cluster_template = self.get_object()
        context['template'] = cluster_template
        context['url'] = self.get_redirect_url()
        context['actions'] = self._get_actions(cluster_template)
        return context

    def _get_actions(self, cluster_template):
        table = ct_tables.ClusterTemplatesTable(self.request)
        return table.render_row_actions(cluster_template)

    @staticmethod
    def get_redirect_url():
        return reverse("horizon:project:data_processing."
                       "clusters:index")


class CreateClusterTemplateView(workflows.WorkflowView):
    workflow_class = create_flow.CreateClusterTemplate
    success_url = ("horizon:project:data_processing.clusters"
                   ":create-cluster-template")
    classes = ("ajax-modal",)
    template_name = "cluster_templates/create.html"
    page_title = _("Create Cluster Template")


class ConfigureClusterTemplateView(workflows.WorkflowView):
    workflow_class = create_flow.ConfigureClusterTemplate
    success_url = ("horizon:project:data_processing.clusters"
                   ":index")
    template_name = "cluster_templates/configure.html"
    page_title = _("Configure Cluster Template")


class CopyClusterTemplateView(workflows.WorkflowView):
    workflow_class = copy_flow.CopyClusterTemplate
    success_url = ("horizon:project:data_processing.clusters"
                   ":index")
    template_name = "cluster_templates/configure.html"
    page_title = _("Copy Cluster Template")

    def get_context_data(self, **kwargs):
        context = super(CopyClusterTemplateView, self)\
            .get_context_data(**kwargs)

        context["template_id"] = kwargs["template_id"]
        return context

    def get_object(self, *args, **kwargs):
        if not hasattr(self, "_object"):
            template_id = self.kwargs['template_id']
            try:
                template = saharaclient.cluster_template_get(self.request,
                                                             template_id)
            except Exception:
                template = {}
                exceptions.handle(self.request,
                                  _("Unable to fetch cluster template."))
            self._object = template
        return self._object

    def get_initial(self):
        initial = super(CopyClusterTemplateView, self).get_initial()
        initial['template_id'] = self.kwargs['template_id']
        return initial


class EditClusterTemplateView(CopyClusterTemplateView):
    workflow_class = edit_flow.EditClusterTemplate
    success_url = ("horizon:project:data_processing.clusters"
                   ":index")
    template_name = "cluster_templates/configure.html"


class ImportClusterTemplateFileView(forms.ModalFormView):
    template_name = "cluster_templates/import.html"
    form_class = import_forms.ImportClusterTemplateFileForm
    submit_label = _("Next")
    submit_url = reverse_lazy("horizon:project:data_processing."
                              "clusters:import-cluster-template-file")
    success_url = reverse_lazy("horizon:project:data_processing."
                               "clusters:import-cluster-template-name")
    page_title = _("Import Cluster Template")

    def get_form_kwargs(self):
        kwargs = super(ImportClusterTemplateFileView, self).get_form_kwargs()
        kwargs['next_view'] = ImportClusterTemplateNameView
        return kwargs


class ImportClusterTemplateNameView(forms.ModalFormView):
    template_name = "cluster_templates/import.html"
    form_class = import_forms.ImportClusterTemplateNameForm
    submit_label = _("Next")
    submit_url = reverse_lazy("horizon:project:data_processing."
                              "clusters:import-cluster-template-name")
    success_url = reverse_lazy("horizon:project:data_processing."
                               "clusters:import-cluster-template-nodegroups")
    page_title = _("Import Cluster Template")

    def get_form_kwargs(self):
        kwargs = super(ImportClusterTemplateNameView, self).get_form_kwargs()
        kwargs['next_view'] = ImportClusterTemplateNodegroupsView
        if 'template_upload' in self.kwargs:
            kwargs['template_upload'] = self.kwargs['template_upload']
        return kwargs


class ImportClusterTemplateNodegroupsView(forms.ModalFormView):
    template_name = "cluster_templates/import_nodegroups.html"
    # template_name = "some_random_stuff.html"
    form_class = import_forms.ImportClusterTemplateNodegroupsForm
    submit_label = _("Import")
    submit_url = reverse_lazy("horizon:project:data_processing."
                              "clusters:import-cluster-template-nodegroups")
    success_url = reverse_lazy("horizon:project:data_processing."
                               "clusters:index")
    page_title = _("Import Cluster Template")

    def get_form_kwargs(self):
        kwargs = super(ImportClusterTemplateNodegroupsView,
                       self).get_form_kwargs()
        if 'template_upload' in self.kwargs:
            kwargs['template_upload'] = self.kwargs['template_upload']
        return kwargs

from django.utils.translation import ugettext_lazy as _
from horizon import exceptions
from horizon import forms

from savannadashboard.api import client as savannaclient
from savannadashboard.utils import workflow_helpers


class UploadFileForm(forms.SelfHandlingForm,
                     workflow_helpers.PluginAndVersionMixin):
    template_name = forms.CharField(max_length=80,
                                    label=_("Cluster Template Name"))

    def __init__(self, request, *args, **kwargs):
        super(UploadFileForm, self).__init__(request, *args, **kwargs)

        savanna = savannaclient.Client(request)
        self._generate_plugin_version_fields(savanna)

        self.fields['template_file'] = forms.FileField(label=_("Template"),
                                                       required=True)

    def handle(self, request, data):
        try:
            # we can set a limit on file size, but should we?
            filecontent = self.files['template_file'].read()

            plugin_name = data['plugin_name']
            hadoop_version = data.get(plugin_name + "_version")

            savanna = savannaclient.Client(request)
            savanna.plugins.convert_to_cluster_template(plugin_name,
                                                        hadoop_version,
                                                        filecontent)
            return True
        except Exception:
            exceptions.handle(request)
            return False

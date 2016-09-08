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
from horizon import tabs

from sahara_dashboard.api import sahara as saharaclient
from sahara_dashboard.content.data_processing.clusters.image_registry \
    import tables as image_registry_tables


class ImageRegistryTab(tabs.TableTab):
    table_classes = (image_registry_tables.ImageRegistryTable, )
    name = _("Image Registry")
    slug = "image_registry_tab"
    template_name = "horizon/common/_detail_table.html"

    def get_image_registry_data(self):
        try:
            images = saharaclient.image_list(self.request)
        except Exception:
            images = []
            msg = _('Unable to retrieve image list')
            exceptions.handle(self.request, msg)
        return images

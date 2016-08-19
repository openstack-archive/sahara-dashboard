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

from horizon import tabs

from sahara_dashboard.content.data_processing.clusters.cluster_templates \
    import tabs as cluster_templates_tabs
from sahara_dashboard.content.data_processing.clusters.clusters \
    import tabs as clusters_tabs
from sahara_dashboard.content.data_processing.clusters.image_registry \
    import tabs as image_registry_tabs
from sahara_dashboard.content.data_processing.clusters.nodegroup_templates \
    import tabs as node_group_templates_tabs
from sahara_dashboard.content.data_processing.tabs \
    import PaginationFriendlyTabGroup


class ClusterTabs(PaginationFriendlyTabGroup):
    slug = "cluster_tabs"
    tabs = (clusters_tabs.ClustersTab,
            cluster_templates_tabs.ClusterTemplatesTab,
            node_group_templates_tabs.NodeGroupTemplatesTab,
            image_registry_tabs.ImageRegistryTab,)
    sticky = True


class IndexView(tabs.TabbedTableView):
    tab_group_class = ClusterTabs
    template_name = "clusters/index.html"
    page_title = _("Clusters")

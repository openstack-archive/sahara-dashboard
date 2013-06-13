import logging

from horizon.api import base

from savannadashboard.api import cluster_templates
from savannadashboard.api import clusters
from savannadashboard.api import httpclient
from savannadashboard.api import images
from savannadashboard.api import node_group_templates
from savannadashboard.api import plugins

LOG = logging.getLogger(__name__)


def get_horizon_parameter(name, default_value):
    import openstack_dashboard.settings

    if hasattr(openstack_dashboard.settings, name):
        return getattr(openstack_dashboard.settings, name)
    else:
        logging.info('Parameter %s is not found in local_settings.py, '
                     'using default "%s"' % (name, default_value))
        return default_value


# Both parameters should be defined in Horizon's local_settings.py
# Example SAVANNA_URL - http://localhost:9000/v1.0
SAVANNA_URL = get_horizon_parameter('SAVANNA_URL', None)
# "type" of Savanna service registered in keystone
SAVANNA_SERVICE = get_horizon_parameter('SAVANNA_SERVICE', 'mapreduce')


def get_savanna_url(request):
    if SAVANNA_URL is not None:
        return SAVANNA_URL + '/' + request.user.tenant_id

    return base.url_for(request, SAVANNA_SERVICE)


class Client(object):
    def __init__(self, request):
        self.client = httpclient.HTTPClient(get_savanna_url(request),
                                            request.user.token.id)

        self.clusters = clusters.ClusterManager(self)
        self.cluster_templates = cluster_templates.ClusterTemplateManager(self)
        self.node_group_templates = (node_group_templates.
                                     NodeGroupTemplateManager(self))
        self.plugins = plugins.PluginManager(self)
        self.images = images.ImageManager(self)

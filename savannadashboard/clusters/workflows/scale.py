# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2013 Mirantis Inc.
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

import json
import logging

from django.utils.translation import ugettext as _
from horizon import exceptions

from savannadashboard.api import client as savannaclient

import savannadashboard.cluster_templates.workflows.create as clt_create_flow
import savannadashboard.clusters.workflows.create as cl_create_flow
from savannadashboard.utils.workflow_helpers import build_node_group_fields


LOG = logging.getLogger(__name__)


class NodeGroupsStep(clt_create_flow.ConfigureNodegroups):
    pass


class ScaleCluster(cl_create_flow.ConfigureCluster):
    slug = "scale_cluster"
    name = _("Scale Cluster")
    finalize_button_name = _("Scale")
    success_url = "horizon:savanna:clusters:index"
    default_steps = (NodeGroupsStep, )

    def __init__(self, request, context_seed, entry_point, *args, **kwargs):
        ScaleCluster._cls_registry = set([])

        savanna = savannaclient.Client(request)

        cluster_id = context_seed["cluster_id"]
        cluster = savanna.clusters.get(cluster_id)

        self.success_message = "Scaling cluster started for %s" % cluster.name
        self.failure_message = "Could not start scaling for %s" % cluster.name

        plugin = cluster.plugin_name
        hadoop_version = cluster.hadoop_version

        #init deletable nodegroups
        deletable = dict()
        for group in cluster.node_groups:
            deletable[group["name"]] = "false"

        request.GET = request.GET.copy()
        request.GET.update({"cluster_id": cluster_id})
        request.GET.update({"plugin_name": plugin})
        request.GET.update({"hadoop_version": hadoop_version})
        request.GET.update({"deletable": deletable})

        super(ScaleCluster, self).__init__(request, context_seed,
                                           entry_point, *args,
                                           **kwargs)

        #init Node Groups

        for step in self.steps:
            if isinstance(step, clt_create_flow.ConfigureNodegroups):
                ng_action = step.action
                template_ngs = cluster.node_groups

                if 'forms_ids' not in request.POST:
                    ng_action.groups = []
                    for id in range(0, len(template_ngs), 1):
                        group_name = "group_name_" + str(id)
                        template_id = "template_id_" + str(id)
                        count = "count_" + str(id)
                        templ_ng = template_ngs[id]
                        ng_action.groups.append(
                            {"name": templ_ng["name"],
                             "template_id": templ_ng["node_group_template_id"],
                             "count": templ_ng["count"],
                             "id": id,
                             "deletable": "false"})

                        build_node_group_fields(ng_action,
                                                group_name,
                                                template_id,
                                                count)

    def format_status_message(self, message):
        return message

    def handle(self, request, context):
        savanna = savannaclient.Client(request)
        cluster_id = request.GET["cluster_id"]
        cluster = savanna.clusters.get(cluster_id)

        existing_node_groups = set([])
        for ng in cluster.node_groups:
            existing_node_groups.add(ng["name"])

        scale_object = dict()

        ids = json.loads(context["ng_forms_ids"])

        for _id in ids:
            name = context["ng_group_name_%s" % _id]
            template_id = context["ng_template_id_%s" % _id]
            count = context["ng_count_%s" % _id]

            if name not in existing_node_groups:
                if "add_node_groups" not in scale_object:
                    scale_object["add_node_groups"] = []

                scale_object["add_node_groups"].append(
                    {"name": name,
                     "node_group_template_id": template_id,
                     "count": int(count)})
            else:
                old_count = None
                for ng in cluster.node_groups:
                    if name == ng["name"]:
                        old_count = ng["count"]
                        break

                if old_count != count:
                    if "resize_node_groups" not in scale_object:
                        scale_object["resize_node_groups"] = []

                    scale_object["resize_node_groups"].append(
                        {"name": name,
                         "count": int(count)}
                    )
        try:
            savanna.clusters.scale(cluster_id, scale_object)
            return True
        except Exception:
            exceptions.handle(request)
            return False

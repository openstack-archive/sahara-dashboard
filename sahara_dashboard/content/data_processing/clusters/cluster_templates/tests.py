# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import copy

from django.urls import reverse
from oslo_serialization import jsonutils

from openstack_dashboard import api as dash_api

from sahara_dashboard import api
from sahara_dashboard.test import helpers as test
from sahara_dashboard import utils


INDEX_URL = reverse('horizon:project:data_processing.clusters:'
                    'cluster-templates-tab')
DETAILS_URL = reverse(
    'horizon:project:data_processing.clusters:ct-details', args=['id'])


class DataProcessingClusterTemplateTests(test.TestCase):

    @test.create_mocks({api.sahara: ('cluster_template_list',
                                     'image_list',
                                     'cluster_list',
                                     'nodegroup_template_list')})
    def test_index(self):
        self.mock_cluster_template_list.return_value = \
            self.cluster_templates.list()
        res = self.client.get(INDEX_URL)
        self.mock_cluster_template_list.assert_called_once_with(
            test.IsHttpRequest(), {})
        self.assertTemplateUsed(res, 'clusters/index.html')
        self.assertContains(res, 'Cluster Templates')
        self.assertContains(res, 'Name')

    @test.create_mocks({api.sahara: ('cluster_template_get',
                                     'nodegroup_template_get'),
                        dash_api.nova: ('flavor_get',)})
    def test_details(self):
        flavor = self.flavors.first()
        ct = self.cluster_templates.first()
        self.mock_flavor_get.return_value = flavor
        self.mock_cluster_template_get.return_value = ct
        res = self.client.get(DETAILS_URL)
        self.assertTemplateUsed(res, 'horizon/common/_detail.html')

    @test.create_mocks({api.sahara: ('client',
                                     'cluster_template_get',
                                     'plugin_get_version_details',
                                     'nodegroup_template_find')})
    def test_copy(self):
        ct = self.cluster_templates.first()
        ngts = self.nodegroup_templates.list()
        configs = self.plugins_configs.first()
        self.mock_cluster_template_get.return_value = ct
        self.mock_plugin_get_version_details.return_value = configs
        self.mock_nodegroup_template_find.return_value = ngts

        url = reverse('horizon:project:data_processing.clusters:ct-copy',
                      args=[ct.id])
        res = self.client.get(url)
        self.mock_cluster_template_get.assert_called_once_with(
            test.IsHttpRequest(), ct.id)
        workflow = res.context['workflow']
        step = workflow.get_step("generalconfigaction")
        self.assertEqual(step.action['cluster_template_name'].field.initial,
                         ct.name + "-copy")

    @test.create_mocks({api.sahara: ('cluster_template_list',
                                     'cluster_template_delete')})
    def test_delete(self):
        ct = self.cluster_templates.first()
        self.mock_cluster_template_list.return_value = \
            self.cluster_templates.list()
        self.mock_cluster_template_delete.return_value = None

        form_data = {'action': 'cluster_templates__delete__%s' % ct.id}
        res = self.client.post(INDEX_URL, form_data)

        self.mock_cluster_template_list.assert_called_once_with(
            test.IsHttpRequest(), {})
        self.mock_cluster_template_delete.assert_called_once_with(
            test.IsHttpRequest(), ct.id)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)
        self.assertMessageCount(success=1)

    @test.create_mocks({api.sahara: ('client',
                                     'cluster_template_get',
                                     'cluster_template_update',
                                     'plugin_get_version_details',
                                     'nodegroup_template_find')})
    def test_update(self):
        ct = self.cluster_templates.first()
        ngts = self.nodegroup_templates.list()
        configs = self.plugins_configs.first()
        new_name = "UpdatedName"
        new_ct = copy.copy(ct)
        new_ct.name = new_name
        self.mock_cluster_template_get.return_value = ct
        self.mock_plugin_get_version_details.return_value = configs
        self.mock_nodegroup_template_find.return_value = ngts
        self.mock_cluster_template_update.return_value = new_ct

        url = reverse('horizon:project:data_processing.clusters:ct-edit',
                      args=[ct.id])

        def serialize(obj):
            return utils.serialize(jsonutils.dump_as_bytes(obj))

        res = self.client.post(
            url,
            {'ct_id': ct.id,
             'cluster_template_name': new_name,
             'plugin_name': ct.plugin_name,
             'hadoop_version': ct.hadoop_version,
             'description': ct.description,
             'hidden_configure_field': "",
             'template_id_0': ct.node_groups[0]['node_group_template_id'],
             'group_name_0': ct.node_groups[0]['name'],
             'count_0': 1,
             'serialized_0': serialize(ct.node_groups[0]),
             'template_id_1': ct.node_groups[1]['node_group_template_id'],
             'group_name_1': ct.node_groups[1]['name'],
             'count_1': 2,
             'serialized_1': serialize(ct.node_groups[1]),
             'forms_ids': "[0,1]",
             })

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)
        self.assertMessageCount(success=1)
        self.mock_cluster_template_update.assert_called_once_with(
            request=test.IsHttpRequest(),
            ct_id=ct.id,
            name=new_name,
            plugin_name=ct.plugin_name,
            hadoop_version=ct.hadoop_version,
            description=ct.description,
            cluster_configs=ct.cluster_configs,
            node_groups=ct.node_groups,
            anti_affinity=ct.anti_affinity,
            use_autoconfig=False,
            shares=ct.shares,
            is_public=False,
            is_protected=False,
            domain_name=ct.domain_name
        )

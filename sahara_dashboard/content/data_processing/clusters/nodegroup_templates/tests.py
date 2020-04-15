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

from unittest import mock

from django.urls import reverse

from openstack_dashboard import api as dash_api

from sahara_dashboard import api
from sahara_dashboard.content.data_processing.utils \
    import workflow_helpers
from sahara_dashboard.content.data_processing.clusters. \
    nodegroup_templates.workflows import create as create_workflow
from sahara_dashboard.test import helpers as test


INDEX_URL = reverse(
    'horizon:project:data_processing.clusters:nodegroup-templates-tab')
DETAILS_URL = reverse(
    'horizon:project:data_processing.clusters:details',
    args=['id'])
CREATE_URL = reverse(
    'horizon:project:data_processing.clusters:' +
    'configure-nodegroup-template')


class DataProcessingNodeGroupTests(test.TestCase):

    @mock.patch('openstack_dashboard.api.base.is_service_enabled')
    def _setup_copy_test(self, service_checker):
        service_checker.return_value = True
        ngt = self.nodegroup_templates.first()
        configs = self.plugins_configs.first()
        self.mock_extension_supported.return_value = True
        self.mock_availability_zone_list.return_value = \
            self.availability_zones.list()
        self.mock_volume_type_list.return_value = []
        self.mock_nodegroup_template_get.return_value = ngt
        self.mock_plugin_get_version_details.return_value = configs
        self.mock_floating_ip_pools_list.return_value = []
        self.mock_security_group_list.return_value = []

        url = reverse(
            'horizon:project:data_processing.clusters:copy',
            args=[ngt.id])
        res = self.client.get(url)

        self.mock_availability_zone_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_availability_zone_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_volume_type_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_nodegroup_template_get.assert_called_once_with(
            test.IsHttpRequest(), ngt.id)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_plugin_get_version_details, 6,
            mock.call(test.IsHttpRequest(), ngt.plugin_name,
                      ngt.hadoop_version))
        self.mock_floating_ip_pools_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_security_group_list.assert_called_once_with(
            test.IsHttpRequest())

        return ngt, configs, res

    @test.create_mocks({api.sahara: ('cluster_template_list',
                                     'image_list',
                                     'cluster_list',
                                     'nodegroup_template_list')})
    def test_index(self):
        self.mock_nodegroup_template_list.return_value = \
            self.nodegroup_templates.list()
        res = self.client.get(INDEX_URL +
                              "?tab=cluster_tabs__node_group_templates_tab")
        self.assertTemplateUsed(res, 'clusters/index.html')
        self.assertContains(res, 'Node Group Templates')
        self.assertContains(res, 'Name')
        self.assertContains(res, 'Plugin')
        self.mock_nodegroup_template_list.assert_called_once_with(
            test.IsHttpRequest(), {})

    @test.create_mocks({api.sahara: ('nodegroup_template_get',),
                        dash_api.nova: ('flavor_get',)})
    def test_details(self):
        flavor = self.flavors.first()
        ngt = self.nodegroup_templates.first()
        self.mock_flavor_get.return_value = flavor
        self.mock_nodegroup_template_get.return_value = ngt
        res = self.client.get(DETAILS_URL)
        self.assertTemplateUsed(res, 'horizon/common/_detail.html')
        self.assertContains(res, 'sample-template')
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_flavor_get, 1,
            mock.call(test.IsHttpRequest(), flavor.id))

    @test.create_mocks({api.sahara: ('nodegroup_template_list',
                                     'nodegroup_template_delete')})
    def test_delete(self):
        ngt = self.nodegroup_templates.first()
        self.mock_nodegroup_template_list.return_value = \
            self.nodegroup_templates.list()
        self.mock_nodegroup_template_delete.return_value = None

        form_data = {'action': 'nodegroup_templates__delete__%s' % ngt.id}
        res = self.client.post(INDEX_URL, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)
        self.assertMessageCount(success=1)
        self.mock_nodegroup_template_list.assert_called_once_with(
            test.IsHttpRequest(), {})
        self.mock_nodegroup_template_delete.assert_called_once_with(
            test.IsHttpRequest(), ngt.id)

    @test.create_mocks({api.sahara: ('nodegroup_template_get',
                                     'plugin_get_version_details',
                                     'image_list'),
                        dash_api.nova: ('availability_zone_list',
                                        'flavor_list'),
                        dash_api.neutron: ('floating_ip_pools_list',
                                           'security_group_list'),
                        dash_api.cinder: ('extension_supported',
                                          'availability_zone_list',
                                          'volume_type_list')})
    def test_copy(self):
        ngt, configs, res = self._setup_copy_test()
        workflow = res.context['workflow']
        step = workflow.get_step("generalconfigaction")
        self.assertEqual(step.action['nodegroup_name'].field.initial,
                         ngt.name + "-copy")

    @test.create_mocks({api.sahara: ('client',
                                     'nodegroup_template_create',
                                     'plugin_get_version_details'),
                        dash_api.neutron: ('floating_ip_pools_list',
                                           'security_group_list'),
                        dash_api.nova: ('flavor_list',
                                        'availability_zone_list'),
                        dash_api.cinder: ('extension_supported',
                                          'availability_zone_list',
                                          'volume_type_list')})
    @mock.patch('openstack_dashboard.api.base.is_service_enabled')
    @mock.patch.object(workflow_helpers, 'parse_configs_from_context')
    def test_create(self, mock_workflow, service_checker):
        service_checker.return_value = True
        mock_workflow.return_value = {}
        flavor = self.flavors.first()
        ngt = self.nodegroup_templates.first()
        configs = self.plugins_configs.first()
        new_name = ngt.name + '-new'

        self.mock_extension_supported.return_value = True
        self.mock_availability_zone_list.return_value = \
            self.availability_zones.list()
        self.mock_volume_type_list.return_value = []
        self.mock_flavor_list.return_value = [flavor]
        self.mock_plugin_get_version_details.return_value = configs
        self.mock_floating_ip_pools_list.return_value = []
        self.mock_security_group_list.return_value = []
        self.mock_nodegroup_template_create.return_value = True

        res = self.client.post(
            CREATE_URL,
            {'nodegroup_name': new_name,
             'plugin_name': ngt.plugin_name,
             ngt.plugin_name + '_version': '1.2.1',
             'hadoop_version': ngt.hadoop_version,
             'description': ngt.description,
             'flavor': flavor.id,
             'availability_zone': '',
             'storage': 'ephemeral_drive',
             'volumes_per_node': 0,
             'volumes_size': 0,
             'volume_type': '',
             'volume_local_to_instance': False,
             'volumes_availability_zone': '',
             'floating_ip_pool': '',
             'security_autogroup': True,
             'processes': 'HDFS:namenode',
             'use_autoconfig': True,
             'shares': [],
             'is_public': False,
             'is_protected': False})

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)
        self.assertMessageCount(success=1)
        self.mock_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), 'AvailabilityZones')
        self.mock_availability_zone_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_flavor_list.assert_called_once_with(
            test.IsHttpRequest())
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_plugin_get_version_details, 4,
            mock.call(test.IsHttpRequest(), ngt.plugin_name,
                      ngt.hadoop_version))
        self.mock_floating_ip_pools_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_security_group_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_nodegroup_template_create(
            test.IsHttpRequest(),
            **{'name': new_name,
               'plugin_name': ngt.plugin_name,
               'hadoop_version': ngt.hadoop_version,
               'description': ngt.description,
               'flavor_id': flavor.id,
               'volumes_per_node': None,
               'volumes_size': None,
               'volume_type': None,
               'volume_local_to_instance': False,
               'volumes_availability_zone': None,
               'node_processes': ['namenode'],
               'node_configs': {},
               'floating_ip_pool': None,
               'security_groups': [],
               'image_id': None,
               'auto_security_group': True,
               'availability_zone': None,
               'is_proxy_gateway': False,
               'use_autoconfig': True,
               'shares': [],
               'is_public': False,
               'is_protected': False})

    @test.create_mocks({api.sahara: ('client',
                                     'nodegroup_template_create',
                                     'nodegroup_template_update',
                                     'nodegroup_template_get',
                                     'plugin_get_version_details'),
                        dash_api.neutron: ('floating_ip_pools_list',
                                           'security_group_list'),
                        dash_api.nova: ('flavor_list',
                                        'availability_zone_list'),
                        dash_api.cinder: ('extension_supported',
                                          'availability_zone_list',
                                          'volume_type_list')})
    @mock.patch('openstack_dashboard.api.base.is_service_enabled')
    @mock.patch.object(workflow_helpers, 'parse_configs_from_context')
    def test_update(self, mock_workflow, service_checker):
        service_checker.return_value = True
        flavor = self.flavors.first()
        ngt = self.nodegroup_templates.first()
        configs = self.plugins_configs.first()
        new_name = ngt.name + '-updated'
        UPDATE_URL = reverse(
            'horizon:project:data_processing.clusters:edit',
            kwargs={'template_id': ngt.id})
        mock_workflow.return_value = {}

        self.mock_extension_supported.return_value = True
        self.mock_availability_zone_list.return_value = \
            self.availability_zones.list()
        self.mock_volume_type_list.return_value = []
        self.mock_flavor_list.return_value = [flavor]
        self.mock_plugin_get_version_details.return_value = configs
        self.mock_floating_ip_pools_list.return_value = []
        self.mock_security_group_list.return_value = []
        self.mock_nodegroup_template_get.return_value = ngt
        self.mock_nodegroup_template_update.return_value = True

        res = self.client.post(
            UPDATE_URL,
            {'ng_id': ngt.id,
             'nodegroup_name': new_name,
             'plugin_name': ngt.plugin_name,
             ngt.plugin_name + '_version': '1.2.1',
             'hadoop_version': ngt.hadoop_version,
             'description': ngt.description,
             'flavor': flavor.id,
             'availability_zone': '',
             'storage': 'ephemeral_drive',
             'volumes_per_node': 0,
             'volumes_size': 0,
             'volume_type': '',
             'volume_local_to_instance': False,
             'volumes_availability_zone': '',
             'floating_ip_pool': '',
             'is_proxy_gateway': False,
             'security_autogroup': True,
             'processes': 'HDFS:namenode',
             'use_autoconfig': True})

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)
        self.assertMessageCount(success=1)
        self.mock_extension_supported.assert_called_once_with(
            test.IsHttpRequest(), 'AvailabilityZones')
        self.mock_availability_zone_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_volume_type_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_flavor_list.assert_called_once_with(
            test.IsHttpRequest())
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_plugin_get_version_details, 5,
            mock.call(test.IsHttpRequest(), ngt.plugin_name,
                      ngt.hadoop_version))
        self.mock_floating_ip_pools_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_security_group_list.assert_called_once_with(
            test.IsHttpRequest())
        self.mock_nodegroup_template_get.assert_called_once_with(
            test.IsHttpRequest(), ngt.id)
        self.mock_nodegroup_template_update.assert_called_once_with(
            request=test.IsHttpRequest(),
            ngt_id=ngt.id,
            name=new_name,
            plugin_name=ngt.plugin_name,
            hadoop_version=ngt.hadoop_version,
            flavor_id=flavor.id,
            description=ngt.description,
            volumes_per_node=0,
            volumes_size=None,
            volume_type=None,
            volume_local_to_instance=False,
            volumes_availability_zone=None,
            node_processes=['namenode'],
            node_configs={},
            floating_ip_pool='',
            security_groups=[],
            auto_security_group=True,
            availability_zone='',
            use_autoconfig=True,
            is_proxy_gateway=False,
            shares=[],
            is_protected=False,
            is_public=False,
            image_id=ngt.image_id,
        )

    @test.create_mocks({api.sahara: ('nodegroup_template_get',
                                     'plugin_get_version_details',
                                     'image_list'),
                        dash_api.nova: ('availability_zone_list',
                                        'flavor_list'),
                        dash_api.neutron: ('floating_ip_pools_list',
                                           'security_group_list'),
                        dash_api.cinder: ('extension_supported',
                                          'availability_zone_list',
                                          'volume_type_list')})
    def test_workflow_steps(self):
        # since the copy workflow is the child of create workflow
        # it's better to test create workflow through copy workflow
        ngt, configs, res = self._setup_copy_test()
        workflow = res.context['workflow']
        expected_instances = [
            create_workflow.GeneralConfig,
            create_workflow.SelectNodeProcesses,
            create_workflow.SecurityConfig
        ]
        for expected, observed in zip(expected_instances, workflow.steps):
            self.assertIsInstance(observed, expected)

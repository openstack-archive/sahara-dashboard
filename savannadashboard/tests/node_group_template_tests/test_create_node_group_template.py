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

from testtools import testcase
import unittest2

from savannadashboard.tests import base
import savannadashboard.tests.configs.config as cfg


class UICreateNodeGroupTemplate(base.UITestCase):

    @testcase.attr('node_group_template', 'vanilla')
    @unittest2.skipIf(cfg.vanilla.skip_plugin_tests,
                      'tests for vanilla plugin skipped')
    def test_create_node_group_template_vanilla(self):
        self.create_node_group_template(
            "selenium-vanilla", ["NN", "JT"], cfg.vanilla, flavor="m1.small",
            storage={'type': "Cinder Volume", 'volume_per_node': '2',
                     'volume_size': '6'}, description='selenium-test',
            params=[{"HDFS Parameters:Show_param": True},
                    {"hadoop.native.lib": False}, {"Filter": "heap"},
                    {"Name Node Heap Size": 512},
                    {"Data Node Heap Size": 512},
                    {"Show_param": False}, {"Filter": ""},
                    {"dfs.datanode.max.xcievers": 3555},
                    {"MapReduce Parameters:io.sort.mb": 200},
                    {"mapred.child.java.opts": "-Xmx300m"}])
        msg = "Error: NodeGroup template with name 'selenium-vanilla'" \
              " already exists"
        self.create_node_group_template("selenium-vanilla", ["NN", "JT"],
                                        cfg.vanilla, positive=False,
                                        message=msg)
        self.delete_node_group_templates(['selenium-vanilla'])

    @testcase.attr('node_group_template', 'hdp')
    @unittest2.skipIf(cfg.hdp.skip_plugin_tests,
                      'tests for hdp plugin skipped')
    def test_create_node_group_template_hdp(self):
        self.create_node_group_template(
            "sel-hdp", ["NN", "JT", "HDFS_CLIENT", "AMBARI_SERVER",
                        "AMBARI_AGENT"], cfg.hdp,
            flavor="m1.small", storage={'type': "Cinder Volume",
                                        'volume_per_node': '2',
                                        'volume_size': '6'},
            description='selenium-test')
        msg = "Error: NodeGroup template with name 'sel-hdp' already exists"
        self.create_node_group_template("sel-hdp", ["NN", "JT"], cfg.hdp,
                                        positive=False, message=msg)
        self.delete_node_group_templates(['sel-hdp'])

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

import testtools

from savannadashboard.tests import base
import savannadashboard.tests.configs.config as cfg


class UICreateClusterTemplate(base.UITestCase):

    @base.attr(tags=['cluster_template', 'vanilla'])
    @testtools.skipIf(cfg.vanilla.skip_plugin_tests,
                      'tests for vanilla plugin skipped')
    def test_create_cluster_template_for_vanilla(self):
        self.create_node_group_template('selenium-master', ["NN", "JT"],
                                        cfg.vanilla)
        self.create_node_group_template('selenium-worker', ["DN", "TT"],
                                        cfg.vanilla)
        self.create_node_group_template('selenium-delete', ["NN", "OZ"],
                                        cfg.vanilla)
        self.create_cluster_template(
            "selenium-clstr-tmpl", {'selenium-master': 1,
                                    'selenium-worker': 2},
            cfg.vanilla, anti_affinity_groups=["NN", "DN", "TT"], params=
            [{"General Parameters:Enable Swift": False},
             {"HDFS Parameters:dfs.replication": 2},
             {"MapReduce Parameters:mapred.output.compress": False}])
        msg = 'Error: Cluster template with name \'selenium-clstr-tmpl\'' \
            ' already exists'
        self.create_cluster_template('selenium-clstr-tmpl',
                                     {'selenium-delete': 1,
                                      'selenium-worker': 2},
                                     cfg.vanilla, positive=False, message=msg)
        self.delete_node_group_templates(["selenium-master", "selenium-worker",
                                          "selenium-delete"],
                                         undelete_names=["selenium-master",
                                                         "selenium-worker"])
        self.delete_cluster_templates(['selenium-clstr-tmpl'])
        self.delete_node_group_templates(["selenium-master",
                                          "selenium-worker"])

    @base.attr(tags=['cluster_template', 'hdp'])
    @testtools.skipIf(cfg.hdp.skip_plugin_tests,
                      'tests for hdp plugin skipped')
    def test_create_cluster_template_for_hdp(self):
        self.create_node_group_template(
            'selenium-hdp-master',
            ["NN", "JT", "SNN", "GANGLIA_SERVER", "GANGLIA_MONITOR",
             "NAGIOS_SERVER", "AMBARI_SERVER", "AMBARI_AGENT"], cfg.hdp)
        self.create_node_group_template(
            'selenium-hdp-worker',
            ["TT", "DN", "GANGLIA_MONITOR", "HDFS_CLIENT", "MAPREDUCE_CLIENT",
             "AMBARI_AGENT"], cfg.hdp)
        self.create_cluster_template(
            "selenium-hdp", {'selenium-hdp-master': 1,
                             'selenium-hdp-worker': 2}, cfg.hdp,
            description="hdp plugin", anti_affinity_groups=["NN", "DN", "TT"],
            params=[{"General Parameters:Show_param": True},
                    {"hadoop_heapsize": 512},
                    {"HDFS Parameters:Show_param": True},
                    {"HDFS Parameters:dfs.replication": 2}])
        self.delete_cluster_templates(['selenium-hdp'])
        self.delete_node_group_templates(["selenium-hdp-master",
                                          "selenium-hdp-worker"])

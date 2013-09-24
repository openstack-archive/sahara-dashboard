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


class UINegativeCreateClusterTemplateTest(base.UITestCase):

    @base.attr(tags='cluster_template')
    @testtools.skip
    @testtools.skipIf(cfg.vanilla.skip_plugin_tests,
                      'tests for vanilla plugin skipped')
    def test_create_vanilla_cluster_template_with_wrong_fields(self):
        self.create_node_group_template('selenium-master', ["NN", "JT"],
                                        cfg.vanilla)
        self.create_node_group_template('selenium-worker', ["DN", "TT"],
                                        cfg.vanilla)
        self.create_cluster_template(
            "", {'selenium-master': 1, 'selenium-worker': 2}, cfg.vanilla,
            anti_affinity_groups=["NN", "DN", "TT"],
            params=[{"General Parameters:Enable Swift": False},
                    {"HDFS Parameters:io.file.buffer.size": "str"},
                    {"MapReduce Parameters:mapreduce.job.counters.max":
                        "str"}],
            positive=False, close_window=False, message=
            'Details, HDFS Parameters, MapReduce Parameters, '
            'Template Name:This field is required., '
            'HDFS Parameters:io.file.buffer.size:Enter a whole number., '
            'MapReduce Parameters:mapreduce.job.counters.max:'
            'Enter a whole number.')
        self.delete_node_group_templates(["selenium-master",
                                          "selenium-worker"])

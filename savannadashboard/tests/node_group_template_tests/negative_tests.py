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


class UINegativeCreateNodeGroupTemplate(base.UITestCase):

    @testcase.attr('node_group_template', 'vanilla')
    @unittest2.skipIf(cfg.vanilla.skip_plugin_tests,
                      'tests for vanilla plugin skipped')
    def test_create_vanilla_node_group_template_with_wrong_parameters(self):
        self.create_node_group_template(
            "", ["NN", "JT"], cfg.vanilla, flavor="m1.small",
            params=[{"HDFS Parameters:dfs.datanode.handler.count": "str"},
                    {"MapReduce Parameters:io.sort.mb": "str"}],
            positive=False, close_window=False,
            message='Configure Node Group Template, '
                    'HDFS Parameters, MapReduce Parameters, '
                    'Template Name:This field is required., '
                    'HDFS Parameters:dfs.datanode.handler.count:'
                    'Enter a whole number., '
                    'MapReduce Parameters:io.sort.mb:'
                    'Enter a whole number.')

    @testcase.attr('node_group_template', 'vanilla')
    @unittest2.skipIf(cfg.vanilla.skip_plugin_tests,
                      'tests for vanilla plugin skipped')
    def test_create_vanilla_node_group_template_with_missing_parameters(self):
        self.create_node_group_template(
            "", [], cfg.vanilla, positive=False, close_window=False,
            message='Configure Node Group Template, '
                    'Template Name:This field is required., '
                    'Processes:This field is required.')

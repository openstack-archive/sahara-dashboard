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


class UICreateCluster(base.UITestCase):

    @base.attr('cluster', 'vanilla', speed='slow')
    @testtools.skipIf(cfg.vanilla.skip_plugin_tests,
                      'tests for vanilla plugin skipped')
    def test_create_vanilla_cluster(self):
        try:
            self.create_node_group_template('selenium-master', ["NN", "JT"],
                                            cfg.vanilla,
                                            storage={'type': 'Cinder Volume',
                                                     "volume_per_node": 1,
                                                     'volume_size': 5})
            self.create_node_group_template('selenium-worker', ["DN", "TT"],
                                            cfg.vanilla)
            self.create_node_group_template('selenium-del1', ["NN", "JT",
                                                              "DN", "TT"],
                                            cfg.vanilla)
            self.create_node_group_template('selenium-del2',
                                            ["DN", "TT", "OZ"],
                                            cfg.vanilla)
            self.create_cluster_template("selenium-cl-tmpl",
                                         {'selenium-master': 1,
                                          'selenium-worker': 2}, cfg.vanilla,
                                         anti_affinity_groups=["NN",
                                                               "DN", "TT"])
            self.create_cluster_template("selenium-cl-tmpl2",
                                         {'selenium-master': 1,
                                          'selenium-del2': 2},
                                         cfg.vanilla,
                                         anti_affinity_groups=
                                         ["NN", "DN", "TT", "JT"])
            self.create_cluster('selenium-cl', 'selenium-cl-tmpl', 'vrovachev',
                                cfg.vanilla, await_run=False)
            self.delete_node_group_templates(["selenium-master",
                                              "selenium-worker",
                                              "selenium-del1",
                                              "selenium-del2"],
                                             undelete_names=["selenium-master",
                                                             "selenium-worker",
                                                             "selenium-del2"])
            self.delete_cluster_templates(['selenium-cl-tmpl',
                                           'selenium-cl-tmpl2'],
                                          undelete_names=["selenium-cl-tmpl"])
            self.delete_node_group_templates(["selenium-master",
                                              "selenium-worker",
                                              "selenium-del2"],
                                             undelete_names=[
                                                 "selenium-master",
                                                 "selenium-worker"])
        finally:
            self.delete_clusters(['selenium-cl'])
            self.delete_cluster_templates(['selenium-cl-tmpl'])
            self.delete_node_group_templates(["selenium-master",
                                              "selenium-worker"])

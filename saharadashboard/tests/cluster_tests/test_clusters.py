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

import random
import string

from testtools import testcase
import unittest2

from saharadashboard.tests import base
import saharadashboard.tests.configs.config as cfg


class UICreateCluster(base.UITestCase):

    def setUp(self):
        super(UICreateCluster, self).setUp()
        self.pass_test = False
        self.processes = ["NN", "JT"]
        self.await_run = False
        self.master_storage = {'type': 'Ephemeral Drive'}
        self.anty_affinity = []
        if not cfg.vanilla.skip_edp_test:
            self.swift = self.connect_to_swift()
            self.processes = ["NN", "JT", "OZ"]
            self.await_run = True
        if cfg.common.cinder:
            self.master_storage = {"type": "Cinder Volume",
                                   "volume_per_node": 1,
                                   "volume_size": 5}
        if cfg.common.anty_affinity:
            self.anty_affinity = "NN", "DN", "TT"

    @testcase.attr('cluster', 'vanilla')
    @unittest2.skipIf(cfg.vanilla.skip_plugin_tests,
                      'tests for vanilla plugin skipped')
    def test_create_vanilla_cluster(self):

        self.create_node_group_template('selenium-master', self.processes,
                                        cfg.vanilla,
                                        storage=self.master_storage)
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
                                      'selenium-worker': 1}, cfg.vanilla,
                                     anti_affinity_groups=self.anty_affinity)
        self.create_cluster_template("selenium-cl-tmpl2",
                                     {'selenium-master': 1,
                                      'selenium-del2': 2},
                                     cfg.vanilla,
                                     anti_affinity_groups=["NN", "DN",
                                                           "TT", "JT"])
        self.create_cluster(cfg.vanilla.cluster_name, 'selenium-cl-tmpl',
                            cfg.vanilla, await_run=self.await_run)
        if not cfg.vanilla.skip_edp_test:
            self.edp_helper()
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
        self.delete_clusters([cfg.vanilla.cluster_name], await_delete=True)
        self.delete_cluster_templates(["selenium-cl-tmpl"])
        self.delete_node_group_templates(["selenium-master",
                                          "selenium-worker"])
        self.pass_test = True

    def edp_helper(self):
        self.swift.put_container('selenium-container')
        self.swift.put_object(
            'selenium-container', 'input', ''.join(random.choice(
                ':' + ' ' + '\n' + string.ascii_lowercase)
                for x in range(10000)))

        self.create_data_source(
            'input', 'selenium-container.sahara/input')
        self.create_data_source(
            'output', 'selenium-container.sahara/output')

        parameters_of_storage = {
            'storage_type': 'Internal database',
            'Internal binary': '*Upload a new file',
            'filename': 'edp-lib.jar'}

        self.create_job_binary('edp-lib.jar', parameters_of_storage)

        parameters_of_storage = {
            'storage_type': 'Internal database',
            'Internal binary': '*Create a script',
            'script_name': 'edp-job.pig',
            'script_text': open('saharadashboard/tests/resources/'
                                'edp-job.pig').read()}

        self.create_job_binary('edp-job.pig', parameters_of_storage)

        self.create_job(
            'selenium-job', 'Pig', 'edp-job.pig', ['edp-lib.jar'])
        self.launch_job_on_existing_cluster(
            'selenium-job', 'input', 'output', cfg.vanilla.cluster_name)

        self.delete_swift_container(self.swift, 'selenium-container')
        if getattr(self, "job_id", None):
            self.delete_job_executions([self.job_id], await_delete=True)
        self.delete_jobs(['selenium-job'])
        self.delete_job_binaries(['edp-lib.jar', 'edp-job.pig'])
        self.delete_data_sources(['input', 'output'])

    def cleanup(self):
        if not cfg.vanilla.skip_edp_test:
            self.delete_swift_container(self.swift, 'selenium-container')
            if getattr(self, "job_id", None):
                self.delete_job_executions([self.job_id], finally_delete=True)
            self.delete_jobs(['selenium-job'], finally_delete=True)
            self.delete_job_binaries(['edp-lib.jar', 'edp-job.pig'],
                                     finally_delete=True)
            self.delete_data_sources(['input', 'output'], finally_delete=True)
        self.delete_clusters([cfg.vanilla.cluster_name], finally_delete=True)
        self.delete_cluster_templates(['selenium-cl-tmpl',
                                       'selenium-cl-tmpl2'],
                                      finally_delete=True)
        self.delete_node_group_templates(["selenium-master", "selenium-worker",
                                          "selenium-del1", "selenium-del2"],
                                         finally_delete=True)

    def tearDown(self):
        if not self.pass_test:
            self.cleanup()
        super(UICreateCluster, self).tearDown()

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
import traceback
import unittest2


from saharadashboard.tests import base
import saharadashboard.tests.configs.config as cfg


class UICreateCluster(base.UITestCase):

    @testcase.attr('cluster', 'vanilla')
    @unittest2.skipIf(cfg.vanilla.skip_plugin_tests,
                      'tests for vanilla plugin skipped')
    def test_create_vanilla_cluster(self):

        try:
            processes = ["NN", "JT"]
            await_run = False

            if not cfg.vanilla.skip_edp_test:
                processes = ["NN", "JT", "OZ"]
                await_run = True

            self.create_node_group_template('selenium-master', processes,
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
                                          'selenium-worker': 1}, cfg.vanilla,
                                         anti_affinity_groups=["NN",
                                                               "DN", "TT"])
            self.create_cluster_template("selenium-cl-tmpl2",
                                         {'selenium-master': 1,
                                          'selenium-del2': 2},
                                         cfg.vanilla,
                                         anti_affinity_groups=
                                         ["NN", "DN", "TT", "JT"])
            self.create_cluster('selenium-cl', 'selenium-cl-tmpl',
                                cfg.vanilla, await_run=await_run)
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

        except Exception as e:
            traceback.print_exc()
            raise e
        finally:
            try:
                self.delete_clusters(['selenium-cl'], finally_delete=True)
            except Exception:
                pass

            try:
                self.delete_cluster_templates(['selenium-cl-tmpl',
                                               'selenium-cl-tmpl2'],
                                              finally_delete=True)
            except Exception:
                pass
            try:
                self.delete_node_group_templates(["selenium-master",
                                                  "selenium-worker",
                                                  "selenium-del1",
                                                  "selenium-del2"],
                                                 finally_delete=True)
            except Exception:
                pass

    def edp_helper(self):

        try:

            swift = self.connect_to_swift()
            swift.put_container('selenium-container')
            swift.put_object(
                'selenium-container', 'input', ''.join(random.choice(
                    ':' + ' ' + '\n' + string.ascii_lowercase)
                    for x in range(10000)))

            self.create_data_source(
                'input', 'selenium-container.savanna/input')
            self.create_data_source(
                'output', 'selenium-container.savanna/output')

            parameters_of_storage = {
                'storage_type': 'Savanna internal database',
                'Savanna binary': '*Upload a new file',
                'filename': 'edp-lib.jar'}

            self.create_job_binary('edp-lib.jar', parameters_of_storage)

            parameters_of_storage = {
                'storage_type': 'Savanna internal database',
                'Savanna binary': '*Create a script',
                'script_name': 'edp-job.pig',
                'script_text': open('saharadashboard/tests/resources/'
                                    'edp-job.pig').read()}

            self.create_job_binary('edp-job.pig', parameters_of_storage)

            self.create_job(
                'selenium-job', 'Pig', 'edp-job.pig', ['edp-lib.jar'])
            self.launch_job_on_existing_cluster(
                'selenium-job', 'input', 'output', 'selenium-cl')

        except Exception as e:
            raise e

        finally:
            try:
                self.delete_swift_container(swift, 'selenium-container')
            except Exception:
                pass
            try:
                self.delete_all_job_executions()
            except Exception:
                pass
            try:
                self.delete_jobs(['selenium-job'], finally_delete=True)
            except Exception:
                pass
            try:
                self.delete_job_binaries(['edp-lib.jar', 'edp-job.pig'],
                                         finally_delete=True)
            except Exception:
                pass
            try:
                self.delete_data_sources(['input', 'output'],
                                         finally_delete=True)
            except Exception:
                pass

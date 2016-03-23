#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import datetime

from sahara_dashboard.test.integration_tests.helpers import SaharaTestCase

SUFFIX = datetime.datetime.now().strftime('%H-%M-%S-%f')[:12]


def gen_name(name):
    return '{}-{}'.format(name, SUFFIX)

PLUGIN_NAME = 'Fake Plugin'
PLUGIN_VERSION = '0.1'

FLAVOR_NAME = gen_name('flavor')
IMAGE_NAME = gen_name("image")
IMAGE_TAGS = ('fake', PLUGIN_VERSION)

MASTER_NAME = gen_name("master")
WORKER_NAME = gen_name("worker")
TEMPLATE_NAME = gen_name("template")
CLUSTER_NAME = gen_name("cluster")


class TestCRUD(SaharaTestCase):

    def setUp(self):
        super(TestCRUD, self).setUp()
        flavors_page = self.home_pg.go_to_system_flavorspage()

        flavors_page.create_flavor(
            name=FLAVOR_NAME,
            vcpus=self.CONFIG.sahara.flavor_vcpus,
            ram=self.CONFIG.sahara.flavor_ram,
            root_disk=self.CONFIG.sahara.flavor_root_disk,
            ephemeral_disk=self.CONFIG.sahara.flavor_ephemeral_disk,
            swap_disk=self.CONFIG.sahara.flavor_swap_disk)

        self.assertTrue(flavors_page.is_flavor_present(FLAVOR_NAME))
        image_pg = self.home_pg.go_to_compute_imagespage()
        image_pg.create_image(IMAGE_NAME,
                              location=self.CONFIG.sahara.fake_http_image)
        image_pg.wait_until_image_active(IMAGE_NAME)
        image_reg_pg = (
            self.home_pg.go_to_dataprocessing_clusters_imageregistrypage())
        image_ssh_user = self.CONFIG.sahara.fake_image_ssh_user
        image_reg_pg.register_image(IMAGE_NAME, image_ssh_user,
                                    "Test description", tags=IMAGE_TAGS)
        image_reg_pg.wait_until_image_registered(IMAGE_NAME)

    def create_cluster(self):
        nodegrouptpls_pg = (
            self.home_pg.go_to_dataprocessing_clusters_nodegrouptemplatespage()
        )

        nodegrouptpls_pg.create(
            PLUGIN_NAME, PLUGIN_VERSION, name=WORKER_NAME, flavor=FLAVOR_NAME,
            processes=['MapReduce:tasktracker', 'HDFS:datanode'])
        self.assertTrue(nodegrouptpls_pg.has_success_message())
        self.assertFalse(nodegrouptpls_pg.has_error_message())
        self.assertTrue(nodegrouptpls_pg.is_present(WORKER_NAME),
                        "Worker template was not created.")
        nodegrouptpls_pg.create(
            PLUGIN_NAME, PLUGIN_VERSION, name=MASTER_NAME, flavor=FLAVOR_NAME,
            proxygateway=True, floating_ip_pool=self.CONFIG.sahara.ip_pool,
            processes=['MapReduce:jobtracker', 'HDFS:namenode'])
        self.assertTrue(nodegrouptpls_pg.has_success_message())
        self.assertFalse(nodegrouptpls_pg.has_error_message())
        self.assertTrue(nodegrouptpls_pg.is_present(MASTER_NAME),
                        "Worker template was not created.")

        clustertpls_pg = (
            self.home_pg.go_to_dataprocessing_clusters_clustertemplatespage())

        clustertpls_pg.create(
            PLUGIN_NAME, PLUGIN_VERSION, name=TEMPLATE_NAME,
            node_group_templates=[MASTER_NAME, WORKER_NAME])
        self.assertTrue(clustertpls_pg.has_success_message())
        self.assertFalse(clustertpls_pg.has_error_message())
        self.assertTrue(clustertpls_pg.is_present(TEMPLATE_NAME),
                        "Cluster template was not created.")

        cluster_pg = self.home_pg.go_to_dataprocessing_clusters_clusterspage()
        cluster_pg.create(PLUGIN_NAME, PLUGIN_VERSION, name=CLUSTER_NAME,
                          image=IMAGE_NAME,
                          cluster_template=TEMPLATE_NAME)
        self.assertTrue(cluster_pg.has_success_message())
        self.assertFalse(cluster_pg.has_error_message())
        cluster_pg.refresh_page()
        self.assertTrue(cluster_pg.is_present(CLUSTER_NAME),
                        "Cluster was not created.")

        cluster_pg.wait_until_cluster_active(
            CLUSTER_NAME, timeout=self.CONFIG.sahara.launch_timeout)
        self.assertTrue(cluster_pg.is_cluster_active(CLUSTER_NAME),
                        "Cluster is not active")

    def cluster_scale(self):
        cluster_pg = self.home_pg.go_to_dataprocessing_clusters_clusterspage()
        cluster_pg.scale(CLUSTER_NAME, WORKER_NAME, 2)
        self.assertTrue(cluster_pg.has_success_message())
        self.assertFalse(cluster_pg.has_error_message())

        cluster_pg.wait_until_cluster_active(
            CLUSTER_NAME, timeout=self.CONFIG.sahara.launch_timeout)
        self.assertTrue(cluster_pg.is_cluster_active(CLUSTER_NAME),
                        "Cluster is not active")
        self.assertEqual(cluster_pg.get_cluster_instances_count(CLUSTER_NAME),
                         3, "Cluster was not scaled")

    def delete_cluster(self):
        cluster_pg = self.home_pg.go_to_dataprocessing_clusters_clusterspage()
        cluster_pg.delete(CLUSTER_NAME)
        self.assertTrue(cluster_pg.has_success_message())
        self.assertFalse(cluster_pg.has_error_message())
        cluster_pg.wait_until_cluster_deleted(CLUSTER_NAME)
        self.assertFalse(cluster_pg.is_present(CLUSTER_NAME),
                         "Cluster was not deleted.")

    def test_cluster_create_scale_delete(self):
        self.create_cluster()
        self.cluster_scale()
        self.delete_cluster()

    def tearDown(self):
        clustertpls_pg = (
            self.home_pg.go_to_dataprocessing_clusters_clustertemplatespage())
        if clustertpls_pg.is_present(TEMPLATE_NAME):
            clustertpls_pg.delete(TEMPLATE_NAME)

        nodegrouptpls_pg = (
            self.home_pg.go_to_dataprocessing_clusters_nodegrouptemplatespage()
        )
        nodegrouptpls_pg.delete_many((WORKER_NAME, MASTER_NAME))

        image_reg_pg = (
            self.home_pg.go_to_dataprocessing_clusters_imageregistrypage())
        image_reg_pg.unregister_image(IMAGE_NAME)

        image_pg = self.home_pg.go_to_compute_imagespage()
        image_pg.delete_image(IMAGE_NAME)

        flavors_page = self.home_pg.go_to_system_flavorspage()
        flavors_page.delete_flavor(FLAVOR_NAME)
        self.assertFalse(flavors_page.is_flavor_present(FLAVOR_NAME))
        super(TestCRUD, self).tearDown()

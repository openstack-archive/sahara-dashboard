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

from savannadashboard.tests import base
import savannadashboard.tests.configs.config as cfg


class UIImageRegistry(base.UITestCase):

    @base.attr(tags='image_registry')
    def test_edit_tags_for_image(self):
        self.edit_tags_by_image_name(cfg.common.image_name_for_edit,
                                     tags_to_add=[
                                         {cfg.hdp.plugin_overview_name:
                                          cfg.hdp.hadoop_version},
                                         {'custom_tag': 'blabla'}])
        self.edit_tags_by_image_name(cfg.common.image_name_for_edit,
                                     tags_to_add=[{'custom_tag': 'qweqwe'}],
                                     tags_to_remove=['qweqwe', 'blabla'])

    @base.attr(tags='image_registry')
    def test_registry_vanilla_image(self):
        self.image_registry(cfg.common.image_name_for_register,
                            user_name='cloud_user',
                            tags_to_add=[{cfg.vanilla.plugin_overview_name:
                                          cfg.vanilla.hadoop_version},
                                         {'custom_tag': 'blabla'}])
        self.unregister_images([cfg.common.image_name_for_register])

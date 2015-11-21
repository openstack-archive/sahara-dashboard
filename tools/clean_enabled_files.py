#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

# This file is temporarily needed to allow the conversion from integrated
# Sahara content in Horizon to plugin based content. Horizon currently defines
# the same module name data_processing and imports it by default. This utility
# removes the configuration files that are responsible for importing the old
# version of the module. Only Sahara content configuration files are effected
# in Horizon.

import os

from openstack_dashboard import enabled as local_enabled

from sahara_dashboard import enabled

ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
WITH_VENV = os.path.join(ROOT, 'tools', 'with_venv.sh')

def main():
    src_path = os.path.dirname(enabled.__file__)
    dest_path = os.path.dirname(local_enabled.__file__)

    src_files = os.listdir(src_path)
    for file in src_files:
        # skip the __init__.py or bad things happen
        if file  == "__init__.py":
            continue

        file_path = os.path.join(dest_path, file)
        if os.path.isfile(file_path):
            print ("removing ", file_path)
            os.remove(file_path)

if __name__ == '__main__':
    main()

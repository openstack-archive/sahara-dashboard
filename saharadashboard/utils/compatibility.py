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

"""Provide compatibility with various OpenStack releases.

All the code which depends on OpenStack release version should be placed there.
Folsom is the oldest recognizable release.
"""


def get_dashboard_release():
    """Return release codename of currently running Dashboard."""
    import horizon.version

    if hasattr(horizon.version, 'HORIZON_VERSION'):
        return 'folsom'

    if hasattr(horizon.version, "version_info"):
        if "2013.2" in horizon.version.version_info.version_string():
            return "havana"

    return 'icehouse'


def _is_folsom():
    return get_dashboard_release() == 'folsom'


def _is_havana():
    return get_dashboard_release() == 'havana'


def convert_url(link):
    """Expect grizzly url and convert it to folsom if needed

    For example, 'horizon:project:instances:detail' should be converted to
    'horizon:nova:instances:detail'
    """
    if _is_folsom():
        return link.replace('project', 'nova', 1)

    if _is_havana():
        return link.replace(':images:', ':images_and_snapshots:', 1)

    return link

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

from designateclient.v2 import client as designate
from keystoneauth1.identity import generic
from keystoneauth1 import session as keystone_session
from openstack_dashboard.api import base


def client(request):
    auth_url = base.url_for(request, 'identity')
    token_kwargs = dict(
        auth_url=auth_url,
        token=request.user.token.id,
        tenant_id=request.user.project_id,
        tenant_name=request.user.project_name,
    )
    auth = generic.Token(**token_kwargs)
    session = keystone_session.Session(auth=auth)
    return designate.Client(session=session)


def get_domain_names(request):
    return client(request).zones.list()

# Copyright (c) 2016 Mirantis Inc.
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

import base64
import copy
from urllib import parse


def serialize(obj):
    """Serialize the given object
    :param obj: string representation of the object
    :return: encoded object (its type is unicode string)
    """
    result = base64.urlsafe_b64encode(obj)
    # this workaround is needed because in case of python 3 the
    # urlsafe_b64encode method returns string of 'bytes' class.
    result = result.decode()
    return result


def deserialize(obj):
    """Deserialize the given object
    :param obj: string representation of the encoded object
    :return: decoded object (its type is unicode string)
    """
    result = base64.urlsafe_b64decode(obj)
    # this workaround is needed because in case of python 3 the
    # urlsafe_b64decode method returns string of 'bytes' class
    result = result.decode()
    return result


def delete_pagination_params_from_request(request, save_limit=None):
    """Delete marker and limit parameters from GET requests
    :param request: instance of GET request
    :param save_limit: if True, 'limit' will not be deleted
    :return: instance of GET request without marker or limit
    """
    request = copy.copy(request)
    request.GET = request.GET.copy()

    params = ['marker']
    if not save_limit:
        params.append('limit')

    for param in ['marker', 'limit']:
        if param in request.GET:
            del(request.GET[param])
            query_string = request.META.get('QUERY_STRING', '')
            query_dict = parse.parse_qs(query_string)
            if param in query_dict:
                del(query_dict[param])

            query_string = parse.urlencode(query_dict, doseq=True)
            request.META['QUERY_STRING'] = query_string
    return request


def smart_sort_helper(version):
    """Allows intelligent sorting of plugin versions, for example when
    minor version of a plugin is 11, sort numerically so that 11 > 10,
    instead of alphabetically so that 2 > 11
    """
    def _safe_cast_to_int(obj):
        try:
            return int(obj)
        except ValueError:
            return obj
    return [_safe_cast_to_int(part) for part in version.split('.')]

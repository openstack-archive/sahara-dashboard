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
import six


def serialize(obj):
    """Serialize the given object
    :param obj: string representation of the object
    :return: encoded object (its type is unicode string)
    """
    result = base64.urlsafe_b64encode(obj)
    # this workaround is needed because in case of python 3 the
    # urlsafe_b64encode method returns string of 'bytes' class.
    if six.PY3:
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
    if six.PY3:
        result = result.decode()
    return result

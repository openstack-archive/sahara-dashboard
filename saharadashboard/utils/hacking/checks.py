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

import tokenize


def hacking_no_assert_equals(logical_line, tokens):
    r"""assertEquals() is deprecated, use assertEqual instead.

    Copied from https://review.openstack.org/#/c/35962/

    Okay: self.assertEqual(0, 0)
    S362: self.assertEquals(0, 0)
    """

    for token_type, text, start_index, _, _ in tokens:

        if token_type == tokenize.NAME and text == "assertEquals":
            yield (
                start_index[1],
                "S362: assertEquals is deprecated, use assertEqual")


def hacking_no_author_attr(logical_line, tokens):
    """__author__ should not be used.

    S363: __author__ = slukjanov
    """
    for token_type, text, start_index, _, _ in tokens:
        if token_type == tokenize.NAME and text == "__author__":
            yield (start_index[1],
                   "S363: __author__ should not be used")


def factory(register):
    register(hacking_no_assert_equals)
    register(hacking_no_author_attr)

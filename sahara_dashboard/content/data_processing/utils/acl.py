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

import abc
import functools

from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import exceptions
from horizon import forms
from horizon import tables


MESSAGE_MAPPING_PRESENT = {
    'public': functools.partial(
        ungettext_lazy,
        u"Make public",
        u"Make public"),
    'private': functools.partial(
        ungettext_lazy,
        u"Make private",
        u"Make private"),
    'protected': functools.partial(
        ungettext_lazy,
        u"Make protected",
        u"Make protected"),
    'unprotected': functools.partial(
        ungettext_lazy,
        u"Make unprotected",
        u"Make unprotected"),
}

MESSAGE_MAPPING_PAST = {
    'public': functools.partial(
        ungettext_lazy,
        u"Made public",
        u"Made public"),
    'private': functools.partial(
        ungettext_lazy,
        u"Made private",
        u"Made private"),
    'protected': functools.partial(
        ungettext_lazy,
        u"Made protected",
        u"Made protected"),
    'unprotected': functools.partial(
        ungettext_lazy,
        u"Made unprotected",
        u"Made unprotected"),
}


class RuleChangeAction(tables.BatchAction):
    rule = "no-rule"

    def action_present(self, count):
        return MESSAGE_MAPPING_PRESENT[self.rule](count)

    def action_past(self, count):
        return MESSAGE_MAPPING_PAST[self.rule](count)

    def action(self, request, datum_id):
        try:
            update_kwargs = {}
            if self.rule in ['public', 'private']:
                update_kwargs['is_public'] = self.rule == "public"
            if self.rule in ["protected", "unprotected"]:
                update_kwargs['is_protected'] = self.rule == "protected"
            self.change_rule_method(request, datum_id, **update_kwargs)
        except Exception as e:
            exceptions.handle(request, e)
            raise


class MakePublic(RuleChangeAction):
    name = "make_public"
    rule = "public"

    @abc.abstractmethod
    def change_rule_method(self, request, datum_id, **update_kwargs):
        pass


class MakePrivate(RuleChangeAction):
    name = "make_private"
    rule = "private"

    @abc.abstractmethod
    def change_rule_method(self, request, datum_id, **update_kwargs):
        pass


class MakeProtected(RuleChangeAction):
    name = "make_protected"
    rule = "protected"

    @abc.abstractmethod
    def change_rule_method(self, request, datum_id, **update_kwargs):
        pass


class MakeUnProtected(RuleChangeAction):
    name = "make_unprotected"
    rule = "unprotected"

    @abc.abstractmethod
    def change_rule_method(self, request, datum_id, **update_kwargs):
        pass


def get_is_public_form(object_type):
    return forms.BooleanField(
        label=_("Public"),
        help_text=_("If selected, %s will be shared across the "
                    "tenants") % object_type,
        required=False,
        widget=forms.CheckboxInput(),
        initial=False,
    )


def get_is_protected_form(object_type):
    return forms.BooleanField(
        label=_("Protected"),
        help_text=_("If selected, %s will be protected from modifications "
                    "until this will be unselected") % object_type,
        required=False,
        widget=forms.CheckboxInput(),
        initial=False)

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

from urllib import parse

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions

from sahara_dashboard.api import sahara as saharaclient
from sahara_dashboard.content.data_processing.jobs \
    .data_sources.workflows import create


class EditDataSource(create.CreateDataSource):
    slug = "edit_data_source"
    name = _("Edit Data Source")
    finalize_button_name = _("Update")
    success_message = _("Data source updated")
    failure_message = _("Could not update data source")
    success_url = "horizon:project:data_processing.jobs:index"
    default_steps = (create.GeneralConfig,)

    FIELD_MAP = {
        "data_source_name": "name",
        "data_source_type": "type",
        "data_source_description": "description",
        "data_source_url": "url",
        "data_source_credential_user": None,
        "data_source_credential_pass": None,
        "data_source_credential_accesskey": None,
        "data_source_credential_secretkey": None,
        "data_source_credential_endpoint": None,
        "data_source_credential_s3_ssl": None,
        "data_source_credential_s3_bucket_in_path": None,
        "data_source_manila_share": None,
        'is_public': "is_public",
        'is_protected': "is_protected"
    }

    def __init__(self, request, context_seed, entry_point, *args, **kwargs):
        self.data_source_id = context_seed["data_source_id"]
        data_source = saharaclient.data_source_get(request,
                                                   self.data_source_id)
        super(EditDataSource, self).__init__(request, context_seed,
                                             entry_point, *args, **kwargs)

        for step in self.steps:
            if isinstance(step, create.GeneralConfig):
                fields = step.action.fields
                for field in fields:
                    if self.FIELD_MAP[field]:
                        if (field == "data_source_url" and
                                data_source.type == "manila"):
                            fields[field].initial = parse.urlparse(
                                data_source.url).path
                        elif (field == "data_source_manila_share"
                              and data_source.type == "manila"):
                            fields[field].initial = parse.urlparse(
                                data_source.url).netloc
                        else:
                            fields[field].initial = (
                                getattr(data_source,
                                        self.FIELD_MAP[field],
                                        None))

    def handle(self, request, context):
        try:
            credentials = {}
            if context["general_data_source_type"] == "swift":
                credentials["user"] = context.get(
                    "general_data_source_credential_user", None)
                credentials["password"] = context.get(
                    "general_data_source_credential_pass", None)
            elif context["general_data_source_type"] == "s3":
                if context.get("general_data_source_credential_accesskey",
                               None):
                    credentials["accesskey"] = context[
                        "general_data_source_credential_accesskey"]
                if context.get("general_data_source_credential_secretkey",
                               None):
                    credentials["secretkey"] = context[
                        "general_data_source_credential_secretkey"]
                if context.get("general_data_source_credential_endpoint", None
                               ):
                    credentials["endpoint"] = context[
                        "general_data_source_credential_endpoint"]
                credentials["bucket_in_path"] = context[
                    "general_data_source_credential_s3_bucket_in_path"]
                credentials["ssl"] = context[
                    "general_data_source_credential_s3_ssl"]
            credentials = credentials or None
            update_data = {
                "name": context["general_data_source_name"],
                "description": context["general_data_source_description"],
                "type": context["general_data_source_type"],
                "url": context["source_url"],
                "credentials": credentials,
                "is_public": context['general_is_public'],
                "is_protected": context['general_is_protected']
            }
            return saharaclient.data_source_update(request,
                                                   self.data_source_id,
                                                   update_data)
        except Exception:
            exceptions.handle(request)
            return False

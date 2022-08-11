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


from django.urls import re_path

import sahara_dashboard.content.data_processing.clusters.views as views
import sahara_dashboard.content.data_processing.clusters.image_registry. \
    views as image_views
import sahara_dashboard.content.data_processing.clusters.nodegroup_templates. \
    views as ngt_views
import sahara_dashboard.content.data_processing.clusters.cluster_templates. \
    views as ct_views
import sahara_dashboard.content.data_processing.clusters.clusters. \
    views as cluster_views
import sahara_dashboard.content.data_processing.clusters.wizard. \
    views as cluster_guide_views


urlpatterns = [re_path(r'^$', views.IndexView.as_view(), name='index'),
               re_path(r'^\?tab=cluster_tabs__image_registry_tab$',
                       views.IndexView.as_view(), name='image-registry-tab'),
               re_path(r'^\?tab=cluster_tabs__node_group_templates_tab$',
                       views.IndexView.as_view(),
                       name='nodegroup-templates-tab'),
               re_path(r'^\?tab=cluster_tabs__clusters_templates_tab$',
                       views.IndexView.as_view(),
                       name='cluster-templates-tab'),
               re_path(r'^\?tab=cluster_tabs__clusters_tab$',
                       views.IndexView.as_view(), name='clusters-tab'),
               re_path(r'^create-cluster-template$',
                       ct_views.CreateClusterTemplateView.as_view(),
                       name='create-cluster-template'),
               re_path(r'^create-nodegroup-template$',
                       ngt_views.CreateNodegroupTemplateView.as_view(),
                       name='create-nodegroup-template'),
               re_path(r'^configure-cluster-template$',
                       ct_views.ConfigureClusterTemplateView.as_view(),
                       name='configure-cluster-template'),
               re_path(r'^import-cluster-template-file$',
                       ct_views.ImportClusterTemplateFileView.as_view(),
                       name='import-cluster-template-file'),
               re_path(r'^import-cluster-template-name$',
                       ct_views.ImportClusterTemplateNameView.as_view(),
                       name='import-cluster-template-name'),
               re_path(r'^import-cluster-template-nodegroups$',
                       ct_views.ImportClusterTemplateNodegroupsView.as_view(),
                       name='import-cluster-template-nodegroups'),
               re_path(r'^configure-nodegroup-template$',
                       ngt_views.ConfigureNodegroupTemplateView.as_view(),
                       name='configure-nodegroup-template'),
               re_path(r'^import-nodegroup-template-file$',
                       ngt_views.ImportNodegroupTemplateFileView.as_view(),
                       name='import-nodegroup-template-file'),
               re_path(r'^import-nodegroup-template-details$',
                       ngt_views.ImportNodegroupTemplateDetailsView.as_view(),
                       name='import-nodegroup-template-details'),
               re_path(r'^cluster-template/(?P<template_id>[^/]+)$',
                       ct_views.ClusterTemplateDetailsView.as_view(),
                       name='ct-details'),
               re_path(r'^node-group-template/(?P<template_id>[^/]+)$',
                       ngt_views.NodegroupTemplateDetailsView.as_view(),
                       name='details'),
               re_path(r'^cluster-template/(?P<template_id>[^/]+)/copy$',
                       ct_views.CopyClusterTemplateView.as_view(),
                       name='ct-copy'),
               re_path(r'^cluster-template/(?P<template_id>[^/]+)/edit$',
                       ct_views.EditClusterTemplateView.as_view(),
                       name='ct-edit'),
               re_path(r'^node-group-template/(?P<template_id>[^/]+)/copy$',
                       ngt_views.CopyNodegroupTemplateView.as_view(),
                       name='copy'),
               re_path(r'^node-group-template/(?P<template_id>[^/]+)/edit$',
                       ngt_views.EditNodegroupTemplateView.as_view(),
                       name='edit'),
               re_path(r'^create-cluster$',
                       cluster_views.CreateClusterView.as_view(),
                       name='create-cluster'),
               re_path(r'^configure-cluster$',
                       cluster_views.ConfigureClusterView.as_view(),
                       name='configure-cluster'),
               re_path(r'^cluster/(?P<cluster_id>[^/]+)$',
                       cluster_views.ClusterDetailsView.as_view(),
                       name='cluster-details'),
               re_path(r'^cluster/(?P<cluster_id>[^/]+)/events$',
                       cluster_views.ClusterEventsView.as_view(),
                       name='events'),
               re_path(r'^cluster/(?P<cluster_id>[^/]+)/scale$',
                       cluster_views.ScaleClusterView.as_view(),
                       name='scale'),
               re_path(r'^cluster/(?P<cluster_id>[^/]+)/verifications$',
                       cluster_views.ClusterHealthChecksView.as_view(),
                       name='verifications'),
               re_path(r'^cluster/(?P<cluster_id>[^/]+)/update_shares$',
                       cluster_views.UpdateClusterSharesView.as_view(),
                       name='update-shares'),
               re_path(r'^edit_tags/(?P<image_id>[^/]+)/$',
                       image_views.EditTagsView.as_view(), name='edit_tags'),
               re_path(r'^register/$',
                       image_views.RegisterImageView.as_view(),
                       name='register'),
               re_path(r'^cluster_guide$',
                       cluster_guide_views.ClusterGuideView.as_view(),
                       name='cluster_guide'),
               re_path(r'^cluster_guide/(?P<reset_cluster_guide>[^/]+)/$',
                       cluster_guide_views.ResetClusterGuideView.as_view(),
                       name='reset_cluster_guide'),
               re_path(r'^image_register/$',
                       cluster_guide_views.ImageRegisterView.as_view(),
                       name='image_register'),
               re_path(r'^plugin_select$',
                       cluster_guide_views.PluginSelectView.as_view(),
                       name='plugin_select'),
               re_path(r'^ngt_select$',
                       cluster_guide_views.NodeGroupSelectView.as_view(),
                       name='ngt_select'), ]

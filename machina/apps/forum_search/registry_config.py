# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SearchRegistryConfig(AppConfig):
    label = 'forum_search'
    name = 'machina.apps.forum_search'
    verbose_name = _('Machina: Forum searches')
#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from abc import ABCMeta

from hvac.api.vault_api_base import VaultApiBase

logger = logging.getLogger(__name__)


class SystemBackendMixin(VaultApiBase):
    """Base class for System Backend API endpoints."""

    __metaclass__ = ABCMeta

"""Base class used by all hvac "api" classes."""
import logging
from abc import ABCMeta

logger = logging.getLogger(__name__)


class VaultApiBase(object):
    """Base class for API endpoints."""

    __metaclass__ = ABCMeta

    def __init__(self, adapter):
        """Default api class constructor.

        :param adapter: Instance of :py:class:`hvac.adapters.Adapter`; used for performing HTTP requests.
        :type adapter: hvac.adapters.Adapter
        """
        self._adapter = adapter

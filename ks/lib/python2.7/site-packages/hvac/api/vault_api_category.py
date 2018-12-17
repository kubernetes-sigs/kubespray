"""Base class used by all hvac api "category" classes."""
import logging
from abc import ABCMeta, abstractproperty

from hvac.api.vault_api_base import VaultApiBase

logger = logging.getLogger(__name__)


class VaultApiCategory(VaultApiBase):
    """Base class for API categories."""
    __metaclass__ = ABCMeta

    def __init__(self, adapter):
        """API Category class constructor.

        :param adapter: Instance of :py:class:`hvac.adapters.Adapter`; used for performing HTTP requests.
        :type adapter: hvac.adapters.Adapter
        """
        self._adapter = adapter
        self.implemented_class_names = []
        for implemented_class in self.implemented_classes:
            class_name = implemented_class.__name__.lower()
            self.implemented_class_names.append(class_name)
            auth_method_instance = implemented_class(adapter=adapter)
            setattr(self, self.get_private_attr_name(class_name), auth_method_instance)

        super(VaultApiCategory, self).__init__(adapter=adapter)

    def __getattr__(self, item):
        """Get an instance of an class instance in this category where available.

        :param item: Name of the class being requested.
        :type item: str | unicode
        :return: The requested class instance where available.
        :rtype: hvac.api.VaultApiBase
        """
        if item in self.implemented_class_names:
            private_attr_name = self.get_private_attr_name(item)
            return getattr(self, private_attr_name)
        if item in [u.lower() for u in self.unimplemented_classes]:
            raise NotImplementedError('"%s" auth method class not currently implemented.')
        raise AttributeError

    @property
    def adapter(self):
        """Retrieve the adapter instance under the "_adapter" property in use by this class.

        :return: The adapter instance in use by this class.
        :rtype: hvac.adapters.Adapter
        """
        return self._adapter

    @adapter.setter
    def adapter(self, adapter):
        """Sets the adapter instance under the "_adapter" property in use by this class.

        Also sets the adapter property for all implemented classes under this category.

        :param adapter: New adapter instance to set for this class and all implemented classes under this category.
        :type adapter: hvac.adapters.Adapter
        """
        self._adapter = adapter
        for implemented_class in self.implemented_classes:
            class_name = implemented_class.__name__.lower()
            getattr(self, self.get_private_attr_name(class_name)).adapter = adapter

    @abstractproperty
    def implemented_classes(self):
        """List of implemented classes under this category.

        :return: List of implemented classes under this category.
        :rtype: List[hvac.api.VaultApiBase]
        """
        raise NotImplementedError

    @property
    def unimplemented_classes(self):
        """List of known unimplemented classes under this category.

        :return: List of known unimplemented classes under this category.
        :rtype: List[str]
        """
        raise NotImplementedError

    @staticmethod
    def get_private_attr_name(class_name):
        """Helper method to prepend a leading underscore to a provided class name.

        :param class_name: Name of a class under this category.
        :type class_name: str|unicode
        :return: The private attribute label for the provided class.
        :rtype: str
        """
        private_attr_name = '_{class_name}'.format(class_name=class_name)
        return private_attr_name

"""Package Manager Installation Broker for goal.

Provides intelligent package manager detection, selection, and installation.
"""

from goal.installers.broker import PackageManagerBroker
from goal.installers.managers.base import InstallResult, AbstractPackageManager

__all__ = ['PackageManagerBroker', 'InstallResult', 'AbstractPackageManager']

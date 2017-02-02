#!/usr/bin/env python
"""This is the GRR client installer module.

GRR allows several installers to be registered as plugins. The
installers are executed when the client is deployed to a target system
in their specified order (according to the registry plugin system).

Installers are usually used to upgrade existing clients and setup
clients in unusual situations.
"""
import logging
import os
import sys

from grr.lib import config_lib
from grr.lib import flags
from grr.lib import registry


class Installer(registry.HookRegistry):
  """A GRR installer plugin.

  Modules can register special actions which only run on installation
  by extending this base class. Execution order is controlled using
  the same mechanism provided by HookRegistry - i.e. by declaring
  "pre" and "order" attributes.
  """

  __metaclass__ = registry.MetaclassRegistry


def RunInstaller():
  """Run all registered installers.

  Run all the current installers and then exit the process.
  """

  try:
    os.makedirs(os.path.dirname(config_lib.CONFIG["Installer.logfile"]))
  except OSError:
    pass

  # Always log to the installer logfile at debug level. This way if our
  # installer fails we can send detailed diagnostics.
  handler = logging.FileHandler(
      config_lib.CONFIG["Installer.logfile"], mode="wb")

  handler.setLevel(logging.DEBUG)

  # Add this to the root logger.
  logging.getLogger().addHandler(handler)

  # Ordinarily when the client starts up, the local volatile
  # configuration is read. Howevwer, when running the installer, we
  # need to ensure that only the installer configuration is used so
  # nothing gets overridden by local settings. We there must reload
  # the configuration from the flag and ignore the Config.writeback
  # location.
  config_lib.CONFIG.Initialize(filename=flags.FLAGS.config, reset=True)
  config_lib.CONFIG.AddContext(
      "Installer Context", "Context applied when we run the client installer.")

  logging.warn("Starting installation procedure for GRR client.")
  try:
    Installer().Init()
  except Exception as e:  # pylint: disable=broad-except
    # Ouch! we failed to install... Not a lot we can do
    # here - just log the error and give up.
    logging.exception("Installation failed: %s", e)

    # Error return status.
    sys.exit(-1)

  # Exit successfully.
  sys.exit(0)

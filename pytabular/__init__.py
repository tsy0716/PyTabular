"""Welcome to PyTabular.

__init__.py will start to setup the basics.
It will setup logging and make sure Pythonnet is good to go.
Then it will begin to import specifics of the module.
"""

# flake8: noqa
import logging
import os
import sys
import platform
from rich.logging import RichHandler
from rich.theme import Theme
from rich.console import Console
from rich import pretty

pretty.install()
console = Console(theme=Theme({"logging.level.warning": "bold reverse red"}))
logging.basicConfig(
    level=logging.DEBUG,
    format="%(message)s",
    datefmt="[%H:%M:%S]",
    handlers=[RichHandler(console=console)],
)
logger = logging.getLogger("PyTabular")
logger.setLevel(logging.INFO)
logger.info("Logging configured...")
logger.info("To update logging:")
logger.info(">>> import logging")
logger.info(">>> pytabular.logger.setLevel(level=logging.INFO)")
logger.info("See https://docs.python.org/3/library/logging.html#logging-levels")


logger.info(f"Python Version::{sys.version}")
logger.info(f"Python Location::{sys.exec_prefix}")
logger.info(f"Package Location:: {__file__}")
logger.info(f"Working Directory:: {os.getcwd()}")
logger.info(f"Platform:: {sys.platform}-{platform.release()}")

dll = os.path.join(os.path.dirname(__file__), "dll")
sys.path.append(dll)
sys.path.append(os.path.dirname(__file__))

logger.info("Configuring pythonnet for cross-platform .NET...")

# Try to configure pythonnet for coreclr before any CLR operations
clr_imported = False
try:
    import pythonnet
    from pythonnet import set_runtime
    
    # Try to configure runtime first
    try:
        set_runtime("coreclr")
        logger.info("✅ pythonnet configured for coreclr (.NET 8.0)")
    except Exception as runtime_error:
        if "already been loaded" in str(runtime_error):
            logger.info("✅ .NET runtime already configured in this process")
        else:
            logger.warning(f"⚠️  Runtime configuration failed: {runtime_error}")
    
    # Now import CLR
    import clr
    clr_imported = True
    logger.info("✅ CLR imported successfully")
    
except Exception as e:
    logger.error(f"❌ Failed to import pythonnet/CLR: {e}")
    raise

logger.info("Beginning CLR references...")

logger.info("Adding DLL references for cross-platform .NET 8.0...")

# Load DLLs in dependency order
dll_dir = os.path.join(os.path.dirname(__file__), "dll")

logger.info("Adding Reference Microsoft.AnalysisServices.Runtime.Core")
clr.AddReference(os.path.join(dll_dir, "Microsoft.AnalysisServices.Runtime.Core.dll"))

logger.info("Adding Reference Microsoft.AnalysisServices.Core")
clr.AddReference(os.path.join(dll_dir, "Microsoft.AnalysisServices.Core.dll"))

logger.info("Adding Reference Microsoft.AnalysisServices")
clr.AddReference(os.path.join(dll_dir, "Microsoft.AnalysisServices.dll"))

logger.info("Adding Reference Microsoft.AnalysisServices.Tabular")
clr.AddReference(os.path.join(dll_dir, "Microsoft.AnalysisServices.Tabular.dll"))

logger.info("Adding Reference Microsoft.AnalysisServices.AdomdClient")
clr.AddReference(os.path.join(dll_dir, "Microsoft.AnalysisServices.AdomdClient.dll"))

logger.info("✅ All cross-platform DLLs loaded successfully")

logger.info("Importing specifics in module...")
from .pytabular import Tabular

from .logic_utils import (
    pd_dataframe_to_m_expression,
    pandas_datatype_to_tabular_datatype,
)
from .tabular_tracing import BaseTrace, RefreshTrace, QueryMonitor
from .tabular_editor import TabularEditor
from .best_practice_analyzer import BPA
from .query import Connection
from .pbi_helper import find_local_pbi_instances
from .document import ModelDocumenter
from .tmdl import Tmdl


logger.info("Import successful...")

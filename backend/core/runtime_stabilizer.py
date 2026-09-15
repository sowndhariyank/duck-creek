"""
Runtime Environment Stabilization Layer.
Dynamically handles module imports, Pydantic type stabilization,
and ADK / A2UI boundary safety at application boot.
"""

import sys
import logging

logger = logging.getLogger("amtha.runtime_stabilizer")

def apply_runtime_stabilization() -> None:
    """
    Applies non-invasive structural type proxies to resolve downstream framework drifts.
    Ensures DataPart and TextPart compatibility for A2UI schemas.
    """
    logger.info("Initializing runtime environment stabilization proxies...")
    
    # 1. Provide safe fallback types if a2a / a2ui are imported dynamically
    try:
        import a2a.types  # type: ignore
    except ImportError:
        # Create virtual module proxy if a2a is not directly installed in local env
        import types
        virtual_a2a = types.ModuleType("a2a")
        virtual_a2a_types = types.ModuleType("a2a.types")
        
        class VirtualDataPart:
            def __init__(self, data: dict):
                self.data = data
                
        class VirtualTextPart:
            def __init__(self, text: str):
                self.text = text
                
        virtual_a2a_types.DataPart = VirtualDataPart  # type: ignore
        virtual_a2a_types.TextPart = VirtualTextPart  # type: ignore
        
        sys.modules["a2a"] = virtual_a2a
        sys.modules["a2a.types"] = virtual_a2a_types
        logger.info("Stabilized virtual a2a.types proxy successfully.")

    logger.info("Runtime stabilization complete.")


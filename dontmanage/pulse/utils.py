"""Compatibility shim: keep old `dontmanage.pulse.utils` imports working."""

from dontmanage.utils import get_app_version, get_dontmanage_version

__all__ = ["get_app_version", "get_dontmanage_version"]

"""
Base plugin system for Ignis AI.
Allows extending functionality through plugins.
"""

import asyncio
import importlib
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..utils.logger import get_logger

logger = get_logger(__name__)


class BasePlugin(ABC):
    """
    Base class for Ignis plugins.
    """

    def __init__(self, name: str, description: str = ""):
        """
        Initialize plugin.

        Args:
            name: Plugin name
            description: Plugin description
        """
        self.name = name
        self.description = description
        self.enabled = True
        self.logger = get_logger(f"plugin.{name}")

    @abstractmethod
    async def process_message(self, message: str) -> Optional[str]:
        """
        Process user message before sending to AI.

        Args:
            message: User message

        Returns:
            Modified message or None to pass through
        """
        pass

    @abstractmethod
    async def process_response(self, message: str, response: str) -> str:
        """
        Process AI response before returning to user.

        Args:
            message: Original user message
            response: AI response

        Returns:
            Modified response
        """
        pass

    def get_status(self) -> Dict[str, Any]:
        """Get plugin status."""
        return {
            'name': self.name,
            'description': self.description,
            'enabled': self.enabled
        }

    def initialize(self):
        """Initialize plugin (called on load)."""
        pass

    async def shutdown(self):
        """Shutdown plugin (called on unload)."""
        pass


class PluginManager:
    """
    Manages loading and execution of plugins.
    """

    def __init__(self):
        """Initialize plugin manager."""
        self.plugins: Dict[str, BasePlugin] = {}
        self.logger = get_logger(__name__)

        # Auto-load built-in plugins
        self._load_builtin_plugins()

    def _load_builtin_plugins(self):
        """Load built-in plugins."""
        builtin_plugins = [
            'coding_assistant',
            'document_reader',
            'calculator'
        ]

        for plugin_name in builtin_plugins:
            try:
                self._load_plugin(plugin_name)
            except Exception as e:
                self.logger.warning(f"Failed to load built-in plugin {plugin_name}: {e}")

    def _load_plugin(self, plugin_name: str):
        """Load a plugin by name."""
        try:
            # Import plugin module
            module = importlib.import_module(f'.{plugin_name}', package='src.plugins')

            # Find plugin class (assumed to be named <PluginName>Plugin)
            class_name = f"{plugin_name.replace('_', ' ').title().replace(' ', '')}Plugin"
            plugin_class = getattr(module, class_name)

            # Instantiate plugin
            plugin_instance = plugin_class()

            # Initialize plugin
            plugin_instance.initialize()

            # Register plugin
            self.plugins[plugin_name] = plugin_instance

            self.logger.info(f"Loaded plugin: {plugin_name}")

        except (ImportError, AttributeError) as e:
            self.logger.error(f"Failed to load plugin {plugin_name}: {e}")
            raise

    async def process_message(self, message: str) -> str:
        """
        Process message through all enabled plugins.

        Args:
            message: User message

        Returns:
            Processed message
        """
        processed_message = message

        for plugin in self.plugins.values():
            if plugin.enabled:
                try:
                    result = await plugin.process_message(processed_message)
                    if result is not None:
                        processed_message = result
                except Exception as e:
                    self.logger.error(f"Plugin {plugin.name} failed processing message: {e}")

        return processed_message

    async def process_response(self, message: str, response: str) -> str:
        """
        Process response through all enabled plugins.

        Args:
            message: Original user message
            response: AI response

        Returns:
            Processed response
        """
        processed_response = response

        for plugin in self.plugins.values():
            if plugin.enabled:
                try:
                    processed_response = await plugin.process_response(message, processed_response)
                except Exception as e:
                    self.logger.error(f"Plugin {plugin.name} failed processing response: {e}")

        return processed_response

    def enable_plugin(self, plugin_name: str) -> bool:
        """
        Enable a plugin.

        Args:
            plugin_name: Name of plugin to enable

        Returns:
            True if successful
        """
        if plugin_name in self.plugins:
            self.plugins[plugin_name].enabled = True
            self.logger.info(f"Enabled plugin: {plugin_name}")
            return True
        return False

    def disable_plugin(self, plugin_name: str) -> bool:
        """
        Disable a plugin.

        Args:
            plugin_name: Name of plugin to disable

        Returns:
            True if successful
        """
        if plugin_name in self.plugins:
            self.plugins[plugin_name].enabled = False
            self.logger.info(f"Disabled plugin: {plugin_name}")
            return True
        return False

    def get_plugin_status(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a specific plugin.

        Args:
            plugin_name: Plugin name

        Returns:
            Plugin status or None if not found
        """
        plugin = self.plugins.get(plugin_name)
        return plugin.get_status() if plugin else None

    def get_status(self) -> Dict[str, Any]:
        """Get plugin manager status."""
        plugin_statuses = {}
        for name, plugin in self.plugins.items():
            plugin_statuses[name] = plugin.get_status()

        return {
            'total_plugins': len(self.plugins),
            'enabled_plugins': sum(1 for p in self.plugins.values() if p.enabled),
            'plugins': plugin_statuses
        }

    async def shutdown(self):
        """Shutdown all plugins."""
        for plugin in self.plugins.values():
            try:
                await plugin.shutdown()
            except Exception as e:
                self.logger.error(f"Error shutting down plugin {plugin.name}: {e}")

        self.plugins.clear()
        self.logger.info("Plugin manager shutdown complete")
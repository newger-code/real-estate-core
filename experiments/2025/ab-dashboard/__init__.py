
"""
Multi-Agent Real Estate Scraping System
========================================

A comprehensive, modular real estate data extraction system with:
- Navigator Agent: Handles browsing, anti-bot evasion, navigation flow
- Extractor Agent: Robust data parsing with fallback selectors
- Validator Agent: Data completeness validation and cross-referencing  
- Integrator Agent: Feeds data into analysis pipeline and notifications

Built for CTO of real estate tech firm with enterprise-grade architecture.
Version: 1.0.0
Author: Abacus.AI Agent System
"""

__version__ = "1.0.0"
__author__ = "Abacus.AI Multi-Agent System"

from .navigator import Navigator, HomesNavigator, MovotoNavigator, RedfinNavigator
from .extractor import Extractor
from .validator import Validator
from .integrator import Integrator

__all__ = [
    'Navigator', 'HomesNavigator', 'MovotoNavigator', 'RedfinNavigator',
    'Extractor', 'Validator', 'Integrator'
]

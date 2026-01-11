"""
Custom exception classes for better error handling
"""

from __future__ import annotations


class CareerCoachError(Exception):
    """Base exception for Career Coach application"""
    pass


class ConfigurationError(CareerCoachError):
    """Raised when configuration is invalid"""
    pass


class YandexGPTError(CareerCoachError):
    """Raised when YandexGPT API call fails"""
    pass


class MongoDBError(CareerCoachError):
    """Raised when MongoDB operation fails"""
    pass


class FAISSError(CareerCoachError):
    """Raised when FAISS operation fails"""
    pass


class ProfileNotFoundError(CareerCoachError):
    """Raised when profile is not found"""
    pass


class SessionNotFoundError(CareerCoachError):
    """Raised when session is not found"""
    pass




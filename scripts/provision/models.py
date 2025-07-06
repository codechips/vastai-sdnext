"""
Data models and validation for the provisioning system.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, HttpUrl, validator, Field


class ModelSource(Enum):
    """Supported model sources."""
    HUGGINGFACE = "huggingface"
    CIVITAI = "civitai"
    DIRECT_URL = "url"


class ProvisioningError(Exception):
    """Base exception for provisioning errors."""
    pass


class ConfigurationError(ProvisioningError):
    """Invalid configuration."""
    pass


class DownloadError(ProvisioningError):
    """Download failed."""
    
    def __init__(self, model_name: str, reason: str):
        self.model_name = model_name
        self.reason = reason
        super().__init__(f"Download failed for {model_name}: {reason}")


class TokenValidationError(ProvisioningError):
    """Token validation failed."""
    pass


@dataclass
class ModelConfig:
    """Configuration for a single model."""
    name: str
    source: ModelSource
    target_dir: Path
    repo: Optional[str] = None
    version_id: Optional[str] = None  # CivitAI version ID (formerly model_id)
    url: Optional[str] = None
    filename: Optional[str] = None
    file: Optional[str] = None  # For HuggingFace specific files
    gated: bool = False
    headers: Dict[str, str] = Field(default_factory=dict)
    
    def __post_init__(self):
        """Validate model configuration after initialization."""
        if self.source == ModelSource.HUGGINGFACE and not self.repo:
            raise ConfigurationError(f"HuggingFace models require 'repo' field for {self.name}")
        elif self.source == ModelSource.CIVITAI and not self.version_id:
            raise ConfigurationError(f"CivitAI models require 'version_id' field for {self.name}")
        elif self.source == ModelSource.DIRECT_URL and not self.url:
            raise ConfigurationError(f"Direct URL models require 'url' field for {self.name}")


class ModelConfigPydantic(BaseModel):
    """Pydantic model for validation of model configurations."""
    source: Optional[str] = None
    repo: Optional[str] = None
    version_id: Optional[str] = None  # CivitAI version ID (formerly model_id)
    url: Optional[HttpUrl] = None
    filename: Optional[str] = None
    file: Optional[str] = None
    gated: bool = False
    headers: Dict[str, str] = Field(default_factory=dict)
    
    @validator('source', pre=True, always=True)
    def validate_source(cls, v, values):
        """Auto-detect source if not provided."""
        if v:
            return v
        
        # Auto-detect based on available fields
        if 'repo' in values and values['repo']:
            return ModelSource.HUGGINGFACE.value
        elif 'version_id' in values and values['version_id']:
            return ModelSource.CIVITAI.value
        elif 'url' in values and values['url']:
            return ModelSource.DIRECT_URL.value
        else:
            return "unknown"
    
    @validator('repo')
    def validate_repo(cls, v, values):
        """Validate repo for HuggingFace models."""
        source = values.get('source')
        if source == ModelSource.HUGGINGFACE.value and not v:
            raise ValueError('repo required for HuggingFace models')
        return v
    
    @validator('version_id')
    def validate_version_id(cls, v, values):
        """Validate version_id for CivitAI models."""
        source = values.get('source')
        if source == ModelSource.CIVITAI.value and not v:
            raise ValueError('version_id required for CivitAI models')
        return v
    
    @validator('url')
    def validate_url(cls, v, values):
        """Validate URL for direct URL models."""
        source = values.get('source')
        if source == ModelSource.DIRECT_URL.value and not v:
            raise ValueError('url required for direct URL models')
        return v


class ProvisionConfigPydantic(BaseModel):
    """Pydantic model for the entire provision configuration."""
    models: Dict[str, Dict[str, ModelConfigPydantic]]
    
    @validator('models')
    def validate_models(cls, v):
        """Validate all model configurations."""
        for category, models in v.items():
            for model_name, model_config in models.items():
                # Additional validation can be added here
                pass
        return v


@dataclass
class DownloadResult:
    """Result of a download operation."""
    model_name: str
    success: bool
    error_message: Optional[str] = None
    file_path: Optional[Path] = None
    size_bytes: Optional[int] = None
    
    def __str__(self) -> str:
        if self.success:
            return f"✅ {self.model_name}: Download successful"
        else:
            return f"❌ {self.model_name}: {self.error_message}"


@dataclass 
class ProvisioningSummary:
    """Summary of provisioning operation."""
    total_models: int
    successful_downloads: int
    failed_downloads: int
    skipped_models: int
    results: List[DownloadResult] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_models == 0:
            return 0.0
        return (self.successful_downloads / self.total_models) * 100
    
    def __str__(self) -> str:
        return (
            f"Provisioning Summary:\n"
            f"  Total models: {self.total_models}\n"
            f"  Successful: {self.successful_downloads}\n"
            f"  Failed: {self.failed_downloads}\n"
            f"  Skipped: {self.skipped_models}\n"
            f"  Success rate: {self.success_rate:.1f}%"
        )
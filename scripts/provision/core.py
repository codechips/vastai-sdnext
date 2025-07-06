"""
VastAI Forge Provisioning System - Core Module

Main orchestrator for downloading models from HuggingFace, CivitAI, and direct URLs.
Supports parallel downloads, token validation, and graceful error handling.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from contextlib import asynccontextmanager

import aiohttp

# Fix imports when running as a script
if __package__ is None:
    # Add current directory to path for imports
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Try both import styles
try:
    from config.parser import ConfigParser
    from downloaders.civitai import CivitAIDownloader
    from downloaders.direct import DirectURLDownloader
    from downloaders.huggingface import HuggingFaceDownloader
    from models import (
        ModelConfig, ModelSource, ProvisioningError, DownloadError,
        DownloadResult, ProvisioningSummary, ProvisionConfigPydantic
    )
    from utils.logging import setup_logging
    from utils.progress import ProgressTracker
    from validators.tokens import TokenValidator
except ImportError:
    from .config.parser import ConfigParser
    from .downloaders.civitai import CivitAIDownloader
    from .downloaders.direct import DirectURLDownloader
    from .downloaders.huggingface import HuggingFaceDownloader
    from .models import (
        ModelConfig, ModelSource, ProvisioningError, DownloadError,
        DownloadResult, ProvisioningSummary, ProvisionConfigPydantic
    )
    from .utils.logging import setup_logging
    from .utils.progress import ProgressTracker
    from .validators.tokens import TokenValidator


class ProvisioningSystem:
    """Main provisioning orchestrator with type safety and async context management."""

    def __init__(self, workspace_dir: Optional[str] = None, max_concurrent: int = 5) -> None:
        # Use environment variable or default
        if workspace_dir is None:
            workspace_dir = os.environ.get("WORKSPACE", "/workspace")
        self.workspace_dir: Path = Path(workspace_dir)
        self.models_dir: Path = self.workspace_dir / "forge" / "models"
        self.logs_dir: Path = self.workspace_dir / "logs"
        self.dry_run: bool = False
        self.max_concurrent: int = max_concurrent
        self._semaphore: asyncio.Semaphore = asyncio.Semaphore(max_concurrent)

        # Ensure directories exist
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.config_parser = ConfigParser()
        self.token_validator = TokenValidator()
        self.progress_tracker = ProgressTracker()

        # Initialize downloaders
        self.hf_downloader = HuggingFaceDownloader()
        self.civitai_downloader = CivitAIDownloader()
        self.direct_downloader = DirectURLDownloader()

        # Setup logging
        setup_logging(self.logs_dir / "provision.log")
        self.logger = logging.getLogger(__name__)
    
    @asynccontextmanager
    async def session(self):
        """Async context manager for HTTP sessions."""
        timeout = aiohttp.ClientTimeout(total=3600)  # 1 hour timeout
        session = aiohttp.ClientSession(timeout=timeout)
        try:
            yield session
        finally:
            await session.close()

    async def provision_from_url(self, config_url: str) -> ProvisioningSummary:
        """
        Provision models from a remote configuration URL.

        Args:
            config_url: URL to fetch TOML configuration from

        Returns:
            ProvisioningSummary with detailed results

        Raises:
            ProvisioningError: If provisioning fails completely
        """
        try:
            self.logger.info(f"Starting provisioning from URL: {config_url}")

            # Fetch and parse configuration with Pydantic validation
            config_dict = await self.config_parser.fetch_and_parse(config_url)
            config = ProvisionConfigPydantic(**config_dict)

            # Validate tokens for gated models
            await self._validate_tokens(config_dict)

            # Download models in parallel
            summary = await self._download_models_typed(config)

            if summary.failed_downloads == 0:
                self.logger.info("Provisioning completed successfully")
            else:
                self.logger.warning(f"Provisioning completed with {summary.failed_downloads} failures")

            return summary

        except Exception as e:
            self.logger.error(f"Provisioning failed: {e}")
            raise ProvisioningError(f"Provisioning from URL failed: {e}") from e

    async def provision_from_file(self, config_path: str) -> bool:
        """
        Provision models from a local configuration file.

        Args:
            config_path: Path to local TOML configuration file

        Returns:
            True if provisioning succeeded, False otherwise
        """
        try:
            self.logger.info(f"Starting provisioning from file: {config_path}")

            # Parse local configuration
            config = await self.config_parser.parse_file(config_path)

            # Validate tokens for gated models
            await self._validate_tokens(config)

            # Download models in parallel
            success = await self._download_models(config)

            if success:
                self.logger.info("Provisioning completed successfully")
            else:
                self.logger.warning("Provisioning completed with some failures")

            return success

        except Exception as e:
            self.logger.error(f"Provisioning failed: {e}")
            return False

    async def _validate_tokens(self, config: Dict) -> None:
        """Validate authentication tokens for gated models."""
        self.logger.info("Validating authentication tokens...")

        # Check if we have any gated models
        gated_models = self._find_gated_models(config)
        if not gated_models:
            self.logger.info("No gated models found, skipping token validation")
            return

        # Validate HuggingFace token
        hf_valid = await self.token_validator.validate_hf_token()
        if hf_valid:
            self.logger.info("✅ HuggingFace token is valid")
        else:
            self.logger.warning("⚠️  HuggingFace token is invalid or missing")

        # Validate CivitAI token
        civitai_valid = await self.token_validator.validate_civitai_token()
        if civitai_valid:
            self.logger.info("✅ CivitAI token is valid")
        else:
            self.logger.warning("⚠️  CivitAI token is invalid or missing")

        # Log gated model access status
        for model in gated_models:
            source = model.get("source", "unknown")
            if source == "huggingface" and not hf_valid:
                self._log_gated_model_error(model, "HuggingFace")
            elif source == "civitai" and not civitai_valid:
                self._log_gated_model_error(model, "CivitAI")

    def _find_gated_models(self, config: Dict) -> List[Dict]:
        """Find all gated models in configuration."""
        gated_models = []

        for category in config.get("models", {}).values():
            for model_name, model_config in category.items():
                if isinstance(model_config, dict) and model_config.get("gated", False):
                    gated_models.append(model_config)

        return gated_models

    def _log_gated_model_error(self, model: Dict, platform: str) -> None:
        """Log clear error message for inaccessible gated model."""
        self.logger.error("🔒 GATED MODEL ACCESS DENIED")
        self.logger.error(
            f"Model: {model.get('repo', model.get('version_id', 'unknown'))}"
        )
        self.logger.error(f"Platform: {platform}")
        self.logger.error("Reason: Terms of Service not accepted or invalid token")

        if platform == "HuggingFace":
            repo = model.get("repo", "")
            if repo:
                self.logger.error(
                    f"Action: Visit https://huggingface.co/{repo} and click 'Agree and access repository'"
                )
        elif platform == "CivitAI":
            self.logger.error("Action: Ensure you have a valid CivitAI API token")

        self.logger.error("Status: SKIPPED")
        self.logger.error("")

    async def _download_models(self, config: Dict) -> bool:
        """Download all models in parallel."""
        download_tasks = []

        # Process each model category
        for category, models in config.get("models", {}).items():
            target_dir = self.models_dir / self._get_category_dir(category)

            if not self.dry_run:
                target_dir.mkdir(parents=True, exist_ok=True)

            for model_name, model_config in models.items():
                if self.dry_run:
                    # In dry run mode, just validate the configuration
                    self.logger.info(f"✅ Would download {model_name} to {target_dir}")
                    continue

                task = self._create_download_task(model_name, model_config, target_dir)
                if task:
                    download_tasks.append(task)

        if self.dry_run:
            self.logger.info("✅ Dry run completed - all configurations are valid")
            return True

        if not download_tasks:
            self.logger.warning("No models to download")
            return True

        self.logger.info(f"Starting {len(download_tasks)} parallel downloads...")

        # Execute downloads in parallel
        results = await asyncio.gather(*download_tasks, return_exceptions=True)

        # Count successes and failures
        successes = sum(1 for result in results if result is True)
        failures = len(results) - successes

        self.logger.info(f"Download results: {successes} succeeded, {failures} failed")

        return failures == 0

    async def _download_models_typed(self, config: ProvisionConfigPydantic) -> ProvisioningSummary:
        """Download all models with type safety and detailed results."""
        download_tasks = []
        model_configs: List[ModelConfig] = []

        # Process each model category
        for category, models in config.models.items():
            target_dir = self.models_dir / self._get_category_dir(category)

            if not self.dry_run:
                target_dir.mkdir(parents=True, exist_ok=True)

            for model_name, model_config_data in models.items():
                try:
                    # Create typed model configuration
                    source = ModelSource(model_config_data.source)
                    model_config = ModelConfig(
                        name=model_name,
                        source=source,
                        target_dir=target_dir,
                        repo=model_config_data.repo,
                        version_id=model_config_data.version_id,
                        url=str(model_config_data.url) if model_config_data.url else None,
                        filename=model_config_data.filename,
                        file=model_config_data.file,
                        gated=model_config_data.gated,
                        headers=model_config_data.headers
                    )
                    model_configs.append(model_config)

                    if self.dry_run:
                        self.logger.info(f"✅ Would download {model_name} to {target_dir}")
                        continue

                    task = self._create_typed_download_task(model_config)
                    if task:
                        download_tasks.append(task)

                except Exception as e:
                    self.logger.error(f"Invalid model configuration for {model_name}: {e}")

        if self.dry_run:
            self.logger.info("✅ Dry run completed - all configurations are valid")
            return ProvisioningSummary(
                total_models=len(model_configs),
                successful_downloads=len(model_configs),
                failed_downloads=0,
                skipped_models=0
            )

        if not download_tasks:
            self.logger.warning("No models to download")
            return ProvisioningSummary(
                total_models=0,
                successful_downloads=0,
                failed_downloads=0,
                skipped_models=0
            )

        self.logger.info(f"Starting {len(download_tasks)} parallel downloads...")

        # Execute downloads with controlled concurrency
        results = await self._execute_concurrent_downloads(download_tasks)

        # Create summary
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful

        self.logger.info(f"Download results: {successful} succeeded, {failed} failed")

        return ProvisioningSummary(
            total_models=len(results),
            successful_downloads=successful,
            failed_downloads=failed,
            skipped_models=0,
            results=results
        )

    async def _execute_concurrent_downloads(self, download_tasks: List) -> List[DownloadResult]:
        """Execute downloads with controlled concurrency."""
        async def download_with_semaphore(task):
            async with self._semaphore:
                return await task

        tasks = [download_with_semaphore(task) for task in download_tasks]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to DownloadResult objects
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(DownloadResult(
                    model_name=f"model_{i}",
                    success=False,
                    error_message=str(result)
                ))
            else:
                processed_results.append(result)
        
        return processed_results

    async def _create_typed_download_task(self, model_config: ModelConfig):
        """Create typed download task."""
        try:
            if model_config.source == ModelSource.HUGGINGFACE:
                return self._download_huggingface_model_typed(model_config)
            elif model_config.source == ModelSource.CIVITAI:
                return self._download_civitai_model_typed(model_config)
            elif model_config.source == ModelSource.DIRECT_URL:
                return self._download_direct_url_typed(model_config)
            else:
                return DownloadResult(
                    model_name=model_config.name,
                    success=False,
                    error_message=f"Unknown source: {model_config.source}"
                )
        except Exception as e:
            return DownloadResult(
                model_name=model_config.name,
                success=False,
                error_message=str(e)
            )

    async def _download_huggingface_model_typed(self, model_config: ModelConfig) -> DownloadResult:
        """Download HuggingFace model with typed result."""
        try:
            success = await self.hf_downloader.download(
                model_name=model_config.name,
                repo_id=model_config.repo,
                filename=model_config.file or "",
                target_dir=model_config.target_dir,
                gated=model_config.gated,
            )
            return DownloadResult(
                model_name=model_config.name,
                success=success,
                file_path=model_config.target_dir if success else None
            )
        except Exception as e:
            return DownloadResult(
                model_name=model_config.name,
                success=False,
                error_message=f"HuggingFace download failed: {e}"
            )

    async def _download_civitai_model_typed(self, model_config: ModelConfig) -> DownloadResult:
        """Download CivitAI model with typed result."""
        try:
            success = await self.civitai_downloader.download(
                model_name=model_config.name,
                version_id=model_config.version_id,
                target_dir=model_config.target_dir,
                filename=model_config.filename or "",
            )
            return DownloadResult(
                model_name=model_config.name,
                success=success,
                file_path=model_config.target_dir if success else None
            )
        except Exception as e:
            return DownloadResult(
                model_name=model_config.name,
                success=False,
                error_message=f"CivitAI download failed: {e}"
            )

    async def _download_direct_url_typed(self, model_config: ModelConfig) -> DownloadResult:
        """Download direct URL model with typed result."""
        try:
            success = await self.direct_downloader.download(
                model_name=model_config.name,
                url=model_config.url,
                target_dir=model_config.target_dir,
                filename=model_config.filename or "",
                headers=model_config.headers,
            )
            return DownloadResult(
                model_name=model_config.name,
                success=success,
                file_path=model_config.target_dir if success else None
            )
        except Exception as e:
            return DownloadResult(
                model_name=model_config.name,
                success=False,
                error_message=f"Direct URL download failed: {e}"
            )

    def _get_category_dir(self, category: str) -> str:
        """Map category to directory name."""
        category_mapping = {
            "checkpoints": "Stable-diffusion",
            "lora": "Lora",
            "vae": "VAE",
            "controlnet": "ControlNet",
            "esrgan": "ESRGAN",
            "embeddings": "embeddings",
            "hypernetworks": "hypernetworks",
            "text_encoder": "text_encoder",
            "clip": "text_encoder",  # Alias for text_encoder
        }
        return category_mapping.get(category, category)

    def _create_download_task(
        self, model_name: str, model_config: Dict, target_dir: Path
    ):
        """Create download task for a model."""
        if isinstance(model_config, str):
            # Simple URL string
            return self._download_direct_url(model_name, model_config, target_dir)

        if not isinstance(model_config, dict):
            self.logger.error(f"Invalid model config for {model_name}: {model_config}")
            return None

        source = model_config.get("source", self._detect_source(model_config))

        if source == "huggingface":
            return self._download_huggingface_model(
                model_name, model_config, target_dir
            )
        elif source == "civitai":
            return self._download_civitai_model(model_name, model_config, target_dir)
        elif source == "url":
            return self._download_direct_url(model_name, model_config, target_dir)
        else:
            self.logger.error(f"Unknown source '{source}' for model {model_name}")
            return None

    def _detect_source(self, model_config: Dict) -> str:
        """Auto-detect source from model configuration."""
        if "repo" in model_config:
            return "huggingface"
        elif "version_id" in model_config:
            return "civitai"
        elif "url" in model_config:
            return "url"
        else:
            return "unknown"

    async def _download_huggingface_model(
        self, model_name: str, config: Dict, target_dir: Path
    ) -> bool:
        """Download model from HuggingFace."""
        try:
            return await self.hf_downloader.download(
                model_name=model_name,
                repo_id=config["repo"],
                filename=config.get("file", ""),
                target_dir=target_dir,
                gated=config.get("gated", False),
            )
        except Exception as e:
            self.logger.error(f"HuggingFace download failed for {model_name}: {e}")
            return False

    async def _download_civitai_model(
        self, model_name: str, config: Dict, target_dir: Path
    ) -> bool:
        """Download model from CivitAI."""
        try:
            return await self.civitai_downloader.download(
                model_name=model_name,
                version_id=config["version_id"],
                target_dir=target_dir,
                filename=config.get("filename", ""),
            )
        except Exception as e:
            self.logger.error(f"CivitAI download failed for {model_name}: {e}")
            return False

    async def _download_direct_url(
        self, model_name: str, config, target_dir: Path
    ) -> bool:
        """Download model from direct URL."""
        try:
            if isinstance(config, str):
                url = config
                filename = ""
                headers = {}
            else:
                url = config["url"]
                filename = config.get("filename", "")
                headers = config.get("headers", {})

            return await self.direct_downloader.download(
                model_name=model_name,
                url=url,
                target_dir=target_dir,
                filename=filename,
                headers=headers,
            )
        except Exception as e:
            self.logger.error(f"Direct URL download failed for {model_name}: {e}")
            return False
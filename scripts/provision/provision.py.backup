#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "aiohttp",
#     "tomli",
#     "huggingface_hub[hf_transfer]",
# ]
# ///
"""
VastAI Forge Provisioning System

Main orchestrator for downloading models from HuggingFace, CivitAI, and direct URLs.
Supports parallel downloads, token validation, and graceful error handling.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List

# Fix imports when running as a script
if __package__ is None and __name__ == "__main__":
    # Add parent directory to path for imports
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Use absolute imports that work in both cases
from downloaders.civitai import CivitAIDownloader
from downloaders.direct import DirectURLDownloader
from downloaders.huggingface import HuggingFaceDownloader
from utils.logging import setup_logging
from utils.progress import ProgressTracker
from validators.tokens import TokenValidator

from config.parser import ConfigParser


class ProvisioningSystem:
    """Main provisioning orchestrator."""

    def __init__(self, workspace_dir: str = ""):
        # Use environment variable or default
        if workspace_dir is None:
            workspace_dir = os.environ.get("WORKSPACE", "/workspace")
        self.workspace_dir = Path(workspace_dir)
        self.models_dir = self.workspace_dir / "forge" / "models"
        self.logs_dir = self.workspace_dir / "logs"
        self.dry_run = False

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

    async def provision_from_url(self, config_url: str) -> bool:
        """
        Provision models from a remote configuration URL.

        Args:
            config_url: URL to fetch TOML configuration from

        Returns:
            True if provisioning succeeded, False otherwise
        """
        try:
            self.logger.info(f"Starting provisioning from URL: {config_url}")

            # Fetch and parse configuration
            config = await self.config_parser.fetch_and_parse(config_url)

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
            f"Model: {model.get('repo', model.get('model_id', 'unknown'))}"
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
        elif "model_id" in model_config:
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
                model_id=config["model_id"],
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


async def main():
    """Main entry point for provisioning."""
    import argparse

    parser = argparse.ArgumentParser(
        description="VastAI Forge Provisioning System - Download models from various sources",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s config.toml                    # Provision from local config file
  %(prog)s http://example.com/config.toml # Provision from remote config
  %(prog)s config.toml --dry-run          # Validate config without downloading

Environment Variables:
  WORKSPACE      - Target directory for models (default: /workspace)
  HF_TOKEN       - HuggingFace API token for gated models
  CIVITAI_TOKEN  - CivitAI API token for some models
        """,
    )

    parser.add_argument("config", help="Path to TOML config file or URL")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate configuration and tokens without downloading models",
    )
    parser.add_argument(
        "--workspace",
        help="Override workspace directory (default: $WORKSPACE or /workspace)",
    )

    args = parser.parse_args()

    # Create provisioner with custom workspace if specified
    provisioner = ProvisioningSystem(args.workspace)

    # For dry run, we'll add a dry_run parameter to the provisioning methods
    if args.dry_run:
        provisioner.dry_run = True
        print("🔍 Dry run mode - validating configuration without downloading")

    # Determine if source is URL or file path
    if args.config.startswith(("http://", "https://")):
        success = await provisioner.provision_from_url(args.config)
    else:
        success = await provisioner.provision_from_file(args.config)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())

"""
Command-line interface for the VastAI Forge Provisioning System.
"""

import argparse
import os
import sys

# Fix imports when running as a script
if __package__ is None:
    # Add current directory to path for imports
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Try both import styles
try:
    from core import ProvisioningSystem
except ImportError:
    from .core import ProvisioningSystem


async def main():
    """Main entry point for provisioning."""
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
    try:
        if args.config.startswith(("http://", "https://")):
            result = await provisioner.provision_from_url(args.config)
        else:
            result = await provisioner.provision_from_file(args.config)
        
        # Handle both old boolean and new ProvisioningSummary return types
        if hasattr(result, 'success_rate'):
            # New ProvisioningSummary type
            print(f"\n{result}")
            success = result.failed_downloads == 0
        else:
            # Old boolean type
            success = result
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"❌ Provisioning failed: {e}")
        sys.exit(1)
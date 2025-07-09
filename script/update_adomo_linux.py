#!/usr/bin/env python3
"""
Update ADOMO Libraries for Linux Compatibility

This script downloads the latest Microsoft.AnalysisServices.AdomdClient NuGet package
and extracts the cross-platform .NET libraries to replace Windows-only DLLs.

Usage:
    python script/update_adomo_linux.py [--version VERSION] [--dry-run]
    
Author: PyTabular Team
Date: 2024
"""

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.request import urlretrieve
from urllib.parse import urljoin

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('update_adomo.log')
    ]
)
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
DLL_DIR = PROJECT_ROOT / "pytabular" / "dll"
BACKUP_DIR = PROJECT_ROOT / "dll_backup"
TEMP_DIR = Path(tempfile.mkdtemp())

# NuGet package information - ONLY the DLLs that PyTabular actually needs and work cross-platform
NUGET_PACKAGES = {
    "Microsoft.AnalysisServices.AdomdClient": {
        "description": "ADOMD.NET client library for Analysis Services",
        "dll_name": "Microsoft.AnalysisServices.AdomdClient.dll"
    },
    "Microsoft.AnalysisServices": {
        "description": "Analysis Services Management Objects (AMO)",
        "dll_name": "Microsoft.AnalysisServices.dll",
        "additional_dlls": ["Microsoft.AnalysisServices.Core.dll", "Microsoft.AnalysisServices.Runtime.Core.dll", "Microsoft.AnalysisServices.Tabular.dll"]  # Core dependencies + Tabular for TOM
    }
}

# Collect ALL required DLLs (main + additional)
REQUIRED_DLLS = set()
for pkg in NUGET_PACKAGES.values():
    REQUIRED_DLLS.add(pkg["dll_name"])
    REQUIRED_DLLS.update(pkg.get("additional_dlls", []))

class NuGetPackageManager:
    """Manages NuGet package downloads and extraction."""
    
    def __init__(self, temp_dir: Path):
        self.temp_dir = temp_dir
        self.nuget_api_base = "https://api.nuget.org/v3-flatcontainer"
        self.nuget_search_api = "https://azuresearch-usnc.nuget.org/query"
        
    def get_latest_version(self, package_name: str) -> Optional[str]:
        """Get the latest version of a NuGet package."""
        logger.info(f"Fetching latest version for {package_name}")
        
        try:
            response = requests.get(
                f"{self.nuget_search_api}?q=packageid:{package_name}&take=1"
            )
            response.raise_for_status()
            
            data = response.json()
            if data["data"]:
                version = data["data"][0]["version"]
                logger.info(f"Latest version for {package_name}: {version}")
                return version
            else:
                logger.error(f"No versions found for {package_name}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Error fetching version for {package_name}: {e}")
            return None
    

    
    def download_package(self, package_name: str, version: str) -> Optional[Path]:
        """Download a NuGet package."""
        logger.info(f"Downloading {package_name} v{version}")
        
        # NuGet package URL format
        package_url = f"{self.nuget_api_base}/{package_name.lower()}/{version.lower()}/{package_name.lower()}.{version.lower()}.nupkg"
        
        try:
            package_file = self.temp_dir / f"{package_name}.{version}.nupkg"
            
            logger.info(f"Downloading from: {package_url}")
            urlretrieve(package_url, package_file)
            
            logger.info(f"Downloaded to: {package_file}")
            return package_file
            
        except Exception as e:
            logger.error(f"Error downloading {package_name}: {e}")
            return None
    
    def extract_package(self, package_file: Path) -> Optional[Path]:
        """Extract a NuGet package."""
        logger.info(f"Extracting {package_file}")
        
        try:
            extract_dir = self.temp_dir / package_file.stem
            extract_dir.mkdir(exist_ok=True)
            
            with zipfile.ZipFile(package_file, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            logger.info(f"Extracted to: {extract_dir}")
            return extract_dir
            
        except Exception as e:
            logger.error(f"Error extracting {package_file}: {e}")
            return None
    
    def find_specific_dll(self, extract_dir: Path, dll_name: str) -> Optional[Path]:
        """Find a specific DLL in the extracted package - CROSS-PLATFORM ONLY."""
        logger.info(f"Searching for {dll_name} in {extract_dir}")
        
        lib_dir = extract_dir / "lib"
        
        if not lib_dir.exists():
            logger.warning(f"No lib directory found in {extract_dir}")
            return None
        
        # ONLY look for .NET 6.0+ libraries (cross-platform) - NO FALLBACK to .NET Framework
        cross_platform_frameworks = ["net8.0", "net7.0", "net6.0", "netstandard2.0"]
        
        for target_framework in cross_platform_frameworks:
            framework_dir = lib_dir / target_framework
            if framework_dir.exists():
                dll_file = framework_dir / dll_name
                if dll_file.exists():
                    logger.info(f"✅ Found {dll_name} in {target_framework}: {dll_file}")
                    return dll_file
                else:
                    logger.debug(f"DLL {dll_name} not found in {framework_dir}")
        
        # Check what's actually available
        available_dirs = [d.name for d in lib_dir.iterdir() if d.is_dir()]
        logger.warning(f"❌ {dll_name} not found in cross-platform frameworks")
        logger.warning(f"Available framework directories: {available_dirs}")
        return None



class AdomoUpdater:
    """Main class for updating ADOMO libraries."""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.package_manager = NuGetPackageManager(TEMP_DIR)
        self.updated_packages = {}
        
    def backup_existing_dlls(self):
        """Backup existing DLL files."""
        logger.info("Backing up existing DLL files...")
        
        if not DLL_DIR.exists():
            logger.warning(f"DLL directory not found: {DLL_DIR}")
            return
        
        if self.dry_run:
            logger.info("[DRY RUN] Would backup DLLs to: %s", BACKUP_DIR)
            return
        
        BACKUP_DIR.mkdir(exist_ok=True)
        
        for dll_file in DLL_DIR.glob("*.dll"):
            backup_file = BACKUP_DIR / dll_file.name
            shutil.copy2(dll_file, backup_file)
            logger.info(f"Backed up: {dll_file} -> {backup_file}")
    

    

    
    def update_all_packages(self, version: Optional[str] = None) -> bool:
        """Update all ADOMO packages with optimized workflow: download → delete → replace."""
        logger.info("Starting ADOMO package update...")
        logger.info(f"Will update ALL {len(REQUIRED_DLLS)} required DLLs: {', '.join(sorted(REQUIRED_DLLS))}")
        
        # PHASE 1: Download all packages first
        logger.info("📥 PHASE 1: Downloading all packages...")
        downloaded_packages = {}
        
        for package_name in NUGET_PACKAGES:
            # Get latest version if not specified
            pkg_version = version
            if not pkg_version:
                pkg_version = self.package_manager.get_latest_version(package_name)
                if not pkg_version:
                    logger.error(f"Could not determine version for {package_name}")
                    return False
            
            # Download package
            package_file = self.package_manager.download_package(package_name, pkg_version)
            if not package_file:
                logger.error(f"Failed to download {package_name}")
                return False
            
            # Extract package
            extract_dir = self.package_manager.extract_package(package_file)
            if not extract_dir:
                logger.error(f"Failed to extract {package_name}")
                return False
            
            downloaded_packages[package_name] = {
                'version': pkg_version,
                'extract_dir': extract_dir,
                'dll_name': NUGET_PACKAGES[package_name]["dll_name"],
                'additional_dlls': NUGET_PACKAGES[package_name].get("additional_dlls", [])
            }
            
            logger.info(f"✅ Downloaded and extracted {package_name} v{pkg_version}")
        
        # PHASE 2: Backup existing DLLs
        logger.info("💾 PHASE 2: Backing up existing DLLs...")
        self.backup_existing_dlls()
        
        # PHASE 3: Delete old DLLs (clear the directory)
        logger.info("🗑️ PHASE 3: Removing old DLLs...")
        if DLL_DIR.exists():
            for dll_file in DLL_DIR.glob("*.dll"):
                if self.dry_run:
                    logger.info(f"[DRY RUN] Would remove: {dll_file}")
                else:
                    logger.info(f"Removing old DLL: {dll_file}")
                    dll_file.unlink()
        
        # PHASE 4: Copy new DLLs
        logger.info("📦 PHASE 4: Installing new DLLs...")
        for package_name, package_info in downloaded_packages.items():
            extract_dir = package_info['extract_dir']
            all_dlls = [package_info['dll_name']] + package_info['additional_dlls']
            
            copied_dlls = []
            total_size = 0
            
            logger.info(f"Installing {len(all_dlls)} DLL(s) from {package_name}...")
            
            for dll_name in all_dlls:
                dll_file = self.package_manager.find_specific_dll(extract_dir, dll_name)
                if not dll_file:
                    logger.error(f"Required DLL {dll_name} not found in {package_name}")
                    return False
                
                # Copy the DLL
                target_file = DLL_DIR / dll_file.name
                
                if self.dry_run:
                    logger.info(f"[DRY RUN] Would install: {dll_file} -> {target_file}")
                    copied_dlls.append(dll_name)
                    total_size += dll_file.stat().st_size
                else:
                    try:
                        DLL_DIR.mkdir(exist_ok=True)
                        shutil.copy2(dll_file, target_file)
                        logger.info(f"✅ Installed: {dll_name} -> {target_file}")
                        copied_dlls.append(dll_name)
                        total_size += dll_file.stat().st_size
                    except Exception as e:
                        logger.error(f"Error installing {dll_file}: {e}")
                        return False
            
            # Record success
            self.updated_packages[package_name] = {
                "version": package_info['version'],
                "dll_name": package_info['dll_name'],
                "additional_dlls": package_info['additional_dlls'],
                "copied_dlls": copied_dlls,
                "total_size": total_size
            }
        
        logger.info(f"✅ Successfully updated all {len(NUGET_PACKAGES)} packages")
        logger.info(f"📦 Installed {len(REQUIRED_DLLS)} DLLs total")
        return True
    
    def verify_dll_directory(self) -> bool:
        """Verify that only the required DLLs are present."""
        if not DLL_DIR.exists():
            logger.error("DLL directory does not exist")
            return False
        
        current_dlls = {f.name for f in DLL_DIR.glob("*.dll")}
        
        # Check if we have exactly the required DLLs
        missing_dlls = REQUIRED_DLLS - current_dlls
        extra_dlls = current_dlls - REQUIRED_DLLS
        
        if missing_dlls:
            logger.error(f"Missing required DLLs: {', '.join(missing_dlls)}")
            return False
        
        if extra_dlls:
            logger.warning(f"Extra DLLs found (will be cleaned up): {', '.join(extra_dlls)}")
        
        if current_dlls == REQUIRED_DLLS:
            logger.info(f"✅ DLL directory contains exactly the {len(REQUIRED_DLLS)} required DLLs")
            return True
        
        return len(missing_dlls) == 0  # Allow extra DLLs, we'll clean them up
    
    def generate_report(self) -> str:
        """Generate a report of the update process."""
        report = ["ADOMO Library Update Report", "=" * 40]
        
        if self.dry_run:
            report.append("DRY RUN MODE - No files were modified")
            report.append("")
        
        report.append(f"Target DLLs: {len(REQUIRED_DLLS)}")
        report.append(f"Packages processed: {len(self.updated_packages)}")
        report.append("")
        
        total_size = 0
        for package_name, info in self.updated_packages.items():
            pkg_size = info.get('total_size', 0)  # Use total_size from new code structure
            size_mb = pkg_size / (1024 * 1024)
            total_size += pkg_size
            report.append(f"✓ {package_name}")
            report.append(f"  Version: {info['version']}")
            report.append(f"  Main DLL: {info['dll_name']}")
            if info.get('additional_dlls'):
                report.append(f"  Additional DLLs: {', '.join(info['additional_dlls'])}")
            if info.get('copied_dlls'):
                report.append(f"  Copied DLLs: {', '.join(info['copied_dlls'])}")
            report.append(f"  Total Size: {size_mb:.1f} MB")
            report.append("")
        
        if total_size > 0:
            total_mb = total_size / (1024 * 1024)
            report.append(f"Total DLL size: {total_mb:.1f} MB")
            report.append("")
        
        if not self.dry_run:
            report.append("Backup location: " + str(BACKUP_DIR))
            report.append("Log file: update_adomo.log")
        
        return "\n".join(report)
    
    def cleanup(self):
        """Clean up temporary files."""
        logger.info("Cleaning up temporary files...")
        try:
            shutil.rmtree(TEMP_DIR)
        except Exception as e:
            logger.warning(f"Error cleaning up temp directory: {e}")

def check_prerequisites():
    """Check if prerequisites are met."""
    logger.info("Checking prerequisites...")
    
    # Check if we're in the right directory
    if not PROJECT_ROOT.exists():
        logger.error("Project root not found. Run this script from the project root.")
        return False
    
    # Check if pytabular directory exists
    if not (PROJECT_ROOT / "pytabular").exists():
        logger.error("pytabular directory not found.")
        return False
    
    # Check internet connection
    try:
        requests.get("https://api.nuget.org", timeout=10)
        logger.info("Internet connection: OK")
    except requests.RequestException:
        logger.error("No internet connection. Cannot download packages.")
        return False
    
    return True

def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Update ADOMO libraries for Linux compatibility"
    )
    parser.add_argument(
        "--version",
        help="Specific version to download (default: latest)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("Starting ADOMO library update for Linux compatibility")
    logger.info(f"Project root: {PROJECT_ROOT}")
    logger.info(f"DLL directory: {DLL_DIR}")
    logger.info(f"Required DLLs: {', '.join(sorted(REQUIRED_DLLS))}")
    
    if args.dry_run:
        logger.info("DRY RUN MODE - No files will be modified")
    
    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)
    
    # Create updater and run update
    updater = AdomoUpdater(dry_run=args.dry_run)
    
    try:
        # Verify current state
        logger.info("Verifying current DLL directory state...")
        updater.verify_dll_directory()
        
        # Run the update
        success = updater.update_all_packages(args.version)
        
        # Verify final state
        if success and not args.dry_run:
            logger.info("Verifying updated DLL directory...")
            final_verification = updater.verify_dll_directory()
            if not final_verification:
                logger.warning("Final verification failed - some DLLs may be missing")
        
        # Generate and display report
        report = updater.generate_report()
        print("\n" + report)
        
        if success:
            logger.info("ADOMO library update completed successfully!")
            print("\n🎉 Update completed successfully!")
            print(f"✅ Successfully updated ALL {len(REQUIRED_DLLS)} required DLLs:")
            for dll in sorted(REQUIRED_DLLS):
                print(f"   - {dll}")
            print("Your PyTabular project is now ready for cross-platform compatibility!")
        else:
            logger.error("ADOMO library update failed!")
            print("\n❌ Update failed!")
            print("Check the log file for details: update_adomo.log")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Update cancelled by user")
        print("\n⚠️  Update cancelled by user")
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
        
    finally:
        updater.cleanup()

if __name__ == "__main__":
    main() 
# PyTabular Scripts

This directory contains utility scripts for maintaining and updating PyTabular.

## ADOMO Linux Migration Script

### `update_adomo_linux.py`

This script migrates PyTabular from Windows-only .NET Framework DLLs to cross-platform .NET 6.0+ NuGet packages, enabling Linux compatibility.

#### What it does:

1. **Downloads** the latest Microsoft Analysis Services NuGet packages:
   - `Microsoft.AnalysisServices.AdomdClient` - ADOMD.NET client library
   - `Microsoft.AnalysisServices.Core` - Core Analysis Services libraries
   - `Microsoft.AnalysisServices` - Analysis Services Management Objects (AMO)
   - `Microsoft.AnalysisServices.Tabular` - Tabular Object Model (TOM)
   - `Microsoft.AnalysisServices.Tabular.Json` - JSON support for TOM

2. **Extracts** cross-platform .NET libraries from the packages

3. **Replaces** Windows-only DLLs in `pytabular/dll/` with cross-platform versions

4. **Backs up** existing DLLs for rollback if needed

#### Usage:

```bash
# Preview what will be updated (recommended first)
python script/update_adomo_linux.py --dry-run

# Update to latest versions
python script/update_adomo_linux.py

# Update to specific version
python script/update_adomo_linux.py --version 19.101.1

# Verbose output
python script/update_adomo_linux.py --verbose

# Help
python script/update_adomo_linux.py --help
```

#### Requirements:

- **Internet connection** - Downloads packages from NuGet
- **Python 3.8+** - Compatible with project requirements
- **requests** library - For HTTP requests to NuGet API

#### Safety Features:

- ✅ **Dry run mode** - Preview changes without modifying files
- ✅ **Automatic backups** - Creates `dll_backup/` directory
- ✅ **Comprehensive logging** - Saves to `update_adomo.log`
- ✅ **Error handling** - Graceful failure with cleanup
- ✅ **Rollback capability** - Restore from backups if needed

#### Output:

The script generates a detailed report showing:
- Package versions downloaded
- Number of DLLs updated
- Backup location
- Success/failure status

#### Example Output:

```
ADOMO Library Update Report
========================================

Packages processed: 5

✓ Microsoft.AnalysisServices.AdomdClient
  Version: 19.101.1
  DLLs: 1

✓ Microsoft.AnalysisServices.Core
  Version: 19.101.1
  DLLs: 1

✓ Microsoft.AnalysisServices
  Version: 19.101.1
  DLLs: 1

✓ Microsoft.AnalysisServices.Tabular
  Version: 19.101.1
  DLLs: 1

✓ Microsoft.AnalysisServices.Tabular.Json
  Version: 19.101.1
  DLLs: 1

Backup location: /home/user/PyTabular/dll_backup
Log file: update_adomo.log

🎉 Update completed successfully!
Your PyTabular project is now ready for Linux compatibility!
```

#### After Running:

1. **Test the updated libraries:**
   ```bash
   make test
   ```

2. **Build the package:**
   ```bash
   make build
   ```

3. **Check that imports work:**
   ```bash
   uv run python -c "import pytabular; print('Success!')"
   ```

4. **Commit the changes:**
   ```bash
   git add pytabular/dll/
   git commit -m "feat: migrate to cross-platform ADOMO libraries"
   ```

#### Troubleshooting:

**Problem**: Package download fails
**Solution**: Check internet connection and try again

**Problem**: Permission denied
**Solution**: Ensure script is executable: `chmod +x script/update_adomo_linux.py`

**Problem**: Import errors after update
**Solution**: Restore from backup and check compatibility

**Problem**: .NET runtime not found
**Solution**: Install .NET 6.0+ runtime on target system

#### Rollback:

If you need to revert to the original Windows DLLs:

```bash
# Restore from backup
cp dll_backup/* pytabular/dll/

# Or use git
git checkout HEAD -- pytabular/dll/
```

#### Integration with Development Workflow:

The script is designed to integrate with the existing uv-based development workflow:

```bash
# Full update and test cycle
python script/update_adomo_linux.py --dry-run  # Preview
python script/update_adomo_linux.py            # Update
make test                                       # Test
make build                                      # Build
```

## Future Scripts

This directory will contain additional maintenance scripts:

- `validate_linux_compatibility.py` - Test Linux compatibility
- `benchmark_performance.py` - Performance testing
- `update_documentation.py` - Auto-generate docs
- `check_dependencies.py` - Dependency analysis

---

For questions or issues, please refer to the main project documentation or create an issue in the GitHub repository. 
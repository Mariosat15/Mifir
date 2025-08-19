"""
Clean up unnecessary files, keeping only what's essential for the MiFIR app.
"""

import os
import glob

def cleanup_files():
    """Remove all unnecessary files."""
    
    # Essential files to KEEP
    essential_files = {
        # Core application files
        'app_mifir_mapper.py',
        'mifir_xml_generator.py', 
        'mifir_fields.py',
        'custom_fields.py',
        'custom_only_xml_generator.py',
        'auto_mapper.py',
        
        # Sample data for testing
        'Sample_MiFIR_Data.csv',
        'Sample_MiFIR_Trading_Data.xlsx',
        
        # Original reference data
        'KD_DATTRA_CY_000030-0-000029_22.xml',
        'Test trades.csv',
        
        # Documentation
        'README.md',
        'requirements.txt',
        'SAMPLE_DATA_README.md',
        'FINAL_SYSTEM_SUMMARY.md',
        
        # Configuration files
        'test_mapping_config.json'  # Keep one sample config
    }
    
    # Get all files in current directory
    all_files = []
    for file in os.listdir('.'):
        if os.path.isfile(file):
            all_files.append(file)
    
    # Files to delete
    files_to_delete = []
    for file in all_files:
        if file not in essential_files:
            files_to_delete.append(file)
    
    print(f"🗑️ CLEANING UP UNNECESSARY FILES")
    print(f"="*50)
    print(f"📋 Total files: {len(all_files)}")
    print(f"✅ Essential files to keep: {len(essential_files)}")
    print(f"🗑️ Files to delete: {len(files_to_delete)}")
    
    # Show what will be kept
    print(f"\n✅ ESSENTIAL FILES TO KEEP:")
    for file in sorted(essential_files):
        if file in all_files:
            print(f"   ✅ {file}")
        else:
            print(f"   ⚠️ {file} (not found)")
    
    # Show what will be deleted
    print(f"\n🗑️ FILES TO DELETE:")
    for file in sorted(files_to_delete):
        print(f"   🗑️ {file}")
    
    # Perform deletion
    deleted_count = 0
    for file in files_to_delete:
        try:
            os.remove(file)
            deleted_count += 1
        except Exception as e:
            print(f"   ❌ Error deleting {file}: {e}")
    
    print(f"\n✅ CLEANUP COMPLETED!")
    print(f"🗑️ Deleted {deleted_count} unnecessary files")
    print(f"✅ Kept {len(essential_files)} essential files")
    
    # Show final file list
    remaining_files = [f for f in os.listdir('.') if os.path.isfile(f)]
    print(f"\n📋 REMAINING FILES ({len(remaining_files)}):")
    for file in sorted(remaining_files):
        print(f"   📄 {file}")
    
    return True

if __name__ == "__main__":
    cleanup_files()

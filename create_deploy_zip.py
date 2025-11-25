#!/usr/bin/env python3
import os
import zipfile
import sys

def create_deploy_zip():
    """Create a deployment zip file preserving directory structure."""
    exclude_dirs = {'.git', '__pycache__', 'venv', '.venv', 'env', '.elasticbeanstalk', '.pytest_cache'}
    exclude_files = {'deploy.zip', 'db.sqlite3', '.DS_Store', 'coverage.xml', '.coverage', '.coveragerc'}
    exclude_extensions = {'.pyc', '.pyo', '.pyd'}
    
    zip_path = 'deploy.zip'
    
    # Remove existing zip
    if os.path.exists(zip_path):
        os.remove(zip_path)
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk('.'):
            # Skip excluded directories (but allow .ebextensions and other needed hidden dirs)
            allowed_hidden = {'.ebextensions', '.platform'}
            dirs[:] = [d for d in dirs if d not in exclude_dirs and (d in allowed_hidden or not d.startswith('.'))]
            
            # Skip excluded root directories
            if any(excluded in root for excluded in exclude_dirs):
                continue
            
            for file in files:
                # Skip excluded files
                if file in exclude_files:
                    continue
                if any(file.endswith(ext) for ext in exclude_extensions):
                    continue
                
                file_path = os.path.join(root, file)
                # Get relative path for zip (remove leading ./)
                arcname = os.path.relpath(file_path, '.')
                zipf.write(file_path, arcname)
                print(f"Added: {arcname}")
    
    print(f"\nCreated {zip_path} successfully!")
    print(f"Size: {os.path.getsize(zip_path) / 1024 / 1024:.2f} MB")

if __name__ == '__main__':
    create_deploy_zip()


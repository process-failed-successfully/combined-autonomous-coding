import os
import zipfile
import tarfile
import shutil
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Union

class ArchiveLabManager:
    """
    Manages archive operations (zip, tar, etc).
    """
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir

    def list_contents(self, archive_path: Union[str, Path]) -> List[Dict[str, Any]]:
        path = Path(archive_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Archive {path} not found.")

        contents = []

        if zipfile.is_zipfile(path):
            with zipfile.ZipFile(path, 'r') as zf:
                for info in zf.infolist():
                    # Handle datetime conversion safely
                    dt = datetime(*info.date_time)

                    contents.append({
                        "name": info.filename,
                        "size": info.file_size,
                        "compressed_size": info.compress_size,
                        "modified": dt.isoformat(),
                        "type": "dir" if info.is_dir() else "file"
                    })
        elif tarfile.is_tarfile(path):
            try:
                with tarfile.open(path, 'r:*') as tf:
                    for member in tf.getmembers():
                        mtype = "file"
                        if member.isdir(): mtype = "dir"
                        elif member.issym(): mtype = "symlink"
                        elif member.islnk(): mtype = "link"

                        contents.append({
                            "name": member.name,
                            "size": member.size,
                            "modified": datetime.fromtimestamp(member.mtime).isoformat(),
                            "type": mtype
                        })
            except tarfile.ReadError:
                 raise ValueError(f"Could not read tar archive: {path}")
        else:
             raise ValueError(f"Unsupported archive format or invalid file: {path}")

        return contents

    def _safe_tar_extract(self, tf: tarfile.TarFile, out_path: Path):
        """
        Safely extract tarfile members avoiding Zip Slip.
        Uses 'data' filter if available (Python 3.12+ or backport).
        Otherwise performs manual validation.
        """
        if hasattr(tarfile, 'data_filter'):
            tf.extractall(out_path, filter='data')
        else:
            # Fallback for older python versions
            # Manual check for Zip Slip
            members = []
            for member in tf.getmembers():
                member_path = (out_path / member.name).resolve()
                if out_path.resolve() not in member_path.parents:
                    raise ValueError(f"Attempted path traversal in tar file: {member.name}")
                members.append(member)
            tf.extractall(out_path, members=members) # nosec B202

    def _safe_zip_extract(self, zf: zipfile.ZipFile, out_path: Path):
        """
        Safely extract zipfile members avoiding Zip Slip.
        """
        for member in zf.namelist():
            member_path = (out_path / member).resolve()
            if out_path.resolve() not in member_path.parents:
                 raise ValueError(f"Attempted path traversal in zip file: {member}")
        zf.extractall(out_path) # nosec

    def extract(self, archive_path: Union[str, Path], dest_dir: Union[str, Path] = None) -> str:
        path = Path(archive_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Archive {path} not found.")

        if dest_dir:
            out = Path(dest_dir).resolve()
        else:
            out = Path.cwd()

        out.mkdir(parents=True, exist_ok=True)

        if zipfile.is_zipfile(path):
             with zipfile.ZipFile(path, 'r') as zf:
                 self._safe_zip_extract(zf, out)
        elif tarfile.is_tarfile(path):
             with tarfile.open(path, 'r:*') as tf:
                 self._safe_tar_extract(tf, out)
        else:
             # Try shutil as fallback (e.g. for other formats registered)
             try:
                 shutil.unpack_archive(str(path), str(out))
             except Exception:
                 raise ValueError(f"Unsupported archive format: {path.suffix}")

        return str(out)

    def create(self, archive_path: Union[str, Path], files: List[Union[str, Path]]) -> str:
        path = Path(archive_path).resolve()

        # Ensure parent exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Determine format from extension if possible
        format = None
        name_lower = path.name.lower()
        if name_lower.endswith('.zip'):
            format = 'zip'
        elif name_lower.endswith('.tar'):
            format = 'tar'
        elif name_lower.endswith('.tar.gz') or name_lower.endswith('.tgz'):
            format = 'gztar'
        elif name_lower.endswith('.tar.bz2') or name_lower.endswith('.tbz'):
            format = 'bztar'
        elif name_lower.endswith('.tar.xz') or name_lower.endswith('.txz'):
            format = 'xztar'

        if format == 'zip':
            with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for f in files:
                    fp = Path(f).resolve()
                    if not fp.exists():
                        print(f"Warning: {fp} not found, skipping.")
                        continue

                    if fp.is_file():
                        zf.write(fp, arcname=fp.name)
                    elif fp.is_dir():
                        for root, dirs, files_in_dir in os.walk(fp):
                            for file in files_in_dir:
                                file_path = Path(root) / file
                                arcname = file_path.relative_to(fp.parent)
                                zf.write(file_path, arcname=arcname)
        elif format in ['tar', 'gztar', 'bztar', 'xztar']:
            mode = 'w'
            if format == 'gztar': mode = 'w:gz'
            elif format == 'bztar': mode = 'w:bz2'
            elif format == 'xztar': mode = 'w:xz'

            with tarfile.open(path, mode) as tf:
                for f in files:
                    fp = Path(f).resolve()
                    if not fp.exists():
                        print(f"Warning: {fp} not found, skipping.")
                        continue

                    arcname = fp.name
                    tf.add(fp, arcname=arcname)
        else:
             raise ValueError("Please specify a valid archive extension (.zip, .tar, .tar.gz, .tgz, .tar.bz2, .tbz, .tar.xz, .txz)")

        return str(path)

    def add(self, archive_path: Union[str, Path], files: List[Union[str, Path]]):
        path = Path(archive_path).resolve()
        if not path.exists():
             raise FileNotFoundError(f"Archive {path} not found.")

        if zipfile.is_zipfile(path):
            with zipfile.ZipFile(path, 'a') as zf:
                for f in files:
                    fp = Path(f).resolve()
                    if not fp.exists():
                        print(f"Warning: {fp} not found, skipping.")
                        continue

                    if fp.is_file():
                        zf.write(fp, arcname=fp.name)
                    elif fp.is_dir():
                         for root, dirs, files_in_dir in os.walk(fp):
                            for file in files_in_dir:
                                file_path = Path(root) / file
                                arcname = file_path.relative_to(fp.parent)
                                zf.write(file_path, arcname=arcname)
        elif tarfile.is_tarfile(path):
            # Check compression
            is_compressed = False
            name_lower = path.name.lower()
            if name_lower.endswith('.gz') or name_lower.endswith('.tgz'): is_compressed = True
            if name_lower.endswith('.bz2') or name_lower.endswith('.tbz'): is_compressed = True
            if name_lower.endswith('.xz') or name_lower.endswith('.txz'): is_compressed = True

            if is_compressed:
                 raise NotImplementedError("Adding to compressed tar archives is not supported. Please recreate the archive.")

            with tarfile.open(path, 'a') as tf:
                for f in files:
                    fp = Path(f).resolve()
                    if not fp.exists():
                        print(f"Warning: {fp} not found, skipping.")
                        continue

                    arcname = fp.name
                    tf.add(fp, arcname=arcname)
        else:
             raise ValueError(f"Unsupported archive format: {path.suffix}")

    def format_bytes(self, size: float) -> str:
        power = 1024
        n = 0
        power_labels = {0: 'B', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
        while size >= power and n < 4:
            size /= power
            n += 1
        return f"{size:.2f} {power_labels[n]}"

def run_archive_lab_logic(args):
    """
    CLI logic for Archive Lab.
    """
    manager = ArchiveLabManager(args.project_dir)

    try:
        if args.action == "list":
            if not args.archive:
                print("Error: Archive path required.")
                sys.exit(1)

            contents = manager.list_contents(args.archive)
            print(f"--- Archive Contents: {args.archive} ---")

            # Simple table
            print(f"{'Size':<10} | {'Type':<4} | {'Modified':<20} | {'Name'}")
            print("-" * 80)
            for item in contents:
                size_str = manager.format_bytes(item['size'])
                mtime = item['modified'][:19].replace("T", " ")
                print(f"{size_str:<10} | {item['type'][:4]:<4} | {mtime:<20} | {item['name']}")

        elif args.action == "extract":
            if not args.archive:
                print("Error: Archive path required.")
                sys.exit(1)

            out = manager.extract(args.archive, args.dest)
            print(f"✅ Extracted to: {out}")

        elif args.action == "create":
            if not args.archive or not args.files:
                print("Error: Archive path and input files required.")
                sys.exit(1)

            out = manager.create(args.archive, args.files)
            print(f"✅ Created archive: {out}")

        elif args.action == "add":
            if not args.archive or not args.files:
                print("Error: Archive path and input files required.")
                sys.exit(1)

            manager.add(args.archive, args.files)
            print(f"✅ Added files to: {args.archive}")

        elif args.action == "info":
            if not args.archive:
                print("Error: Archive path required.")
                sys.exit(1)

            contents = manager.list_contents(args.archive)
            total_size = sum(c['size'] for c in contents)
            file_count = sum(1 for c in contents if c['type'] == 'file')
            dir_count = sum(1 for c in contents if c['type'] == 'dir')

            path = Path(args.archive).resolve()
            archive_size = path.stat().st_size

            print(f"--- Archive Info: {args.archive} ---")
            print(f"Type: {path.suffix}")
            print(f"Size: {manager.format_bytes(archive_size)}")
            print(f"Uncompressed Size: {manager.format_bytes(total_size)}")
            print(f"Files: {file_count}")
            print(f"Directories: {dir_count}")
            if archive_size > 0:
                ratio = (1 - (archive_size / total_size)) * 100 if total_size > 0 else 0
                print(f"Compression Ratio: {ratio:.1f}%")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

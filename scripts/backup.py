"""Offline local metadata/vault backup; preserve graph volume and .env separately."""
import argparse
import sqlite3
import sys
import tempfile
import zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from backend.app.lease import InstanceLease

def backup(source,target):
    source=Path(source).resolve();target=Path(target).resolve()
    if target.exists():raise ValueError('Choose a new backup path; existing backups are never overwritten.')
    if not (source/'metadata.sqlite').exists() or not (source/'key-check').exists():raise ValueError('Source is not a complete MosaicGuard data directory.')
    target.parent.mkdir(parents=True,exist_ok=True)
    with InstanceLease(source),zipfile.ZipFile(target,'x',zipfile.ZIP_DEFLATED) as z:
        # The app is stopped; SQLite backup also absorbs a residual WAL consistently.
        con=sqlite3.connect(source/'metadata.sqlite');mem=sqlite3.connect(':memory:');con.backup(mem)
        z.writestr('metadata.sqlite',mem.serialize());con.close();mem.close()
        for file in [source/'key-check',*(source/'vault').rglob('*.bin')]:
            if file.is_file():z.write(file,str(file.relative_to(source)).replace('\\','/'))
    return target

def restore(archive,target):
    target=Path(target).resolve()
    if target.exists():raise ValueError('Restore target must be new. Existing data is never overwritten.')
    with zipfile.ZipFile(archive) as z:
        for name in z.namelist():
            dest=(target/name).resolve()
            if not dest.is_relative_to(target):raise ValueError('Unsafe archive path rejected.')
        z.extractall(target)
    return target

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['backup','restore']);p.add_argument('source');p.add_argument('target');a=p.parse_args()
    try:print(str(backup(a.source,a.target) if a.mode=='backup' else restore(a.source,a.target)))
    except (ValueError,RuntimeError) as e:raise SystemExit(str(e))

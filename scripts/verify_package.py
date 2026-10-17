"""Independently reopen and verify an exported ZIP without executing any contents."""
import csv,hashlib,io,json,sys,zipfile

def encode(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def sha(v):return hashlib.sha256(v).hexdigest()
def verify(filename):
    with zipfile.ZipFile(filename) as z:
        if sum(i.file_size for i in z.infolist())>100*1024*1024:raise ValueError('Package exceeds verification size bound.')
        manifest=json.loads(z.read('manifest.json'))
        if manifest['format']!='mosaicguard-package-v1':raise ValueError('Unsupported package format.')
        if set(z.namelist())!=set(manifest['files'])|{'manifest.json'}:raise ValueError('Unexpected or missing files.')
        for name,digest in manifest['files'].items():
            if sha(z.read(name))!=digest:raise ValueError('File digest mismatch.')
        for name,policy in manifest['transport'].items():
            rows=list(csv.reader(io.StringIO(z.read(name).decode('utf-8-sig'),newline='')))
            for i,j in policy['prefix_apostrophe_cells']:
                if not rows[i][j].startswith("'"):raise ValueError('Transport prefix missing.')
                rows[i][j]=rows[i][j][1:]
            if sha(encode(rows))!=policy['semantic_sha256']:raise ValueError('Reopened semantic data digest mismatch.')
    return {'verified':True,'files':len(manifest['files']),'audit_id':manifest['audit_id'],'scenario_id':manifest['scenario_id']}

if __name__=='__main__':
    try:print(json.dumps(verify(sys.argv[1])))
    except (ValueError,KeyError,IndexError,zipfile.BadZipFile):raise SystemExit('Package verification failed. No contents were executed or extracted.')

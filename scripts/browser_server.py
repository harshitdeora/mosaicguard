"""Isolated synthetic browser-test installation. Never points at operator data."""
import os
import sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from dotenv import load_dotenv
load_dotenv(root/'.env')
os.environ['MOSAIC_DATA']=str(root/'work'/'browser-tests')
from backend.app.main import app,PH
from backend.app.core import db
with db() as c:
    c.execute('INSERT OR IGNORE INTO owner VALUES(1,?,?)',('browser-owner',PH.hash('Synthetic-browser-password-42')))
if __name__=='__main__':
    import uvicorn
    uvicorn.run(app,host='127.0.0.1',port=8028,access_log=False,log_level='critical')

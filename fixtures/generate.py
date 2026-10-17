"""Fictional data, generated locally. No real people or hidden identity columns."""
import csv
import io
from datetime import date,timedelta

def kit(n=200):
    def csv_text(headers,rows):
        s=io.StringIO(newline='');w=csv.writer(s,lineterminator='\r\n');w.writerow(headers);w.writerows(rows);return s.getvalue()
    rows=[]
    for i in range(n):
        rows.append({'key':f'FICT-{i:05}','dept':['Learning','Operations','Research','Outreach'][i%4],
                     'session':f'S-{i//5:03}','day':str(date(2026,1,1)+timedelta(days=i%300)),
                     'badge':f'B-{i:05}','rating':(i%5)+1})
    return [
      {'name':'feedback.csv','role':'candidate','types':{'survey_day':'date','rating':'number'},'csv':csv_text(['department','session','survey_day','badge','rating'],[[r['dept'],r['session'],r['day'],r['badge'],r['rating']] for r in rows])},
      {'name':'attendance.csv','role':'available','types':{},'csv':csv_text(['session','participant_key'],[[r['session'],r['key']] for r in rows])},
      {'name':'directory.csv','role':'reference','types':{},'csv':csv_text(['participant_key','department'],[[r['key'],r['dept']] for r in rows])},
      {'name':'badges.csv','role':'available','types':{},'csv':csv_text(['badge','participant_key'],[[r['badge'],r['key']] for r in rows])},
      {'name':'calendar.csv','role':'available','types':{'survey_day':'date'},'csv':csv_text(['survey_day','participant_key'],[[r['day'],r['key']] for r in rows])},
    ]

if __name__=='__main__':
    from pathlib import Path
    for f in kit():Path(__file__).with_name(f['name']).write_text(f['csv'],encoding='utf-8',newline='')

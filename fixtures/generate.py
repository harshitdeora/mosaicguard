"""Fictional data, generated locally. No real people or hidden identity columns."""
import csv
import io
from datetime import date,timedelta

def csv_text(headers,rows):
    s=io.StringIO(newline='');w=csv.writer(s,lineterminator='\r\n');w.writerow(headers);w.writerows(rows);return s.getvalue()

def beginner_kit():
    """Two tiny files for learning the product without the five-file demo."""
    return [
      {
        'name':'anonymous_feedback.csv',
        'role':'candidate',
        'types':{'satisfaction':'number'},
        'identifiers':[],
        'sensitive':['feedback_topic'],
        'meanings':{
          'event_code':'Workshop attended by the respondent',
          'age_group':'Respondent age band',
          'city':'Respondent city',
          'satisfaction':'Satisfaction score from 1 to 5',
          'feedback_topic':'Main subject of the response',
        },
        'csv':csv_text(
          ['event_code','age_group','city','satisfaction','feedback_topic'],
          [
            ['EVT-100','18-29','Pune',5,'Course pace'],
            ['EVT-100','30-39','Pune',4,'Materials'],
            ['EVT-200','18-29','Mumbai',3,'Timing'],
            ['EVT-300','40-49','Delhi',5,'Mentoring'],
            ['EVT-300','30-39','Delhi',4,'Course pace'],
            ['EVT-400','18-29','Bengaluru',2,'Location'],
          ],
        ),
      },
      {
        'name':'workshop_registration.csv',
        'role':'reference',
        'types':{},
        'identifiers':['member_id','member_name'],
        'sensitive':[],
        'meanings':{
          'event_code':'Workshop registration code',
          'member_id':'Unique fictional member identifier',
          'member_name':'Fictional member name',
          'city':'Registered member city',
        },
        'csv':csv_text(
          ['event_code','member_id','member_name','city'],
          [
            ['EVT-100','M001','Asha Rao','Pune'],
            ['EVT-100','M002','Rohan Mehta','Pune'],
            ['EVT-200','M003','Nila Shah','Mumbai'],
            ['EVT-300','M004','Kabir Singh','Delhi'],
            ['EVT-300','M005','Maya Iyer','Delhi'],
            ['EVT-300','M006','Dev Patel','Delhi'],
            ['EVT-400','M007','Tara Nair','Bengaluru'],
          ],
        ),
      },
    ]

def kit(n=200):
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

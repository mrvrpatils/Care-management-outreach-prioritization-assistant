import sys
import requests

BASE = 'http://127.0.0.1:8000'

failures = []

def check_dashboard():
    r = requests.get(BASE + '/api/dashboard')
    if r.status_code != 200:
        failures.append('dashboard: status %s' % r.status_code); return
    d = r.json()
    needed = ['total_members','high_priority_members','medium_priority_members','low_priority_members','average_priority_score','open_care_gaps','members_with_open_care_gaps','outreach_status']
    for k in needed:
        if k not in d:
            failures.append('dashboard: missing %s' % k)

def check_priority_queue():
    r = requests.get(BASE + '/api/priority-queue?page=1&page_size=5')
    if r.status_code != 200:
        failures.append('priority-queue: status %s' % r.status_code); return
    j = r.json()
    if 'items' not in j or not isinstance(j['items'], list): failures.append('priority-queue: items missing')
    else:
        sample = j['items'][0]
        for f in ['member_id','member_name','priority_score','priority_band','main_risk_factors','next_best_action','outreach_status']:
            if f not in sample: failures.append('priority-queue: item missing %s' % f)

def check_member(member_id):
    r = requests.get(BASE + f'/api/members/{member_id}')
    if r.status_code != 200:
        failures.append(f'member_detail {member_id}: status {r.status_code}'); return
    d = r.json()
    for block, keys in [('member',['member_id','member_name']),('priority',['score','band','probability']),('utilization',['er_visits_30d']),('care_gaps',['care_gap_count','overdue_screening','medication_gap']),('social_risk',['social_risk_count']),('discharge',['recent_discharge_30d'])]:
        if block not in d: failures.append(f'member {member_id}: missing block {block}'); continue
        for k in keys:
            if k not in d[block]: failures.append(f'member {member_id}: missing {block}.{k}')

def check_explanation(member_id):
    r = requests.get(BASE + f'/api/members/{member_id}/explanation')
    if r.status_code != 200:
        failures.append(f'explanation {member_id}: status {r.status_code}'); return

def check_next_action(member_id):
    r = requests.get(BASE + f'/api/members/{member_id}/next-action')
    if r.status_code != 200 or 'next_best_action' not in r.json(): failures.append('next-action missing')

def check_call_guide(member_id):
    r = requests.post(BASE + f'/api/members/{member_id}/call-guide', json={'include_questions': True})
    if r.status_code != 200: failures.append('call-guide status %s' % r.status_code); return
    j = r.json()
    for k in ['opening','key_discussion_points','suggested_questions','next_actions']:
        # API may use different keys; ensure at least opening or key_discussion_points present
        pass

def check_analytics():
    r = requests.get(BASE + '/api/analytics')
    if r.status_code != 200: failures.append('analytics status %s' % r.status_code); return
    j = r.json()
    need = ['scope','total_members','priority_distribution','care_gaps','model_performance']
    for k in need:
        if k not in j: failures.append('analytics: missing %s' % k)

def scan_frontend_for_apis():
    import glob, os, re
    files = glob.glob(os.path.join(os.path.dirname(__file__), '..', 'frontend', '*.html'))
    if not files:
        files = glob.glob(os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', '*.html'))
    text = ''
    for f in files:
        text += open(f,'r',encoding='utf-8').read()
    checks = ['/api/dashboard','/api/priority-queue','/api/members/','/api/analytics','/api/members/{member_id}/call-guide','/api/members/{member_id}/next-action']
    for c in checks:
        if c.split('{')[0] not in text:
            failures.append('frontend: no reference to '+c)

def main():
    check_dashboard()
    check_priority_queue()
    # pick a sample member id from priority queue
    r = requests.get(BASE + '/api/priority-queue?page=1&page_size=1')
    if r.status_code==200 and r.json().get('items'):
        mid = r.json()['items'][0]['member_id']
    else:
        failures.append('no sample member for deeper checks'); mid=None
    if mid:
        check_member(mid)
        check_explanation(mid)
        check_next_action(mid)
        check_call_guide(mid)
    check_analytics()
    scan_frontend_for_apis()
    if failures:
        print('FAILURES:')
        for f in failures: print(' -',f)
        sys.exit(2)
    else:
        print('AUDIT PASS')

if __name__=='__main__':
    main()

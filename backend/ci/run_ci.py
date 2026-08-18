#!/usr/bin/env python3
"""CI-ready test runner for CareWise AI backend.

Usage: run from `backend/` directory or execute directly. The script will:
- ensure a Python virtualenv at `.venv` (create if absent)
- install `requirements.txt` into the venv (only if venv was created)
- run `pytest`
- start the FastAPI app (if not already running) on http://127.0.0.1:8000
- verify main API endpoints
- run a lightweight frontend/headless smoke test (HTTP GETs & content checks)
- print a clear summary and exit non-zero on failures

Notes:
- This script avoids changing application functionality or UI.
- Tailwind CDN and third-party deprecation warnings are treated as non-blocking.
"""
import os
import sys
import subprocess
import time
import requests
import socket

ROOT = os.path.dirname(os.path.dirname(__file__))
VENV_DIR = os.path.join(ROOT, '.venv')
REQUIREMENTS = os.path.join(ROOT, 'requirements.txt')

def python_in_venv():
    if os.name == 'nt':
        return os.path.join(VENV_DIR, 'Scripts', 'python.exe')
    return os.path.join(VENV_DIR, 'bin', 'python')

def ensure_venv():
    python = None
    created = False
    if os.path.exists(VENV_DIR):
        python = python_in_venv()
        if not os.path.exists(python):
            python = sys.executable
    else:
        print('Creating virtualenv at .venv')
        subprocess.check_call([sys.executable, '-m', 'venv', VENV_DIR])
        python = python_in_venv()
        created = True
    return python, created

def pip_install(python):
    if not os.path.exists(REQUIREMENTS):
        print('No requirements.txt found, skipping pip install')
        return
    print('Installing requirements (may take a moment)')
    subprocess.check_call([python, '-m', 'pip', 'install', '--upgrade', 'pip'])
    subprocess.check_call([python, '-m', 'pip', 'install', '-r', REQUIREMENTS])

def run_pytest(python):
    print('Running pytest')
    p = subprocess.run([python, '-m', 'pytest', '-q'], cwd=ROOT)
    return p.returncode == 0

def is_port_in_use(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.settimeout(0.5)
            s.connect((host, port))
            return True
        except Exception:
            return False

def start_uvicorn(python):
    cmd = [python, '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000']
    # Start subprocess and return Popen
    print('Starting uvicorn...')
    p = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # wait for it to bind
    for _ in range(30):
        if is_port_in_use('127.0.0.1', 8000):
            time.sleep(0.5)
            return p
        time.sleep(0.5)
    # timeout
    p.terminate()
    raise RuntimeError('uvicorn failed to start')

def stop_process(p):
    try:
        p.terminate()
        p.wait(timeout=5)
    except Exception:
        try:
            p.kill()
        except Exception:
            pass

def verify_apis():
    failures = []
    BASE = 'http://127.0.0.1:8000'
    endpoints = [
        ('GET', '/api/dashboard'),
        ('GET', '/api/priority-queue?page=1&page_size=5'),
        ('GET', '/api/analytics'),
    ]
    for method, path in endpoints:
        try:
            r = requests.request(method, BASE + path, timeout=5)
            if r.status_code != 200:
                failures.append(f'{path} -> status {r.status_code}')
        except Exception as e:
            failures.append(f'{path} -> exception {e}')

    # try to get a sample member id
    member_id = None
    try:
        r = requests.get(BASE + '/api/priority-queue?page=1&page_size=1', timeout=5)
        if r.ok:
            j = r.json()
            items = j.get('items') or []
            if items:
                member_id = items[0].get('member_id')
    except Exception:
        pass
    if not member_id:
        member_id = 'M00001'

    # member detail
    try:
        r = requests.get(BASE + f'/api/members/{member_id}', timeout=5)
        if r.status_code != 200:
            failures.append(f'/api/members/{member_id} -> status {r.status_code}')
    except Exception as e:
        failures.append(f'/api/members/{member_id} -> exception {e}')

    # call guide POST
    try:
        r = requests.post(BASE + f'/api/members/{member_id}/call-guide', json={'include_questions': True}, timeout=10)
        if r.status_code != 200:
            failures.append(f'POST /api/members/{member_id}/call-guide -> status {r.status_code}')
    except Exception as e:
        failures.append(f'POST /api/members/{member_id}/call-guide -> exception {e}')

    return failures, member_id

def frontend_smoke(member_id):
    failures = []
    BASE = 'http://127.0.0.1:8000'
    pages = [
        ('/', 'Dashboard'),
        ('/outreach', 'Outreach Queue'),
        (f'/member?id={member_id}', 'Member Profile'),
        ('/analytics', 'Analytics'),
        (f'/call-guide?id={member_id}', 'AI Call Guide'),
    ]
    for path, expect in pages:
        try:
            r = requests.get(BASE + path, timeout=5)
            if r.status_code != 200:
                failures.append(f'{path} -> status {r.status_code}')
            else:
                if expect not in r.text and expect.lower() not in r.text.lower():
                    failures.append(f'{path} -> missing text "{expect}"')
        except Exception as e:
            failures.append(f'{path} -> exception {e}')
    return failures

def main():
    os.chdir(ROOT)
    python, created = ensure_venv()
    if not python or not os.path.exists(python):
        print('Failed to locate python in venv or system; aborting')
        sys.exit(2)
    if created:
        pip_install(python)

    # run pytest
    ok = run_pytest(python)
    if not ok:
        print('\nCI RESULT: pytest failed')
        sys.exit(2)

    server_started = False
    uvicorn_proc = None
    try:
        if not is_port_in_use('127.0.0.1', 8000):
            uvicorn_proc = start_uvicorn(python)
            server_started = True
        else:
            print('Detected existing server on port 8000; using it')

        api_failures, member_id = verify_apis()
        smoke_failures = frontend_smoke(member_id)

        failures = api_failures + smoke_failures
        if failures:
            print('\nCI RESULT: FAIL')
            for f in failures:
                print(' -', f)
            sys.exit(3)
        else:
            print('\nCI RESULT: PASS')
            sys.exit(0)
    finally:
        if server_started and uvicorn_proc:
            print('Stopping uvicorn')
            stop_process(uvicorn_proc)

if __name__ == '__main__':
    main()

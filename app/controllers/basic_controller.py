"""Flask controller layer.

MVC mapping: SCNEDT/GIOKYB handled keyboard editing in the original binary. In a
web deployment HTTP receives the line and delegates it to the interpreter model.
"""
from __future__ import annotations
import os, threading, uuid
from flask import Blueprint, jsonify, render_template, request, session
from app.services.interpreter import GWBasicInterpreter

bp=Blueprint('basic',__name__)
_lock=threading.RLock()
_sessions: dict[str,GWBasicInterpreter]={}


def engine() -> GWBasicInterpreter:
    sid=session.get('basic_sid')
    if not sid:
        sid=uuid.uuid4().hex; session['basic_sid']=sid
    with _lock:
        if sid not in _sessions:
            _sessions[sid]=GWBasicInterpreter(
                data_dir=os.getenv('BASIC_DATA_DIR','data'),
                max_steps=int(os.getenv('BASIC_MAX_STEPS','100000'))
            )
        return _sessions[sid]


@bp.get('/')
def index():
    return render_template('index.html')


@bp.post('/api/execute')
def execute():
    payload=request.get_json(silent=True) or {}
    command=str(payload.get('command',''))
    return jsonify(engine().submit(command))


@bp.get('/api/state')
def state():
    e=engine()
    return jsonify({
        'screen': e.state.screen.text(),
        'variables': e.state.variables,
        'program': [{'line':n,'source':e.state.program[n]} for n in sorted(e.state.program)],
        'graphics': e.state.graphics_commands[-500:],
        'waiting_input': e.state.pending_input is not None,
    })


@bp.post('/api/reset')
def reset():
    e=engine(); e.state.reset_runtime(preserve_program=False)
    return jsonify({'status':'ok'})

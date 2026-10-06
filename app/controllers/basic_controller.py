"""Flask controller layer.

MVC mapping: SCNEDT/GIOKYB handled keyboard editing in the original binary. In a
web deployment HTTP receives the line and delegates it to the interpreter model.
"""
from __future__ import annotations
from pathlib import Path
import os, threading, uuid
from flask import Blueprint, jsonify, render_template, request, session, send_file
from werkzeug.utils import secure_filename
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


@bp.post('/api/cassette/upload')
def cassette_upload():
    """Mount a WAV/MP3 capture as the session's CAS1: device."""
    upload=request.files.get('cassette')
    if upload is None or not upload.filename:
        return jsonify({'status':'error','error':'No cassette audio supplied'}),400
    name=secure_filename(upload.filename)
    suffix=Path(name).suffix.lower()
    if suffix not in ('.wav','.mp3'):
        return jsonify({'status':'error','error':'Cassette must be WAV or MP3'}),400
    sid=session.get('basic_sid') or uuid.uuid4().hex
    session['basic_sid']=sid
    root=Path(os.getenv('BASIC_DATA_DIR','data')).resolve()/'cassettes'
    root.mkdir(parents=True,exist_ok=True)
    path=(root/f'{sid}_{name}').resolve()
    upload.save(path)
    e=engine(); e.mount_cassette(path)
    try:
        from app.services import cassette
        files=cassette.scan_audio(path)
        listing=[{'name':f.name,'type':f.type_letter,'type_code':f.file_type,
                  'bytes':len(f.payload),'crc_ok':f.crc_ok,
                  'segment':f.segment,'offset':f.offset} for f in files]
        return jsonify({'status':'ok','mounted':path.name,'files':listing})
    except Exception as exc:
        # Keep the mount: a marginal analog recording may still be useful after
        # improving decoder parameters, but report that automatic indexing failed.
        return jsonify({'status':'mounted_with_error','mounted':path.name,'error':str(exc),'files':[]})


@bp.get('/api/cassette/status')
def cassette_status():
    e=engine(); path=e.cassette_path
    payload={'mounted':path.name,'exists':path.exists(),'format':path.suffix.lower().lstrip('.')}
    if path.exists():
        try:
            from app.services import cassette
            payload['files']=[{'name':f.name,'type':f.type_letter,'type_code':f.file_type,
                               'bytes':len(f.payload),'crc_ok':f.crc_ok,
                               'segment':f.segment,'offset':f.offset}
                              for f in cassette.scan_audio(path)]
        except Exception as exc:
            payload['error']=str(exc); payload['files']=[]
    return jsonify(payload)


@bp.get('/api/cassette/download')
def cassette_download():
    path=engine().cassette_path
    if not path.exists():
        return jsonify({'status':'error','error':'No cassette image is mounted'}),404
    return send_file(path,as_attachment=True,download_name=path.name)

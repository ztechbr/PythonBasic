from __future__ import annotations
import os


def create_app():
    # Lazy import keeps the interpreter core usable in academic/unit-test contexts
    # even before Flask dependencies are installed.
    from flask import Flask
    app=Flask(__name__)
    app.secret_key=os.getenv('SECRET_KEY','development-only-change-me')
    app.config['MAX_CONTENT_LENGTH']=int(os.getenv('MAX_CASSETTE_UPLOAD_BYTES', str(128*1024*1024)))
    from app.controllers import bp
    app.register_blueprint(bp)
    return app

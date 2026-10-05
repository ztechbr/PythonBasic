from __future__ import annotations
import os


def create_app():
    # Lazy import keeps the interpreter core usable in academic/unit-test contexts
    # even before Flask dependencies are installed.
    from flask import Flask
    app=Flask(__name__)
    app.secret_key=os.getenv('SECRET_KEY','development-only-change-me')
    from app.controllers import bp
    app.register_blueprint(bp)
    return app

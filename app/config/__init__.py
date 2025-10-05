"""
Configuration initialization for the Flask app
"""
from flask import Flask
from app.config.settings import config

def create_app(config_name='default'):
    """Application factory pattern"""
    import os
    
    # Get the project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    app = Flask(
        __name__,
        template_folder=os.path.join(project_root, 'templates'),
        static_folder=os.path.join(project_root, 'static'),
        static_url_path='/static'
    )
    app.config.from_object(config[config_name])
    
    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.api import api_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    return app

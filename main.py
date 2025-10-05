"""
Main application entry point
"""
from app.config import create_app

app = create_app()

if __name__ == "__main__":
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        threaded=app.config['THREADED'],
        debug=app.config['DEBUG']
    )

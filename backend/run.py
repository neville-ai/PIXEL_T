import os
import sys

# Ensure current directory is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

app = create_app()

if __name__ == '__main__':
    host = app.config.get('BACKEND_HOST', '127.0.0.1')
    port = app.config.get('BACKEND_PORT', 5000)
    debug = app.config.get('DEBUG', False)
    app.run(host=host, port=port, debug=debug)

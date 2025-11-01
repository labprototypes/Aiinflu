"""Run Flask development server."""
from app import create_app, db

app = create_app()


@app.shell_context_processor
def make_shell_context():
    """Add database models to shell context."""
    from app.models import Blogger, Project
    return {'db': db, 'Blogger': Blogger, 'Project': Project}


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

"""Project API endpoints (placeholder for future)."""
from flask import jsonify
from app.api import bp
from app.models import Project


@bp.route('/projects', methods=['GET'])
def get_projects():
    """Get all projects."""
    projects = Project.query.order_by(Project.updated_at.desc()).all()
    return jsonify([project.to_dict() for project in projects])


@bp.route('/projects/<project_id>', methods=['GET'])
def get_project(project_id):
    """Get single project by ID."""
    project = Project.query.get_or_404(project_id)
    return jsonify(project.to_dict())


# More endpoints will be added in future commits

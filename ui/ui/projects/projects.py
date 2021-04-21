"""Blueprint for the projects module."""
import logging
import os
import tempfile
from typing import Any, Dict

from flask import (
    Blueprint,
    Config,
    abort,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)

from ui.projects.api import Client
from ui.projects.model import Job, Project

logger = logging.getLogger(__name__)
logger.level = logging.DEBUG

root_folder = "~/Downloads"


def construct_projects_bp(cfg: Config):
    """Create constructor from function to pass in config."""
    projects_bp = Blueprint(
        "projects_bp",
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    endpoint_path: str = cfg["BACKEND_URL"]
    client = Client(endpoint_path)

    def check_api_connection():
        if not client.check_api():
            return render_template("api_down.html"), 502

    projects_bp.before_request(check_api_connection)

    @projects_bp.route("/")
    def projects_index():
        """Entrypoint for the blueprint."""
        projects = client.get_projects()
        return render_template("projects/projects.html", projects=projects)

    @projects_bp.route("/new", methods=["POST", "GET"])
    def projects_project_new():
        """Create a new project."""
        if request.method == "POST":
            project = Project(
                **{
                    "name": request.form["project_name"],
                    "number": request.form["project_id"],
                    "description": request.form["project_desc"],
                    "location": request.form["project_location"],
                }
            )

            client.post_project(project)

            return redirect(url_for("projects_bp.projects_index"))

        return render_template("projects/project_new.html")

    @projects_bp.route("/<int:project_id>")
    def projects_project(project_id: int):
        """View a single project."""
        project = client.get_project(project_id)
        jobs = client.get_jobs(project_id)
        if project is None:
            return render_template("404.html"), 404

        return render_template(
            "projects/project.html", project=project, jobs=jobs
        )

    @projects_bp.route("/<int:project_id>/jobs/<int:job_id>")
    def projects_job(project_id: int, job_id: int):
        """View a single job."""
        job = client.get_job(project_id, job_id)
        if job is None:
            return render_template("404.html"), 404

        obj_stats = job.get_object_stats()

        return render_template(
            "projects/job.html", job=job, obj_stats=obj_stats
        )

    @projects_bp.route(
        "/<int:project_id>/jobs/<int:job_id>/toggle", methods=["PUT"]
    )
    def projects_job_toggle(project_id: int, job_id: int):
        """Toogle job status."""
        old_status, new_status = client.change_job_status(project_id, job_id)

        if old_status is None or new_status is None:
            return "404"

        return jsonify(old_status=old_status, new_status=new_status), 201

    @projects_bp.route("/<int:project_id>/jobs/new", methods=["POST", "GET"])
    def projects_job_new(project_id: int):
        """Create new job inside a project."""
        project = client.get_project(project_id)

        if request.method == "POST":
            if len(request.form["tree_data"]) <= 0:
                return render_template(
                    "projects/job_new.html",
                    project_name=project.get_name(),
                    form_data=request.form,
                )

            hardcoded_path = os.path.dirname(os.path.expanduser(root_folder))
            videos = [
                hardcoded_path + "/" + path[1:-1]
                for path in request.form["tree_data"][1:-1].split(",")
            ]
            videos = [
                path if not os.path.isdir(path) else f"Folder is empty: {path}"
                for path in videos
            ]

            job = Job(
                **{
                    "name": request.form["job_name"],
                    "description": request.form["job_description"],
                    "_status": "Pending",
                    "videos": videos,
                    "location": request.form["job_location"],
                    "_objects": list(),
                }
            )

            result = client.post_job(project_id, job)

            if not isinstance(result, int):
                return render_template(
                    "projects/job_new.html",
                    project_name=project.get_name(),
                    file_errors=result,
                    form_data=request.form,
                )

            return redirect(
                url_for(
                    "projects_bp.projects_job",
                    project_id=project_id,
                    job_id=result,
                )
            )

        return render_template(
            "projects/job_new.html", project_name=project.get_name()
        )

    @projects_bp.route("/json")
    def projects_json() -> Dict:
        """Create new job inside a project."""
        data: Dict[str, Any] = path_to_dict(os.path.expanduser(root_folder))

        return data

    @projects_bp.route("/<int:project_id>/jobs/<int:job_id>/csv")
    def projects_job_make_csv(project_id: int, job_id: int):
        """Download results of a job as a csv-file."""
        job = client.get_job(job_id, project_id)
        if job is None:
            return render_template("404.html"), 404

        obj_stats = job.get_object_stats()

        if not isinstance(job, Job):
            print("nei")

        # PoC of download file
        with tempfile.NamedTemporaryFile(suffix=".csv") as csv_file:

            # write headers to file
            csv_file.write(b"id,label,time_in,time_out,probability\n")

            for idx, obj in enumerate(job._objects):
                csv_file.write(
                    str.encode(
                        f"{idx},{obj.label},{obj.time_in},{obj.time_out},{obj.probability}\n"
                    )
                )

            csv_file.seek(0)

            return send_file(
                csv_file.name,
                as_attachment=True,
                mimetype="text/plain",
                attachment_filename=f"report_p{project_id}_j{job_id}.csv",
            )

    return projects_bp


def path_to_dict(path: str) -> Dict[str, Any]:
    """Polute endpoint with stuff."""
    d: Dict[str, Any] = {"text": os.path.basename(path)}
    if os.path.isdir(path):
        d["children"] = [
            path_to_dict(os.path.join(path, x)) for x in os.listdir(path)
        ]
    else:
        d["icon"] = "jstree-file"

    return d

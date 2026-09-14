# Hosting ExpertCook

For a small academic demonstration with an editable knowledge base, the recommended setup is one Railway service built from the repository's Dockerfile, one persistent volume and an administrator token for rule edits. This keeps the Python app and browser frontend together and avoids adding a database before one is needed.

The recommendation is specific to this project's small, file-backed design. Railway supports Dockerfile builds and persistent volumes. Its Hobby subscription is currently $5 per month, credited toward resource usage; usage above the included amount costs extra. Check the current price before subscribing. Sources checked on 14 September 2026: [Railway Dockerfiles](https://docs.railway.com/builds/dockerfiles), [volumes](https://docs.railway.com/volumes), and [pricing](https://docs.railway.com/pricing).

Render is a reasonable alternative with a paid web service and persistent disk. Its free web service sleeps after 15 minutes without inbound traffic and cannot attach a persistent disk, making it less suitable for a dependable demonstration with browser-edited rules. A free deployment can still demonstrate a read-only, repository-backed configuration. Sources: [Render free services](https://render.com/docs/free) and [persistent disks](https://render.com/docs/disks).

## What Docker does

Docker packages Python 3.12, the pinned application dependencies and the source code into an image. A running copy is a container. The same image can run locally or on the host, reducing differences in installation and startup. Docker does not decide which cooking rules fire; Experta does that inside the Python application.

The container filesystem can be replaced during deployment. The volume holds `/data/proportions.json` outside that replaceable filesystem. A backup is still needed because persistent storage does not protect against an administrator saving an incorrect but valid recipe or deleting the volume.

## Run locally with Docker

From the repository root, with Docker running:

```bash
docker compose up --build -d
docker compose ps
docker compose logs --tail=50 web
```

Open `http://localhost:8000`. The Compose port is bound to localhost. Rule viewing and guide generation work immediately; saves require an administrator token.

To enable authorized rule editing, create a strong random token in a password manager and set it in a local `.env` file as `RULES_ADMIN_TOKEN=your-token`. This file is ignored by Git. Recreate the service with `docker compose up -d`, then enter the token into the administrator field in the rule editor. Keep it out of screenshots, chapter evidence and source control.

Alternatively, `python scripts/configure_admin.py` creates a random token in a new `.env` file with owner-only permissions, without printing it. It preserves existing files. With explicit `--project`, `--environment` and `--service` arguments, it copies that token to the selected Railway service through standard input and defers deployment until the configuration is complete. Open `.env` locally to retrieve the token for the editor; it is not your Railway account credential.

Stop the containers with `docker compose down`. This preserves the named rules volume. Do not add `--volumes` unless you intentionally want to erase that saved configuration.

## Deploy on Railway

1. Commit and push the reviewed changes to the intended GitHub branch. The work was implemented on `proportions`; choose that branch in Railway if it has not been merged into `main`.
2. Create a Railway project and select the repository as a service source. The root Dockerfile and `railway.json` define the build and health check. Use the repository root as the service root.
3. Attach a volume to this service at `/data` before enabling rule editing.
4. Set `PROPORTIONS_PATH=/data/proportions.json`. Set a strong secret `RULES_ADMIN_TOKEN`. Leave `ALLOW_RULE_EDITS` unset and `DEBUG` unset. Railway supplies `PORT`; Gunicorn reads it.
5. Keep one replica and disable optional application sleeping for a predictable presentation. The file-backed configuration is intended for a single service instance. `railway.json` requests one replica; the volume and secrets must be configured in Railway.
6. Deploy, inspect build/runtime logs and wait for that deployment to report success. The configured health check is `/healthz`. The first startup seeds the empty volume from the bundled JSON.
7. Generate a public domain from the service's networking settings. Use HTTPS when entering the administrator token. Open the domain and generate both dishes.
8. Download a guide and audit, then run the HTTP checks below against the deployed URL. Record the deployment ID, URL, date and committed source revision for the academic chapter.

The Dockerfile starts `gunicorn --config gunicorn.conf.py server:app`. Gunicorn binds to `0.0.0.0:$PORT` with one worker and one thread. The static frontend is served by Flask, so a separate frontend host is unnecessary. See [Flask's Gunicorn deployment guidance](https://flask.palletsprojects.com/en/stable/deploying/gunicorn/).

No Railway account or cloud resource is provisioned by these instructions alone. The local deployment files do not constitute evidence that a public deployment has succeeded.

## Verify before a demonstration

In a Python environment with the requirements installed:

```bash
python -m pip check
python verify.py --output docs/evidence
python smoke_web.py https://YOUR-SERVICE.up.railway.app
```

The HTTP checks generate guides but do not save rules. Test editing and persistence deliberately: save a controlled, documented change through the authenticated editor; restart or redeploy the service; verify that the same configuration hash remains; then restore the intended recipe. Capture this as a deployment experiment separately from local regression results.

For a native local installation without Docker:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip check
.venv/bin/gunicorn --config gunicorn.conf.py server:app
```

On Windows, use the Docker workflow for the Gunicorn deployment environment. The existing CLI and Tkinter interfaces remain available through the Python environment; Tkinter also needs the operating system's Tk support.

## Retention and rollback

Download the current configuration before substantial rule edits. Enable volume backups using the host's available backup settings. Keep the Git revision, requirements file, guide exports and verification report together for each academic evaluation run.

A code rollback and a knowledge rollback are separate operations. Reverting a deployment does not automatically replace the volume's edited proportions. Restore the intended configuration through an authorized save, then verify `/healthz` and its configuration hash. When changing the schema or the required ingredient set, validate the existing volume contents against the new code before release.

This version returns audit evidence to the client but does not maintain a server-side archive of every request or a named-user history of administrative edits. If the project grows to multiple users editing concurrently or multiple service replicas, move the knowledge versions and retained run records into a shared database and introduce account-based access control.

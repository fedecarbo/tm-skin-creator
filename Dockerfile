# The viewer and gallery in a container, for machines other than the Windows PC.
# Installing skins into the game stays on the Windows PC. See docker/serve.py.
FROM python:3.14-slim

# Only what the viewer needs, at the versions pinned in requirements.txt. Playwright is there
# because tool/skin.py imports tool/snap.py. No browser is downloaded: the Mac's own Chrome takes
# the snapshots (docker/snap.mjs) and tool.snap makes the sheets here.
COPY requirements.txt /tmp/requirements.txt
RUN grep -E '^(numpy|pillow|scipy|playwright|greenlet|pyee|typing_extensions)==' /tmp/requirements.txt > /tmp/viewer.txt \
 && pip install --no-cache-dir -r /tmp/viewer.txt

# git: the skins' page orders skins by the commit that added each one (tool/gallery.py).
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

# tool/paths.py puts the work folder under LOCALAPPDATA, a Windows variable.
ENV LOCALAPPDATA=/data PYTHONPATH=/app PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
EXPOSE 8765
CMD ["python", "docker/serve.py"]

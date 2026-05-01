from pathlib import Path


def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)


def save_upload(file_obj, dest_path):
    with open(dest_path, "wb") as handle:
        for chunk in file_obj.chunks():
            handle.write(chunk)

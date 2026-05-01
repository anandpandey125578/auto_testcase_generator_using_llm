import logging
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect, render

from services.csv_service import CSV_COLUMNS, parse_csv, parse_uploaded_csv, rows_to_csv
from services.extraction_service import extract_text
from services.llm_service import generate_code_from_csv, generate_testcases, test_connection
from utils.file_handler import ensure_dir, save_upload
from utils.validators import is_image, is_pdf

logger = logging.getLogger(__name__)


def home(request):
    context = {
        "selected_model": request.session.get("openai_model", "gpt-4o-mini"),
        "integration_status": request.session.pop("integration_status", ""),
        "integration_error": request.session.pop("integration_error", ""),
    }

    if request.method == "POST":
        action = request.POST.get("action", "upload")
        pdf_file = request.FILES.get("pdf_file")
        image_files = request.FILES.getlist("image_files")
        api_key = request.POST.get("api_key", "").strip()
        model_name = request.POST.get("model_name", "gpt-4o-mini").strip()

        if action == "test_integration":
            logger.info("Integration test requested")
            if api_key:
                request.session["api_key"] = api_key
            if model_name:
                request.session["openai_model"] = model_name
            try:
                test_connection(api_key, model_name)
                request.session["integration_status"] = "Integration confirmed."
                logger.info("Integration test succeeded (model=%s)", model_name)
            except Exception as exc:  # noqa: BLE001
                request.session["integration_error"] = str(exc)
                logger.warning("Integration test failed: %s", exc)
            return redirect("home")

        errors = []
        session_api_key = request.session.get("api_key", "")
        if not session_api_key:
            errors.append("Confirm OpenAI integration before uploading files.")
        if not pdf_file and not image_files:
            errors.append("Upload a PDF or at least one image.")

        if pdf_file and not is_pdf(pdf_file.name):
            errors.append("PDF file type is invalid.")

        invalid_images = [f.name for f in image_files if not is_image(f.name)]
        if invalid_images:
            errors.append("One or more image files are invalid.")

        if errors:
            context["errors"] = errors
            return render(request, "home.html", context)

        upload_id = uuid4().hex
        logger.info(
            "Upload accepted (pdf=%s, images=%s)",
            bool(pdf_file),
            len(image_files),
        )
        upload_root = Path(settings.MEDIA_ROOT) / "uploads" / upload_id

        pdf_path = None
        if pdf_file:
            pdf_dir = upload_root / "pdf"
            ensure_dir(pdf_dir)
            pdf_path = pdf_dir / pdf_file.name
            save_upload(pdf_file, pdf_path)

        image_paths = []
        if image_files:
            image_dir = upload_root / "images"
            ensure_dir(image_dir)
            for image_file in image_files:
                image_path = image_dir / image_file.name
                save_upload(image_file, image_path)
                image_paths.append(str(image_path))

        # Use session integration for API key/model during upload.

        request.session["upload_id"] = upload_id
        request.session["pdf_path"] = str(pdf_path) if pdf_path else ""
        request.session["image_paths"] = image_paths

        return redirect("review")

    return render(request, "home.html", context)


def review(request):
    pdf_path = request.session.get("pdf_path")
    image_paths = request.session.get("image_paths", [])

    image_sequence = []
    for idx, path in enumerate(image_paths):
        file_path = Path(path)
        try:
            relative_path = file_path.relative_to(settings.MEDIA_ROOT).as_posix()
        except ValueError:
            relative_path = file_path.name

        image_sequence.append(
            {
                "index": idx + 1,
                "name": file_path.name,
                "url": f"{settings.MEDIA_URL}{relative_path}",
            }
        )

    if request.method == "POST":
        action = request.POST.get("action")
        try:
            index = int(request.POST.get("index", ""))
        except ValueError:
            index = -1

        if action in {"move_up", "move_down"} and 0 <= index < len(image_paths):
            if action == "move_up" and index > 0:
                image_paths[index - 1], image_paths[index] = (
                    image_paths[index],
                    image_paths[index - 1],
                )
            elif action == "move_down" and index < len(image_paths) - 1:
                image_paths[index + 1], image_paths[index] = (
                    image_paths[index],
                    image_paths[index + 1],
                )

            request.session["image_paths"] = image_paths
            return redirect("review")

        if action == "extract":
            try:
                pdf_list = [pdf_path] if pdf_path else []
                raw_text = extract_text(pdf_list, [])
                request.session["raw_text"] = raw_text
                request.session["extract_error"] = ""
                logger.info("PDF extraction completed (len=%s)", len(raw_text))
            except Exception as exc:  # noqa: BLE001
                request.session["extract_error"] = str(exc)
                logger.warning("PDF extraction failed: %s", exc)

            return redirect("review")

        if action == "generate_csv":
            raw_text = request.session.get("raw_text", "")
            api_key = request.session.get("api_key", "")
            model_name = request.session.get("openai_model", "gpt-4o-mini")
            try:
                csv_text = generate_testcases(
                    raw_text,
                    image_sequence,
                    image_paths,
                    api_key,
                    model_name,
                )
                headers, rows = parse_csv(csv_text)
                request.session["csv_text"] = rows_to_csv(headers, rows)
                request.session["csv_error"] = ""
                logger.info("CSV generated (rows=%s)", len(rows))
            except Exception as exc:  # noqa: BLE001
                request.session["csv_error"] = str(exc)
                logger.warning("CSV generation failed: %s", exc)

            return redirect("review")

        if action in {"save_csv", "add_row", "delete_row"}:
            csv_text = request.session.get("csv_text", "")
            if not csv_text:
                request.session["csv_error"] = "Generate CSV before editing."
                return redirect("review")

            try:
                headers, rows = parse_csv(csv_text)
            except Exception as exc:  # noqa: BLE001
                request.session["csv_error"] = str(exc)
                return redirect("review")

            row_count = int(request.POST.get("row_count", len(rows)))
            updated_rows = []
            for row_index in range(row_count):
                row_values = []
                for col_index in range(len(headers)):
                    key = f"cell_{row_index}_{col_index}"
                    row_values.append(request.POST.get(key, ""))
                updated_rows.append(row_values)

            if action == "add_row":
                updated_rows.append([""] * len(headers))
            elif action == "delete_row":
                delete_index = int(request.POST.get("delete_index", "-1"))
                if 0 <= delete_index < len(updated_rows):
                    updated_rows.pop(delete_index)

            request.session["csv_text"] = rows_to_csv(headers, updated_rows)
            request.session["csv_error"] = ""
            logger.info("CSV edited (rows=%s)", len(updated_rows))
            return redirect("review")

    raw_text = request.session.get("raw_text", "")
    csv_text = request.session.get("csv_text", "")
    csv_headers = []
    csv_rows = []
    if csv_text:
        try:
            csv_headers, csv_rows = parse_csv(csv_text)
        except Exception:
            csv_headers, csv_rows = [], []
    if not csv_headers:
        csv_headers = CSV_COLUMNS
    context = {
        "pdf_name": Path(pdf_path).name if pdf_path else "",
        "image_sequence": image_sequence,
        "raw_text_preview": raw_text[:1200],
        "raw_text_length": len(raw_text),
        "extract_error": request.session.get("extract_error", ""),
        "csv_error": request.session.get("csv_error", ""),
        "csv_headers": csv_headers,
        "csv_rows": csv_rows,
    }
    return render(request, "review.html", context)


def download_csv(request):
    csv_text = request.session.get("csv_text", "")
    if not csv_text:
        return redirect("review")

    response = HttpResponse(csv_text, content_type="text/csv")
    response["Content-Disposition"] = "attachment; filename=testcases.csv"
    return response


def generate(request):
    image_paths = request.session.get("image_paths", [])
    image_sequence = []
    for idx, path in enumerate(image_paths):
        file_path = Path(path)
        try:
            relative_path = file_path.relative_to(settings.MEDIA_ROOT).as_posix()
        except ValueError:
            relative_path = file_path.name

        image_sequence.append(
            {
                "index": idx + 1,
                "name": file_path.name,
                "url": f"{settings.MEDIA_URL}{relative_path}",
            }
        )

    context = {
        "csv_upload_error": request.session.pop("csv_upload_error", ""),
        "csv_upload_status": request.session.pop("csv_upload_status", ""),
        "selected_framework": request.session.get("selected_framework", "selenium"),
        "reviewed_csv_headers": [],
        "reviewed_csv_rows": [],
        "image_sequence": image_sequence,
        "codegen_error": request.session.pop("codegen_error", ""),
        "codegen_status": request.session.pop("codegen_status", ""),
        "generated_code_preview": "",
    }

    generated_code = request.session.get("generated_code", "")
    if generated_code:
        context["generated_code_preview"] = generated_code[:1600]

    reviewed_csv_text = request.session.get("reviewed_csv_text", "")
    if reviewed_csv_text:
        try:
            headers, rows = parse_csv(reviewed_csv_text)
            context["reviewed_csv_headers"] = headers
            context["reviewed_csv_rows"] = rows
        except Exception:
            context["reviewed_csv_headers"] = []
            context["reviewed_csv_rows"] = []

    if request.method == "POST":
        action = request.POST.get("action", "validate_csv")
        csv_file = request.FILES.get("csv_file")
        framework = request.POST.get("framework", "selenium")

        if framework:
            request.session["selected_framework"] = framework

        if action == "validate_csv":
            try:
                headers, rows, csv_text = parse_uploaded_csv(csv_file)
                request.session["reviewed_csv_text"] = rows_to_csv(headers, rows)
                request.session["csv_upload_status"] = "CSV validated successfully."
                logger.info("CSV upload validated (rows=%s)", len(rows))
            except Exception as exc:  # noqa: BLE001
                request.session["csv_upload_error"] = str(exc)
                logger.warning("CSV upload validation failed: %s", exc)

        if action == "generate_code":
            reviewed_csv_text = request.session.get("reviewed_csv_text", "")
            api_key = request.session.get("api_key", "")
            model_name = request.session.get("openai_model", "gpt-4o-mini")
            if not reviewed_csv_text:
                request.session["codegen_error"] = "Validate a CSV before generating code."
                return redirect("generate")

            try:
                generated_code = generate_code_from_csv(
                    reviewed_csv_text,
                    framework,
                    image_sequence,
                    image_paths,
                    api_key,
                    model_name,
                )
                request.session["generated_code"] = generated_code
                request.session["codegen_status"] = "Code generated successfully."
                logger.info("Code generation completed (len=%s)", len(generated_code))
            except Exception as exc:  # noqa: BLE001
                request.session["codegen_error"] = str(exc)
                logger.warning("Code generation failed: %s", exc)

        return redirect("generate")

    return render(request, "generate.html", context)


def output(request):
    context = {
        "generated_code": request.session.get("generated_code", ""),
    }
    return render(request, "output.html", context)


def download_code(request):
    generated_code = request.session.get("generated_code", "")
    if not generated_code:
        return redirect("output")

    response = HttpResponse(generated_code, content_type="text/plain")
    response["Content-Disposition"] = "attachment; filename=generated_tests.py"
    return response

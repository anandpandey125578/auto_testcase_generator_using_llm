import csv
import io

CSV_COLUMNS = [
    "TC_ID",
    "Module",
    "Title",
    "Preconditions",
    "Steps",
    "Test_Data",
    "Expected_Result",
    "Type (UI/API)",
    "Priority (High/Medium/Low)",
    "Automation_Candidate (Yes/No)",
]


def validate_csv_schema(headers):
    return headers == CSV_COLUMNS


def parse_csv(csv_text):
    reader = csv.reader(io.StringIO(csv_text))
    rows = list(reader)
    if not rows:
        raise ValueError("CSV output is empty.")

    headers = rows[0]
    if not validate_csv_schema(headers):
        raise ValueError("CSV schema mismatch.")

    return headers, rows[1:]


def rows_to_csv(headers, rows):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(rows)
    return output.getvalue()


def parse_uploaded_csv(file_obj):
    if not file_obj:
        raise ValueError("No CSV file uploaded.")

    content = file_obj.read()
    if not content:
        raise ValueError("Uploaded CSV is empty.")

    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("CSV must be UTF-8 encoded.") from exc

    headers, rows = parse_csv(text)
    return headers, rows, text

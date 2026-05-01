def is_pdf(file_name):
    return file_name.lower().endswith(".pdf")


def is_image(file_name):
    return file_name.lower().endswith((".png", ".jpg", ".jpeg"))

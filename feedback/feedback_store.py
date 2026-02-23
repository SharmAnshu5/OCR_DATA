def save_feedback(
    conn,
    file_name,
    field_name,
    extracted_value,
    correct_value,
    confidence,
    source
):
    sql = """
    INSERT INTO OCR_FEEDBACK
    (FILE_NAME, FIELD_NAME, EXTRACTED_VALUE, CORRECT_VALUE, CONFIDENCE, SOURCE)
    VALUES (:1, :2, :3, :4, :5, :6)
    """
    conn.cursor().execute(
        sql,
        (
            file_name,
            field_name,
            extracted_value,
            correct_value,
            confidence,
            source,
        ),
    )
    conn.commit()

import logging

DB_COLUMNS = [
    "FILE_NAME", 
    "AGENCY_CODE",
    "AGENCY_NAME",
    "CLIENT_CODE",
    "CLIENT_NAME",
    "RO_CLIENT_CODE",
    "RO_CLIENT_NAME", 
    "RO_NUMBER",
    "RO_DATE",
    "KEY_NUMBER",
    "COLOUR",
    "AD_CAT",
    "AD_SUBCAT",
    "PRODUCT",
    "BRAND",
    "PACKAGE_NAME",
    "INSERT_DATE",
    "AD_HEIGHT",
    "AD_WIDTH",
    "AD_SIZE",
    "PAGE_PREMIUM",
    "RO_AMOUNT",
    "RO_RATE",
    "RO_REMARKS",
    "EXTRACTED_TEXT",
    "POSITIONING"
]

SQL = """
INSERT INTO RO_OCR_DATA (
    FILE_NAME,
    AGENCY_CODE,
    AGENCY_NAME,
    CLIENT_CODE,
    CLIENT_NAME,
    RO_CLIENT_CODE,
    RO_CLIENT_NAME,
    RO_NUMBER,
    RO_DATE,
    KEY_NUMBER,
    COLOUR,
    AD_CAT,
    AD_SUBCAT,
    PRODUCT,
    BRAND,
    PACKAGE_NAME,
    INSERT_DATE,
    AD_HEIGHT,
    AD_WIDTH,
    AD_SIZE,
    PAGE_PREMIUM,
    RO_AMOUNT,
    RO_RATE,
    RO_REMARKS,
    EXTRACTED_TEXT,
    POSITIONING,
    CREATED_DT
) VALUES (
    :FILE_NAME,
    :AGENCY_CODE,
    :AGENCY_NAME,
    :CLIENT_CODE,
    :CLIENT_NAME,
    :RO_CLIENT_CODE,
    :RO_CLIENT_NAME,
    :RO_NUMBER,
    TO_DATE(:RO_DATE, 'DD-MM-YYYY'),
    :KEY_NUMBER,
    :COLOUR,
    :AD_CAT,
    :AD_SUBCAT,
    :PRODUCT,
    :BRAND,
    :PACKAGE_NAME,
    TO_DATE(:INSERT_DATE, 'DD-MM-YYYY'),
    :AD_HEIGHT,
    :AD_WIDTH,
    :AD_SIZE,
    :PAGE_PREMIUM,
    :RO_AMOUNT,
    :RO_RATE,
    :RO_REMARKS,
    :EXTRACTED_TEXT,
    :POSITIONING,    
    SYSDATE
)
"""


def insert_ro_data(conn, data: dict):
    bind_data = {}
    for col in DB_COLUMNS:
        value = data.get(col)
        if value == "":
            value = None
        bind_data[col] = value
    logging.debug("FINAL DB BINDS:")
    for k, v in bind_data.items():
        logging.debug("  %s = %s", k, v)
    cur = conn.cursor()
    cur.execute(SQL, bind_data)
    conn.commit()
    logging.info("DB INSERT SUCCESS")


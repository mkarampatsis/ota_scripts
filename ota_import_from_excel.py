import json
import re

import pandas as pd
from datetime import datetime, timezone

from connection import get_database
from models.cofog import Cofog
from models.ota import Ota

dbname = get_database()

# ---------- CONFIG ----------
EXCEL_FILE = "ota_table.xlsx"
OUTPUT_JSON = "ota_table_import.json"

# Fixed refs (adjust if needed)
LEGAL_PROVISION_REFS = ["693dad20c781bc1fe764138b"]

# ---------- HELPERS ----------


def extract_code(value: str | float | None) -> str | None:
    """
    Extract numeric code from strings like:
    '2.1.1 some name', '2.1.1. some name', '2 some name', etc.
    Returns '2.1.1', '2', etc.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    s = str(value).strip()

    # First token until space
    first_token = s.split()[0]

    # Remove trailing dot if exists (e.g. '2.1.1.' -> '2.1.1')
    first_token = first_token.rstrip(".")

    # Validate pattern: digits and dots only
    if re.fullmatch(r"[0-9]+(\.[0-9]+)*", first_token):
        return first_token
    return None


def build_cofog_name_index(cofog_docs):
    """
    Build a flat index: code -> name for cofog1, cofog2, cofog3
    using MongoEngine document attributes.
    """
    index = {}

    for doc in cofog_docs:
        # Cofog1
        code1 = doc.code
        name1 = doc.name
        if code1 and name1:
            index[code1] = name1

        # Cofog2
        for c2 in doc.cofog2:
            code2 = c2.code
            name2 = c2.name
            if code2 and name2:
                index[code2] = name2

            # Cofog3
            for c3 in c2.cofog3:
                code3 = c3.code
                name3 = c3.name
                if code3 and name3:
                    index[code3] = name3

    return index


def get_cofog_name(code: str | None, index: dict) -> str | None:
    if not code:
        return None
    return index.get(code)


# ---------- MAIN ----------
def main():
    # Load all cofog docs and build index
    cofog_docs = list(Cofog.objects())
    cofog_index = build_cofog_name_index(cofog_docs)

    # Read Excel
    df = pd.read_excel(EXCEL_FILE)

    # Expect columns exactly as described
    # Adjust if actual headers differ
    col_1 = "Φορέας άσκησης αρμοδιότητας"
    col_2 = "Τύπος Αρμοδιότητας"
    col_3 = "Αυτοδιοικητική/Κρατική"
    col_4 = "Cofog 1ο επίπεδο"
    col_5 = "Cofog 2ο επίπεδο"
    col_6 = "Cofog 3ο επίπεδο"
    col_7 = "Παράρτημα Κωδικός αρμοδιότητας"
    col_8 = "Κείμενο αρμοδιότητας"
    col_9 = "Φορέα Δημόσιας Πολιτικής (Κωδικός)"

    now_iso = datetime.now(timezone.utc).isoformat()

    documents = []

    for _, row in df.iterrows():
        remit_competence = row.get(col_1)
        remit_type = row.get(col_2)
        remit_local_or_global = row.get(col_3)
        cofog1_raw = row.get(col_4)
        cofog2_raw = row.get(col_5)
        cofog3_raw = row.get(col_6)
        annex_code = row.get(col_7)
        remit_text = row.get(col_8)
        org_code = row.get(col_9)

        cofog1_code = extract_code(cofog1_raw)
        cofog2_code = extract_code(cofog2_raw)
        cofog3_code = extract_code(cofog3_raw)

        cofog1_name = get_cofog_name(cofog1_code, cofog_index)
        cofog2_name = get_cofog_name(cofog2_code, cofog_index)
        cofog3_name = get_cofog_name(cofog3_code, cofog_index)

        doc = {
            "createdAt": {"$date": now_iso},
            "updatedAt": {"$date": now_iso},
            "remitText": remit_text if pd.notna(remit_text) else "",
            "remitCompetence": remit_competence if pd.notna(remit_competence) else "",
            "remitType": remit_type if pd.notna(remit_type) else "",
            "remitLocalOrGlobal": remit_local_or_global
            if pd.notna(remit_local_or_global)
            else "",
            "legalProvisionRefs": [{"$oid": oid} for oid in LEGAL_PROVISION_REFS],
            "instructionProvisionRefs": [],
            "publicPolicyAgency": {
                "organization": "",
                "organizationCode": org_code if pd.notna(org_code) else "",
                "organizationType": "",
                "status": "Active",
                "subOrganizationOf": "",
                "subOrganizationOfCode": "",
            },
            "cofog": {
                "cofog1": cofog1_code,
                "cofog1_name": cofog1_name,
                "cofog2": cofog2_code,
                "cofog2_name": cofog2_name,
                "cofog3": cofog3_code,
                "cofog3_name": cofog3_name,
            },
            "status": "ΕΝΕΡΓΗ",
            "finalized": False,
            "elasticSync": False,
            # Optional: include annex code if you need it
            "annexCode": annex_code if pd.notna(annex_code) else "",
        }

        documents.append(doc)

    # Write JSON file for import
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(documents, f, ensure_ascii=False, indent=2)

    print(f"Exported {len(documents)} documents to {OUTPUT_JSON}")


if __name__ == "__main__":
    main()

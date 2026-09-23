from fastapi import FastAPI, Query
from fastapi.responses import Response
import pandas as pd
import re
import json
from pathlib import Path
from datetime import datetime

from metadata import metadata_response
app = FastAPI()
ODATA_CONTENT_TYPE = "application/json;odata.metadata=minimal"
ODATA_HEADERS = {
    "Content-Type": ODATA_CONTENT_TYPE,
    "OData-Version": "4.0"
}



@app.get("/Orders")
def get_orders(
    odata_filter: str | None = Query(default=None, alias="$filter"),
    odata_select: str | None = Query(default=None, alias="$select"),
    odata_orderby: str | None = Query(default=None, alias="$orderby"),
    odata_top: int | None = Query(default=None, alias="$top"),
    odata_skip: int | None = Query(default=None, alias="$skip")
):
    # Load the Excel dataset
    df = pd.read_excel("orders.xlsx")
    result = df

    if odata_filter:
        match = re.fullmatch(
            r"(\w+)\s+(eq|gt|ge|lt|le)\s+(.+)",
            odata_filter
        )

        if not match:
            return Response(
                content='{"error":"Unsupported $filter expression"}',
                media_type="application/json",
                status_code=400
            )

        column, operator, value = match.groups()

        if column not in result.columns:
            return Response(
                content='{"error":"Unknown property"}',
                media_type="application/json",
                status_code=400
            )

        # String value
        if value.startswith("'") and value.endswith("'"):
            value = value[1:-1]

            if operator != "eq":
                return Response(
                    content='{"error":"String comparison only supports eq"}',
                    media_type="application/json",
                    status_code=400
                )

            result = result[
                result[column].astype(str).str.lower() == value.lower()
            ]

        # Numeric value
        else:
            try:
                value = float(value)
            except ValueError:
                return Response(
                    content='{"error":"Invalid filter value"}',
                    media_type="application/json",
                    status_code=400
                )

            numeric_column = pd.to_numeric(
                result[column],
                errors="coerce"
            )

            if operator == "eq":
                result = result[numeric_column == value]
            elif operator == "gt":
                result = result[numeric_column > value]
            elif operator == "ge":
                result = result[numeric_column >= value]
            elif operator == "lt":
                result = result[numeric_column < value]
            elif operator == "le":
                result = result[numeric_column <= value]

    if odata_orderby:
        parts = odata_orderby.split()

        column = parts[0]
        direction = parts[1].lower() if len(parts) >1 else "asc"

        if column not in result.columns:
            return Response(
                content= '{"error" : "Unknown property in $orderby"}',
                media_type = "application/json",
                status_code = 400
            )

        if direction not in ["asc","desc"]:
            return Response(
                content= '{"error" : "Invalid $orderby direction"}',
                media_type = "application/json",
                status_code = 400
            )

        result = result.sort_values(
            by = column,
            ascending = (direction == "asc")
        )

    if odata_skip is not None:
        if odata_skip < 0:
            return Response(
                content= '{"error" : "$skip cannot be negative"}',
                media_type = "application/json",
                status_code = 400
            )
        result = result.iloc[odata_skip:]

    if odata_top is not None:
            if odata_top < 0:
                return Response(
                    content= '{"error" : "$top cannot be negative"}',
                    media_type = "application/json",
                    status_code = 400
                )
            result = result.iloc[:odata_top]

    if odata_select:
        columns = [column.strip() for column in odata_select.split(",")]

        invalid_columns = [
            column for column in columns
            if column not in result.columns
        ]

        if invalid_columns:
            return Response(
                content='{"error":"Unknown property in $select"}',
                media_type="application/json",
                status_code=400
            )

        result = result[columns]

    response_data = {
        "@odata.context": "http://127.0.0.1:8000/$metadata#Orders",
        "value": result.to_dict(orient="records")
    }

    return Response(
        content=json.dumps(
            response_data,
            default = str
            # orient="records",
            # date_format="iso"
        ),
        headers = ODATA_HEADERS
    )

@app.get("/")
def get_service_document():
    service_document = {
        "@odata.context" : "http://127.0.0.1:8000/$metadata",
        "value": [
            {
                "name":"Orders",
                "kind":"EntitySet",
                "url":"Orders"
            }
        ]
    }

    return Response(
        content = json.dumps(
            service_document,
            default=str
        ),
        headers= ODATA_HEADERS
    )

@app.get("/$metadata")
def get_metadata():
    return metadata_response()

@app.get("/health")
def health_check():
    file_path = Path("orders.xlsx")

    return {
        "status": "ok",
        "source": "orders.xlsx",
        "source_last_modified": datetime.fromtimestamp(
            file_path.stat().st_mtime
        ).isoformat()
    }
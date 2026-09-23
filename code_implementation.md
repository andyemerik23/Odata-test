# Code Implementation

## Packages and Libraries

| Name                          | Purpose of Use                                                                                |
| ----------------------------- | ----------------------------------------------------------------------------------------------- |
| `fastapi`                     | Creates the HTTP API and defines the application's endpoints.                                  |
| `uvicorn`                     | Runs the FastAPI application as an ASGI server.                                                 |
| `pandas`                      | Loads and manipulates the Excel dataset through DataFrames.                                     |
| `openpyxl`                    | Provides `.xlsx` file support for pandas.                                                       |
| `re`                          | Parses the limited `$filter` expression structure supported by the implementation.              |
| `json`                        | Serializes Python response objects into JSON.                                                   |
| `pathlib.Path`                | Handles the source-file path and retrieves file metadata for the health endpoint.               |
| `datetime`                    | Converts the source file modification time into an ISO-formatted timestamp.                     |
| `fastapi.Query`               | Maps HTTP query parameters such as `$filter` to Python function arguments.                      |
| `fastapi.responses.Response`  | Provides direct control over HTTP response bodies, headers, content types, and status codes.    |

---

## 1. Code Implementation Overview

The Python implementation is divided primarily between `app.py` and `metadata.py`. Each file has a distinct responsibility within the OData service.

```text
app.py
│
├── Application
├── Data loading
├── HTTP endpoints
├── Query processing
└── JSON responses

metadata.py
│
└── OData v4 schema definition
```

`app.py` is responsible for serving and processing the actual data, while `metadata.py` describes the structure of that data to OData clients.

The implementation is intentionally lightweight. It provides the subset of OData behavior required for the Tableau Public experiment rather than attempting to implement the complete OData v4 specification.

---

## `app.py`

### 1. Application Imports

The main application imports the FastAPI framework, HTTP response utilities, pandas, regular expressions, JSON serialization, and the metadata response function.

The core imports are:

```python
from fastapi import FastAPI, Query
from fastapi.responses import Response
import pandas as pd
import re
import json

from metadata import metadata_response
```

The health endpoint additionally uses Python's standard-library modules for file information and timestamps:

```python
from pathlib import Path
from datetime import datetime
```

### 2. FastAPI Application

The application is initialized with:

```python
app = FastAPI()
```

This creates the FastAPI application object to which the HTTP routes are attached.

FastAPI acts as the web framework between the Python application and HTTP clients such as Tableau.

### 3. OData Response Configuration

The application defines the response information required by the OData v4 client:

```python
ODATA_CONTENT_TYPE = "application/json;odata.metadata=minimal"

ODATA_HEADERS = {
    "Content-Type": ODATA_CONTENT_TYPE,
    "OData-Version": "4.0"
}
```

These values identify the response as an OData v4-compatible response.

During development, Tableau initially rejected the service because the response was not sufficiently identified as an OData v4 response. Adding the `OData-Version: 4.0` header and the OData-compatible JSON content type allowed Tableau to recognize the service correctly.

### 4. Loading the Dataset

The application uses pandas to read the Excel source:

```python
df = pd.read_excel("orders.xlsx")
```

The resulting DataFrame becomes the in-memory representation of the source dataset.

Conceptually:

```text
orders.xlsx
    ↓
pd.read_excel()
    ↓
pandas DataFrame
    ↓
OData processing
```

The later implementation also considers source freshness by reading the Excel file when the `/Orders` endpoint is requested. This allows source changes to become visible through the API without requiring a server restart.

### 5. `/Orders` Endpoint

The central API endpoint is:

```python
@app.get("/Orders")
```

This endpoint represents the OData entity set:

```text
Orders
```

It accepts several query parameters:

```text
odata_filter
odata_select
odata_orderby
odata_top
odata_skip
```

Each parameter is mapped to the corresponding OData query option:

```text
$filter
$select
$orderby
$top
$skip
```

For example:

```text
/Orders?$filter=Sales%20gt%2010000000
```

is received by FastAPI as the value of `odata_filter`.

This allows the application to translate an OData-style URL into pandas operations.

### 6. `$filter`

The `$filter` implementation validates the expression using a regular expression.

The supported basic structure is:

```text
Property Operator Value
```

For example:

```text
Sales gt 10000000
```

The implementation recognizes:

```text
eq  →  =
gt  →  >
ge  →  >=
lt  →  <
le  →  <=

```

The requested property is checked against the DataFrame columns before filtering.

String comparisons are handled separately from numeric comparisons. For example:

```text
City eq 'Malang'
```

performs a case-insensitive string comparison.

Numeric expressions such as:

```text
Sales gt 10000000
```

convert the target value to a numeric value and compare it against the corresponding DataFrame column.

The processing flow is therefore:

```text
OData expression
    ↓
FastAPI parameter
    ↓
Python parsing
    ↓
pandas filtering
```

The implementation intentionally supports only a restricted subset of `$filter`. More complex expressions involving logical operators, functions, nested expressions, or navigation properties are outside the scope of this implementation.

### 7. `$orderby`

The `$orderby` implementation reads a property and an optional direction.

For example:

```text
Sales desc
```

The direction can be:

```text
asc
desc
```

The application then uses pandas sorting:

```python
result.sort_values(
    by=column,
    ascending=(direction == "asc")
)
```

This connects the OData concept of ordering to pandas DataFrame sorting.

The current implementation supports one primary order-by expression rather than the full range of OData ordering capabilities.

### 8. `$skip`

`$skip` removes the first N records.

For example:

```text
/Orders?$skip=5
```

The implementation uses:

```python
result.iloc[odata_skip:]
```

A negative `$skip` value is rejected because it would not represent a valid pagination operation.

### 9. `$top`

`$top` limits the number of returned records.

For example:

```text
/Orders?$top=5
```

The implementation uses:

```python
result.iloc[:odata_top]
```

A negative value is rejected.

The combination of `skip`and`top` therefore provides a simple form of pagination:

```text
$skip=10
$top=5
```

This means that the service skips the first 10 records and returns the next 5 records.

### 10. `$select`

`$select` controls which properties are included in the response.

For example:

```text
/Orders?$select=Order_ID,City,Sales
```

The request is converted into a list of requested columns.

The implementation first validates that every requested column exists in the DataFrame. Only valid columns are then returned.

This demonstrates an important OData concept:

```text
Full entity
    ↓
$select
    ↓
Projected entity
```

However, `select`affectsthereturnedrecords,while`metadata` still describes the complete entity schema.

This explains why Tableau can still identify fields that were not present in a particular `$select` response.

### 11. OData JSON Response

After query processing, the DataFrame is converted into a list of dictionaries:

```python
result.to_dict(orient="records")
```

The response is wrapped in an OData-style structure:

```python
response_data = {
    "@odata.context": "...",
    "value": result.to_dict(orient="records")
}
```

The response is then serialized using:

```python
json.dumps(
    response_data,
    default=str
)
```

The `default=str` option allows values such as dates to be serialized into JSON-compatible representations.

### 12. Service Document

The root endpoint:

```python
@app.get("/")
```

returns the service document.

It identifies:

```text
Orders
```

as an entity set.

Conceptually, the response tells an OData client that the service contains the `Orders` entity set. This is the first discovery layer before the client requests the entity collection or metadata.

### 13. `$metadata` Endpoint

The metadata route is:

```python
@app.get("/$metadata")
def get_metadata():
    return metadata_response()
```

Rather than embedding the XML directly inside `app.py`, the application delegates the response to `metadata.py`.

This keeps the application logic and schema definition separated.

### 14. Health Endpoint

The `/health` endpoint provides a simple operational check.

It reports:

```text
status
source
source_last_modified
```

The file timestamp is obtained from the operating system using `Path.stat()` and converted into an ISO-formatted timestamp.

The endpoint is useful for distinguishing:

```text
Is the API running?
```

from:

```text
When was the source file last modified?
```

The `source_last_modified` value should not be interpreted as the Tableau extract-refresh timestamp.

---

## `metadata.py`

### 1. Metadata Implementation

`metadata.py` contains the OData metadata XML.

The metadata begins with the OData EdmX namespace and declares version 4.0.

The central entity is:

```xml
<EntityType Name="Order">
```

This represents the schema of a single order entity.

The collection is:

```xml
<EntitySet Name="Orders"
    EntityType="ODataDemo.Order"/>
```

This represents the collection of order entities exposed by the service.

The relationship is therefore:

```text
Order
    = one entity

Orders
    = collection of Order entities
```

### 2. Entity Key

The entity defines:

```xml
<Key>
    <PropertyRef Name="Order_ID"/>
</Key>
```

This identifies `Order_ID` as the entity key.

Conceptually:

```text
Order
└── Order_ID
        ↓
    unique identity
```

The key allows an OData client to understand which property identifies an individual entity.

### 3. Property Definitions

Each dataset column is represented as an OData property.

For example:

```xml
<Property Name="Order_ID"
    Type="Edm.String"
    Nullable="false"/>
```

A numeric property is defined as:

```xml
<Property Name="Quantity"
    Type="Edm.Int32"/>
```

Another numeric property is defined as:

```xml
<Property Name="Sales"
    Type="Edm.Double"/>
```

The metadata therefore acts as a contract between the API and the client.

The DataFrame contains the actual values, while the metadata describes what those values mean structurally.

## Dictionary

| Name                 | Purpose of Use                                                                                                 |
| --------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `FastAPI`             | Creates the FastAPI web application and provides the framework for defining HTTP routes.                        |
| `Uvicorn`             | Runs the FastAPI application and listens for HTTP requests.                                                     |
| `pandas`              | Provides the DataFrame used to load, filter, sort, select, and transform the Excel data.                        |
| `openpyxl`            | Acts as the Excel engine used by pandas to read the `.xlsx` source file.                                        |
| `Query`               | Defines and maps HTTP query-string parameters such as `filter`,`select`, `orderby`,`top`, and `$skip`.    |
| `Response`            | Provides explicit control over the HTTP response body, content type, headers, and status code.                  |
| `re`                  | Parses the limited `$filter` syntax implemented by the service.                                                 |
| `json`                | Converts Python response objects into a JSON response body following the OData-style response structure.        |
| `Path`                | Inspects the `orders.xlsx` source file and obtains information such as its last modification time.              |
| `datetime`            | Converts the source file modification timestamp into an ISO-formatted timestamp for the `/health` response.     |
| `metadata_response`   | Returns the OData metadata XML defined in `metadata.py`.                                                        |
| `app`                 | Represents the FastAPI application to which the project's HTTP routes are attached.                             |
| `ODATA_CONTENT_TYPE`  | Defines the JSON content type used by the OData-compatible responses.                                           |
| `ODATA_HEADERS`       | Defines the HTTP headers required to identify the service as an OData v4-compatible response.                   |
| `df`                  | Represents the Excel dataset as a pandas DataFrame during data processing.                                      |
| `odata_filter`        | Receives the `$filter` query parameter and passes it to the filtering logic.                                    |
| `odata_select`        | Receives the `$select` query parameter and determines which properties are returned.                            |
| `odata_orderby`       | Receives the `$orderby` query parameter and determines the sorting operation.                                   |
| `odata_top`           | Receives the `$top` query parameter and limits the number of returned records.                                  |
| `odata_skip`          | Receives the `$skip` query parameter and determines how many records are skipped.                               |


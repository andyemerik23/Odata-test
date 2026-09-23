# OData v4 Service for Tableau Public

## Project Overview

This project demonstrates how an Excel-based dataset can be exposed through a lightweight OData v4-compatible web service and consumed by Tableau Public for data visualization.

The main objective is to understand the technical relationship between a source file, a data-serving API, the OData protocol, and a business intelligence platform. Instead of connecting Tableau directly to the Excel file, the project introduces FastAPI as an intermediary service. Python and pandas read the source data, FastAPI exposes the data through HTTP endpoints, and the service follows the basic OData v4 conventions required by Tableau.

The resulting architecture is:

```text
orders.xlsx
     │
     ▼
  pandas
     │
     ▼
  FastAPI
     │
     ▼
 OData v4 API
     │
     ▼
Tableau Public
     │
     ▼
 Tableau Extract
     │
     ▼
 Dashboard
```

The project is intentionally implemented as a lightweight OData-compatible service rather than a complete production-grade OData server. The purpose is educational: to understand how OData metadata, entity sets, query options, HTTP responses, and Tableau extracts interact.

A particularly important finding from the implementation is that the OData service and Tableau Public have different responsibilities for data freshness. The FastAPI service can expose the latest data available in `orders.xlsx`, but Tableau Public consumes the OData source through an extract. Therefore, changes in the Excel source are not automatically reflected in the Tableau dashboard until the Tableau extract is refreshed.

This distinction became one of the main architectural insights of the project.

---

## Dataset Source Description

The dataset used in this project is a synthetic generated Excel dataset named `orders.xlsx`.

The dataset represents simplified order transactions and contains 100 records in 10 fields. The dataset is stored locally because the objective is to demonstrate the data-serving architecture rather than to build a production ingestion pipeline.

The Excel file acts as the source layer. pandas is responsible for reading the spreadsheet into a DataFrame, while FastAPI exposes that DataFrame through HTTP endpoints.

An important implementation decision was to keep the dataset relatively small. This makes it easier to inspect the raw data, manually modify individual records, observe how those changes propagate through the API, and compare the API response with the Tableau extract.

---

## Tools and Software Used

| Name           | Purpose                                                              |
| -------------- | --------------------------------------------------------------------- |
| Python         | Main programming language used to implement the service               |
| FastAPI        | Web framework used to create the HTTP API                              |
| Uvicorn        | ASGI server used to run the FastAPI application                        |
| pandas         | Reads and processes the Excel dataset                                  |
| openpyxl       | Excel engine used by pandas to read `.xlsx` files                      |
| VS Code        | Development environment for the Python project                        |
| Excel          | Source data storage and manual source-data modification                |
| curl           | Used to independently test HTTP endpoints                              |
| Tableau Public | BI platform used to consume the OData service and build the dashboard  |
| OData v4       | Data-access protocol/interface exposed by the FastAPI service          |

---

## Architecture

The project consists of the following components:

```text
D:\Odata-test
│
├── orders.xlsx
├── app.py
├── metadata.py
└── .venv/
```

---

## Discovery and Insights

**1. OData is an interface, not the data source**

FastAPI and pandas perform the data-serving work. OData provides a standardized way for clients such as Tableau to request and understand the data. The system can therefore be described as: "Tableau consumes Excel-derived data exposed by a FastAPI service through an OData v4-compatible interface."

**2. Metadata is fundamental to OData clients**

The `$metadata` endpoint is not simply documentation for humans. It acts as a machine-readable schema describing the entity, properties, keys, and types. Without appropriate metadata, Tableau cannot reliably understand the structure of the service. This explains why the project contains both `app.py` for data retrieval and `metadata.py` for schema definition.

**3. HTTP response headers matter**

The first Tableau connection attempts demonstrated that returning JSON alone was insufficient. The response needed to communicate that the service was using OData v4. The service therefore returns `OData-Version: 4.0` along with an appropriate JSON content type. This demonstrated that interoperability depends not only on the response body but also on protocol-level information contained in the HTTP response.

**4. `$select` does not necessarily reduce Tableau's visible schema**

When `select`wasusedtorequestonlycertaincolumns,theAPIcorrectlyreturnedthosefields.However,Tableaucouldstillidentifythebroaderschemabecauseitobtainedtheschemafrom`metadata`. Consequently, field projection in an individual data request and schema discovery are separate concepts.

**5. Tableau Public introduces an extract boundary**

The FastAPI service can expose updated source data, but Tableau Public consumes the source through an extract. The API can already contain the new value while the dashboard continues to display the previous extract.

**6. Tableau filters do not prove that OData queries are being reissued**

When a Tableau filter was applied, there was not necessarily a corresponding new request visible in the FastAPI server. This is consistent with Tableau operating on its extracted dataset after the data has already been retrieved. Therefore, BI-layer filtering and source-layer OData filtering should be treated as separate operations.

---

## Limitations and Recommendations

This implementation is intentionally lightweight and should not be treated as a production OData platform.

1. **The service is currently bound to `127.0.0.1`.**
   This makes it suitable for local development and experimentation but not for a publicly accessible Tableau deployment. A production-oriented architecture would require a publicly reachable HTTPS endpoint and an appropriate hosting environment.

2. **The service implements only a subset of OData functionality.**
   It supports the query operations needed for this experiment, but it is not a complete implementation of the OData v4 specification.

3. **The use of Excel as the source layer.**
   Excel is appropriate for demonstrating the architecture, but a production data platform would generally use a database, data warehouse, object storage system, or another managed data source depending on the workload.

4. **Lack of security.**
   The current service does not implement authentication, authorization, rate limiting, production-grade logging, or other security controls expected from an internet-facing API.

5. **Tableau Public's extract-based behavior.**
   In this implementation, the API can expose current source data, but the dashboard does not continuously consume the API as a live query interface. The extract must be refreshed for updated source data to appear in the dashboard.

For a production-oriented extension, the architecture could therefore evolve toward:

```text
Production Data Source --> Data Ingestion --> Database / Data Warehouse --> OData / API Layer --> HTTPS + Security Controls --> BI Platform
```

The current project should therefore be understood as a technical demonstration of the relationship between an OData service and Tableau Public, rather than as a production-ready deployment.

---

## Conclusion

This project successfully demonstrates an end-to-end path from an Excel source dataset to a Tableau Public dashboard through a custom FastAPI-based OData v4-compatible service.

The most significant outcome is not simply that Tableau can connect to the service. The implementation demonstrates how schema metadata, HTTP responses, OData query options, API processing, Tableau extraction, and dashboard visualization interact.

The testing also established a clear architectural boundary: the FastAPI/OData service can expose updated source data independently of Tableau's extract. Consequently, source freshness and dashboard freshness are separate concerns. The project therefore provides a practical foundation for understanding OData as a standardized data-serving interface and Tableau Public as an extract-based BI consumer.



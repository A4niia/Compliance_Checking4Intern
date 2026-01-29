# AIT Student Policy Validation Prototype

## 1. Project Overview

This project is a proof-of-concept prototype for a Master's Thesis focused on creating an automated data quality validation and natural language explanation framework. It utilizes a combination of Semantic Web technologies (Ontology, SHACL, SPARQL) and a relational database (PostgreSQL) to validate AIT student data against official policies and procedures (P&P).

The core workflow demonstrated in this prototype is:
**SQL Database -> Virtual Knowledge Graph -> SHACL Validation**

This setup serves as the foundation for the next phase, which will involve using Large Language Models (LLMs) to generate human-readable explanations from the structured validation reports produced by this system.

## 2. Prerequisites

Before running this project, please ensure you have the following software installed:
*   [Docker](https://www.docker.com/products/docker-desktop/)
*   [Docker Compose](https://docs.docker.com/compose/install/) (usually included with Docker Desktop)
*   A database management tool, such as [DBeaver](https://dbeaver.io/) or pgAdmin.

## 3. Project Structure

```
ait-policy-prototype/
├── docker-compose.yml        # Defines and configures the project's services (GraphDB & PostgreSQL).
├── .env                      # Stores database credentials (MUST be created manually).
├── graphdb_lib_jdbc/         # Contains the PostgreSQL JDBC driver.
│   └── postgresql-*.jar
├── postgres_data/            # Persistent data storage for the PostgreSQL container.
└── graphdb_data/             # Persistent data storage for the GraphDB container.
```

## 4. Quick Start & Setup Guide

Follow these steps to set up and run the entire environment.

### Step 1: Configure Environment Variables

1.  Create a file named `.env` in the root directory of this project.
2.  Add the following content to the `.env` file to set the database credentials:

    ```env
    POSTGRES_DB=ait_database
    POSTGRES_USER=postgres
    POSTGRES_PASSWORD=mysecretpassword
    ```

### Step 2: Download PostgreSQL JDBC Driver

1.  Download the PostgreSQL JDBC driver (`.jar` file) from the [official website](https://jdbc.postgresql.org/download/).
2.  Place the downloaded `.jar` file into the `graphdb_lib_jdbc/` directory.

### Step 3: Run the Environment

1.  Open a terminal in the project's root directory.
2.  Execute the following command to build and start the services in the background:
    ```bash
    docker-compose up -d
    ```
3.  To verify that both services are running, use `docker-compose ps`. Both `my-graphdb` and `ait-postgres` should show a `Up` status.

### Step 4: Prepare the PostgreSQL Database

1.  Connect to the PostgreSQL database using a tool like DBeaver with the credentials from your `.env` file (Host: `localhost`, Port: `5432`).
2.  Open a new SQL editor and execute the entire `setup_database.sql` script to create tables and insert sample data.

### Step 5: Configure GraphDB Repositories

1.  **Open GraphDB Workbench:** Navigate to `http://localhost:7200` in your web browser.

2.  **Create the Policy Repository (`ait_student_policy`):**
    *   Go to **Setup -> Repositories -> Create new repository**.
    *   **Repository ID:** `ait_student_policy`.
    *   **Enable SHACL:** Tick the checkbox for **Enable the SHACL validation**.
    *   Click **Create**.

3.  **Import Ontology and SHACL Rules:**
    *   Go to **Import -> RDF**. Use the **Text snippet** tab for the following:
    *   **Ontology:** Import the content of `AIT-ontology.ttl` into the **default graph** (leave "Target graphs" empty).
    *   **SHACL Rules:** Import the content of `ait-shacl-rules.ttl` into the **Named graph**: `http://rdf4j.org/schema/rdf4j#SHACLShapeGraph`.

4.  **Create the Virtual Repository (`ait_student_virtual`):**
    *   Go to **Setup -> Repositories -> Create new repository**.
    *   Select **Ontop Virtual SPARQL**.
    *   **Repository ID:** `ait_student_virtual`.
    *   **Connection Info:**
        *   Driver: `PostgreSQL`
        *   Host name: `postgres` (This is the service name from `docker-compose.yml`)
        *   Database name, Username, Password: Use the values from your `.env` file.
    *   **Ontop settings:** Upload the `ait-mapping.obda` file.
    *   Click **Test connection** to verify, then click **Create**.

## 5. How to Test the Workflow

To run a full end-to-end test of the validation workflow:

1.  Navigate to the **SPARQL** tab in GraphDB Workbench.
2.  Select the `ait_student_policy` repository.
3.  Execute the federated query from `federated_insert_query.sparql`.

**Expected Outcome:**
The query will **fail** with a `GraphDBShaclSailValidationException`. The error message will contain a detailed `ValidationReport` in Turtle format, identifying the specific students and rules that were violated. This proves that the automated validation workflow is functioning correctly.

## 6. Shutting Down

To stop and remove all containers, network, and volumes defined in this project, run the following command from the root directory:
```bash
docker-compose down
```
To stop without removing volumes, use `docker-compose stop`.
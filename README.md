# City Hive Assessment

A naive implementation of an ETL job that fetches raw inventory data from S3 and loads data into MongoDB via Rails

### System Requirements
* Docker v.25 or greater
* Docker Compose V2

### Install
* `git clone https://github.com/doellerbe/city-hive-assessment.git`

### Build
* `cd city-hive-assessment/inventory_unit_service`
* `docker compose up --build`

### Run ETL job
* `cd ../integration-eng`
* `python3 integration-exercise.py list_uploads` (options: 'generate_csv', 'upload', 'list_uploads')

### Verify Data in MongoDB
* `docker exec -it inventory_unit_service-db-1 /bin/bash`
* `root@68f6e11eddb4:/# mongosh mongodb://user:password@db:27017/admin`

#### Improvements to Solution
- Add AuthN and AuthZ to properly handle access to the API and comply with CSRF/CORS
- Add data validation to ensure there is no bad data that can make it to the DB
  - Use a schema registry to version the CSV data, JSON data, and Mongo data. This can provide constraints and validation as the data and requirements evolve
- Add exception handling during processing so failures can be dealt with more gracefully
- Refactor the Python code for readability and separation of concerns
  - Extract the HTML Parsing and URL building to its own class
  - Handle the data transform in its own class with proper exception handling
  - Handle API interactions in a separate class with proper exception handling

- Add a service layer to rails app to modify data for request/response
- Add bulk write functionality to rails so that the API endpoint is not spammed when handling large batches
- Add unit tests for python module to ensure transform logic does not regress
- Add unit tests for rails app to verify controller actions and data persistence

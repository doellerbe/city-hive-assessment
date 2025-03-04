import csv
import json
import statistics
import pendulum
from collections import Counter

import urllib3
from bs4 import BeautifulSoup


# 1. Using requests or any other HTTP library, grab the file HTML from: https://bitbucket.org/cityhive/jobs/src/master/integration-eng/integration-entryfile.html
# 2. Then, parse the URL for the csv file located in the S3 bucket (as part of the script, not by hand)
# 3. Make a GET request to Amazon's S3 with the details from #2 and save the to `local_file_path`

initial_html_file = "https://bitbucket.org/cityhive/jobs/raw/47fb39b480e7e5b588a5f57e6e068cea9fcbfcb2/integration-eng/integration-entryfile.html"
local_file_path = "resources/output.csv"


def build_s3_endpoint(html):
    soup = BeautifulSoup(html, 'html.parser')
    bucket = soup.find("div", {"id": "bucket-value"}).text
    region = soup.find("div", {"id": "region-value"})['data-region']
    object_path = soup.find("div", {"id": "object-value"})

    resource_path = ""
    paths = object_path.find_all("span", class_="path")[1:]

    for idx, path in enumerate(paths):
        resource_path += path.text
        if idx < len(paths) - 1:
            resource_path += '/'

    return f"https://{bucket}.s3.{region}.amazonaws.com/{resource_path}"


def fetch_s3_data(endpoint):
    response = http.request("GET", endpoint)
    if response.status == 200:
        with open(local_file_path, 'wb') as file:
            file.write(response.data)
        print(f"CSV file downloaded successfully to {local_file_path}")
    else:
        print(f"Failed to download CSV file. Status code: {response.status}")


def process_line(data):
    sale_date = ""
    if not data['Last_Sold'] is None and not data['Last_Sold'] == "NULL":
        dt = pendulum.parse(data['Last_Sold'])
        if not dt.year == 2020:
            return
        sale_date = dt
        print(f"DATE: {sale_date}")
    else:
        return

    upc = data['ItemNum']
    internal_id = ""

    if len(upc) < 5:
        internal_id = f"biz_id_{upc}"
        upc = ""
    else:
        for char in upc:
            if not char.isdigit():
                internal_id = f"biz_id_{upc}"
                upc = ""
    print(f"UPC: {upc}")
    print(f"INTERNAL_ID: {internal_id}")

    price = 0.0
    if not data['Price'] is None:
        price = float(data['Price'])
    print(f"PRICE: {price}")
    cost = 0.0
    if not data['Cost'] is None:
        cost = float(data['Cost'])
    print(f"COST: {cost}")

    margin_percentage = 0.0
    if price > 0.0 and cost > 0.0:
        margin_percentage = abs(price - cost) / statistics.mean([cost, price]) * 100
    if margin_percentage > 30:
        price = round((price / 100) * 7, 2)
        print(f"MARGIN ABOVE 30: {price}")
    else:
        price = round((price / 100) * 9, 2)
        print(f"MARGIN 30 or LESS: {price}")

    if not data['ItemName'] is None and data['ItemName_Extra']:
        name = data['ItemName'] + data['ItemName_Extra']
        print(f"NAME: {name}")

    quantity = data['Quantity']
    print(f"QUANTITY: {quantity}")
    department = data['Dept_ID']
    print(f"DEPARTMENT: {department}")


def sanitize_headers(headers):
    """ Append a counter to duplicate headers to make them unique """
    counter = Counter(headers)
    seen = {}
    new_headers = []

    for h in headers:
        # print(f"HEADER: {h}")
        # print(counter[h])
        if counter[h] > 1:
            # print(f"Adding {h} to SEEN")
            if h not in seen:
                new_headers.append(h)
                seen[h] = 0
            else:
                seen[h] = seen.get(h) + 1
                new_headers.append(f"{h}_{seen[h]}")
        else:
            new_headers.append(h)

    return new_headers

# http = urllib3.PoolManager()
# response = http.request("GET", initial_html_file)
# endpoint = build_s3_endpoint(response.data)
# fetch_s3_data(endpoint)


with open(local_file_path, 'r') as in_file:
    reader = csv.DictReader(in_file, delimiter='|')
    sanitized_headers = sanitize_headers(reader.fieldnames)
    reader = csv.DictReader(in_file, delimiter='|', fieldnames=sanitized_headers)
    next(reader)  # remove the row with dashes

    for row in reader:
        process_line(row)


print("Finished!")

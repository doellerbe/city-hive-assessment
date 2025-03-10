import collections
import csv
import io
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
        return io.StringIO(response.data.decode('utf-8'))
    else:
        print(f"Failed to download CSV file. Status code: {response.status}")
        return None


def transform_line(row_idx, input, duplicate_sku_ids, sku_counter, output):
    input['Transform_ID'] = row_idx
    input['Tags'] = []

    last_sold = coalesce_null(input['Last_Sold'])
    if last_sold is not None:
        dt = pendulum.parse(last_sold)
        if not dt.year == 2020:
            return
    else:
        return

    upc = coalesce_null(input['ItemNum'])
    if upc is None:
        upc = "INVALID"
    internal_id = None
    if sku_counter.get(upc) is None:
        sku_counter[upc] = 1
    else:
        sku_counter[upc] += 1

    def is_valid_upc(val):
        for char in val:
            if not char.isdigit():
                return False
        return True

    if len(upc) < 5 or not is_valid_upc(upc):
        internal_id = f"biz_id_{upc}"
        upc = None
    elif not is_valid_upc(upc):
        internal_id = f"biz_id_{input['ItemNum']}"
        upc = None
    input['Internal_ID'] = internal_id
    if upc is not None and sku_counter[upc] > 1:
        duplicate_sku_ids.append(row_idx)

    price = 0.0
    if not input['Price'] is None:
        price = float(input['Price'])
    cost = 0.0
    if not input['Cost'] is None:
        cost = float(input['Cost'])

    margin_percentage = 0.0
    if price > 0.0 and cost > 0.0:
        margin_percentage = abs(price - cost) / statistics.mean([cost, price]) * 100
    if margin_percentage > 30:
        price += round((price / 100) * 7, 2)
        input['Tags'].append('high_margin')
    elif margin_percentage < 30:
        price += round((price / 100) * 9, 2)
        input['Tags'].append('low_margin')
    else:
        price += round((price / 100) * 9, 2)

    input['Margin_Percentage'] = margin_percentage
    input['Price'] = price
    input['Cost'] = cost

    name = input['ItemName'] + input['ItemName_Extra']
    input['Name'] = name

    department = coalesce_null(input['Dept_ID'])
    input['Department'] = department

    vendor = coalesce_null(input['Vendor_Number'])
    description = coalesce_null(input['Description_1'])

    properties = {"department": department, "vendor": vendor, "description": description}
    input['Properties'] = json.dumps(properties)

    output[input['Transform_ID']] = input


def coalesce_null(val):
    """Reduce any empty string or missing value to None"""
    if val == "" or val == 'NULL' or val == 'NONE' or val == 'Null':
        return None
    else:
        return val


def sanitize_headers(headers):
    """ Append a counter to duplicate headers to make them unique """
    counter = Counter(headers)
    seen = {}
    new_headers = []

    for h in headers:
        if counter[h] > 1:
            if h not in seen:
                new_headers.append(h)
                seen[h] = 0
            else:
                seen[h] = seen.get(h) + 1
                new_headers.append(f"{h}_{seen[h]}")
        else:
            new_headers.append(h)

    return new_headers


def transform_data(extracted_data):
    reader = csv.DictReader(extracted_data, delimiter='|')
    sanitized_headers = sanitize_headers(reader.fieldnames)
    reader = csv.DictReader(extracted_data, delimiter='|', fieldnames=sanitized_headers)
    next(reader)  # remove the row with dashes
    duplicate_sku_idx = []
    sku_counter = {}

    """
        This should change to a single dict for the final output. 
        We only needed the idx to perform the duplicate sku mapping
    """
    out = collections.defaultdict(dict)
    for idx, row in enumerate(reader):
        transform_line(idx, row, duplicate_sku_idx, sku_counter, out)
    for idx, row in out.items():
        if idx in duplicate_sku_idx:
            row['Tags'].append('duplicated_sku')

        for key, val in row.items():
            row[key] = coalesce_null(val)
    return out


http = urllib3.PoolManager()
response = http.request("GET", initial_html_file)
endpoint = build_s3_endpoint(response.data)
extracted = fetch_s3_data(endpoint)
transformed = transform_data(extracted)
for row in transformed.values():
    data = json.dumps(row)
    print(f"Writing row: {row}")
    http.request("POST",
                 url="http://localhost:3001/inventory_units.json",
                 headers={'Content-Type': 'application/json'},
                 body=data)

print("Finished!")

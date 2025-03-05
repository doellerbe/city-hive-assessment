import collections
import csv
import json
import statistics
from typing import Dict

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


def process_line(row_idx, data, duplicate_sku_ids, sku_counter, out):
    data['Transform_ID'] = row_idx
    data['Tags'] = set([])

    last_sold = coalesce_null(data['Last_Sold'])
    if last_sold is not None:
        dt = pendulum.parse(last_sold)
        if not dt.year == 2020:
            return
    else:
        return

    upc = coalesce_null(data['ItemNum'])
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
        internal_id = f"biz_id_{data['ItemNum']}"
        upc = None
    data['Internal_ID'] = internal_id
    if upc is not None and sku_counter[upc] > 1:
        duplicate_sku_ids.add(row_idx)

    price = 0.0
    if not data['Price'] is None:
        price = float(data['Price'])
    cost = 0.0
    if not data['Cost'] is None:
        cost = float(data['Cost'])

    margin_percentage = 0.0
    if price > 0.0 and cost > 0.0:
        margin_percentage = abs(price - cost) / statistics.mean([cost, price]) * 100
    if margin_percentage > 30:
        price += round((price / 100) * 7, 2)
        data['Tags'].add('high_margin')
    elif margin_percentage < 30:
        price += round((price / 100) * 9, 2)
        data['Tags'].add('low_margin')
    else:
        price += round((price / 100) * 9, 2)

    data['Margin_Percentage'] = margin_percentage
    data['Price'] = price
    data['Cost'] = cost

    name = data['ItemName'] + data['ItemName_Extra']
    data['Name'] = name

    department = coalesce_null(data['Dept_ID'])
    data['Department'] = department

    vendor = coalesce_null(data['Vendor_Number'])
    description = coalesce_null(data['Description_1'])

    properties = {"department": department, "vendor": vendor, "description": description}
    data['Properties'] = json.dumps(properties)

    out[data['Transform_ID']] = data


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


# http = urllib3.PoolManager()
# response = http.request("GET", initial_html_file)
# endpoint = build_s3_endpoint(response.data)
# fetch_s3_data(endpoint)


with open(local_file_path, 'r') as in_file:
    reader = csv.DictReader(in_file, delimiter='|')
    sanitized_headers = sanitize_headers(reader.fieldnames)
    reader = csv.DictReader(in_file, delimiter='|', fieldnames=sanitized_headers)
    next(reader)  # remove the row with dashes

    duplicate_sku_idx = set([])
    sku_counter = {}
    transformed = collections.defaultdict(dict)
    for idx, row in enumerate(reader):
        process_line(idx, row, duplicate_sku_idx, sku_counter, transformed)

    for idx, row in transformed.items():
        if idx in duplicate_sku_idx:
            row['Tags'].add('duplicated_sku')

        # clean up empty, null, or none strings
        for key, val in row.items():
            row[key] = coalesce_null(val)
    print(transformed)


print("Finished!")

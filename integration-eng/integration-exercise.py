import csv
import json
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


def process_line(line):

    if len(line) > 10:
        return {
            'upc': line.get('ItemNum'),
            'price': line.get('Price'),
            'quantity': line.get('Quantity'),
            'dept_id': line.get('Dept_ID')
        }


def sanitize_headers(headers):
    """ Append a counter to duplicate headers to make them unique """
    counter = Counter(headers)
    seen = {}
    new_headers = []

    for h in headers:
        print(f"HEADER: {h}")
        print(counter[h])
        if counter[h] > 1:
            print(f"Adding {h} to SEEN")
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

    for row in reader:
        print(row.get('ItemNum'))


print("Finished!")

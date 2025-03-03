import csv
import json

import urllib3
from bs4 import BeautifulSoup


# 1. Using requests or any other HTTP library, grab the file HTML from: https://bitbucket.org/cityhive/jobs/src/master/integration-eng/integration-entryfile.html
# 2. Then, parse the URL for the csv file located in the S3 bucket (as part of the script, not by hand)
# 3. Make a GET request to Amazon's S3 with the details from #2 and save the to `local_file_path`

initial_html_file = "https://bitbucket.org/cityhive/jobs/raw/47fb39b480e7e5b588a5f57e6e068cea9fcbfcb2/integration-eng/integration-entryfile.html"
local_file_path = "path-to-exported-file"


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


http = urllib3.PoolManager()
response = http.request("GET", initial_html_file)
endpoint = build_s3_endpoint(response.data)
print(endpoint)

# json_data = build_s3_endpoint(sample_html)
# print(json.dumps(json_data, indent=4))


# def process_line(line):
#     if len(line) > 10:
#         return {
#             'upc': line[0],
#             'price': line[4],
#             'quantity': line[5]
#         }
#
#
# with open(local_file_path, 'r') as in_file:
#     reader = csv.reader(in_file, delimiter='|')
#     for line in reader:
#         l = process_line(line)
#         if l: print(l)


print("Finished!")

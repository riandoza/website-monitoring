import re
import time
import requests
import csv
import validators


def rm_https(url: str):
    if not validators.url(url):
        return url
    return re.sub(r'http(s)?(:)?(//)?|(//)?(www\.)?', "", url, flags=re.MULTILINE)


def check_link(url: str):
    retries = 2
    message = "Something Error"
    for i in range(retries):
        try:
            response = requests.get(url, allow_redirects=False, timeout=5)
            if response.status_code == 200:
                message = "working fine."
                return url, response.status_code, 'https', message
            elif response.status_code == 301 or response.status_code == 302:
                if rm_https(url) in response.headers['Location']:
                    message = "working fine."
                    return response.headers['Location'], 200, 'https', message
                else:
                    message = f"redirecting to {response.headers['Location']}."
                    return response.headers['Location'], response.status_code, 'https', message
            else:
                return 'Error', response.status_code, 'https', message
        except requests.exceptions.SSLError:
            url = url.replace("https", "http")
            try:
                response = requests.get(url, allow_redirects=False, timeout=10)
                if response.status_code == 200:
                    message = "working fine over http."
                    return url, response.status_code, 'http', message
                elif response.status_code == 301 or response.status_code == 302:
                    if rm_https(url) in response.headers['Location']:
                        message = "working fine over http."
                        return response.headers['Location'], 200, 'http', message
                    else:
                        message = f"redirecting to {response.headers['Location']} over http."
                        return response.headers['Location'], response.status_code, 'http', message
                else:
                    return 'Error', response.status_code, 'http', message
            except requests.exceptions.RequestException as e:
                message = f"Error occurred : {e}"
                return 'Error', 500, 'https', message
        except requests.exceptions.ConnectionError:
            if i < retries - 1:
                print(f"Connection error occurred while checking {url}. Retrying in 1 second...")
                time.sleep(1)
            else:
                message = "Max retries exceeded"
                return 'Error', 502, 'https', message
        except requests.exceptions.Timeout:
            message = "Timeout occurred"
            return 'Error', 408, 'https', message


try:
    with open('websites.csv', mode='r') as file:
        csv_reader = csv.DictReader(file)
        rows = []
        counter = 0
        for row in csv_reader:
            url = row['Domain']
            if not validators.domain(url) and not validators.url(url):
                continue
            if not url.startswith('http'):
                url = f"https://{url}"
            new_url, code, schema, message = check_link(url)
            r = {'Domain': row['Domain'],
                 'Url': new_url,
                 'Code': code,
                 'Schema': schema,
                 'Message': message}
            rows.append(r)
        if rows:
            with open('websites.csv', mode='w') as file:
                fieldnames = ['Domain', 'Url', 'Code', 'Schema', 'Message']
                csv_writer = csv.DictWriter(file, fieldnames=fieldnames)
                csv_writer.writerow(dict((heads, heads) for heads in fieldnames))
                csv_writer.writerows(rows)

    print("Done!")
except Exception as e:
    print(f"An error occurred: {e}")

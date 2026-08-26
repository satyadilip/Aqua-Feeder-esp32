import urllib.request
import re

html = urllib.request.urlopen('http://lorawan-telemetry-stack-webhostingbucket-djy9frtf8y6f.s3-website-us-east-1.amazonaws.com/').read().decode('utf-8')
urls = re.findall(r'https?://[^\s"\'<>]+', html)
print("Found URLs:", urls)

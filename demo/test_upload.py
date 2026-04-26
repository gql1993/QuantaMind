import http.client
import os

boundary = "----QuantaMindBoundary"
filename = "test.csv"
content = b"freq_ghz,T1_us\n5.01,45.2\n4.98,38.1"

body = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
    f"Content-Type: application/octet-stream\r\n\r\n"
).encode() + content + (
    f"\r\n--{boundary}\r\n"
    f'Content-Disposition: form-data; name="project_id"\r\n\r\n'
    f"default\r\n"
    f"--{boundary}--\r\n"
).encode()

c = http.client.HTTPConnection("127.0.0.1", 18789, timeout=10)
c.request("POST", "/api/v1/library/upload", body, {"Content-Type": f"multipart/form-data; boundary={boundary}"})
r = c.getresponse()
print("Status:", r.status)
print("Body:", r.read().decode()[:500])
c.close()

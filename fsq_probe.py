import subprocess, duckdb, time
for b in ['s3://fsq-os-places-us-east-1/release/', 's3://fsq-os-places-us-east-1/']:
    print(b, subprocess.run(['aws', 's3', 'ls', b, '--no-sign-request'], capture_output=True, text=True), flush=True)

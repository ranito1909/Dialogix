from google.oauth2 import service_account
import os
import tempfile
from google.cloud import storage
import pandas as pd
import numpy as np
from jinja2 import Environment, FileSystemLoader

os.environ['GOOGLE_STORAGE_ACCOUNT_FILE'] = "google_dialogix_api_keys.json"

def check_gcs_directory(domain_name):
    bucket_name="dialogix-bucket1"
    service_account_file = os.environ.get("GOOGLE_STORAGE_ACCOUNT_FILE")
  
    # Initialize Google Cloud Storage client
    credentials = service_account.Credentials.from_service_account_file(service_account_file)
    client = storage.Client(credentials=credentials)

    # Get the specified bucket
    bucket = client.bucket(bucket_name)

    # Specify the directory name (object prefix) based on the domain
    directory_name = f"{domain_name}/"

    # Check if the directory exists by listing objects with the specified prefix
    blobs = list(bucket.list_blobs(prefix=directory_name))
    return blobs
def upload_temp_directory(tmp_dir,folder_name):
  """
  Uploads all files from a temporary directory to Google Cloud Storage.

  Args:
    tmp_dir: The path to the temporary directory containing the files.

  Returns:
    None
  """
  

  # Use environment variables
  service_account_file = os.environ.get("GOOGLE_STORAGE_ACCOUNT_FILE")
  # Check if environment variables are set
  if not service_account_file or not folder_name:
    raise ValueError("Missing required environment variables: GOOGLE_STORAGE_ACCOUNT_FILE, FOLDER_NAME")

  # Initialize Google Cloud Storage client
  credentials = service_account.Credentials.from_service_account_file(service_account_file)
  client = storage.Client(credentials=credentials)

  # Create the desired folder name in the bucket
  bucket = client.bucket("dialogix-bucket1")
  # Iterate through files and upload them with the folder name prefix
  for filename in os.listdir(tmp_dir):
    file_path = os.path.join(tmp_dir, filename)
    destination_blob_name = f"{folder_name}/{filename}"
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(file_path)
    print(f"Uploaded file: {filename}")
def upload_html_2gcd(url, userOpenLine, botName, output_directory,UserId):
    # Set up Google Cloud Storage client
    service_account_file = os.environ.get("GOOGLE_STORAGE_ACCOUNT_FILE")
  # Check if environment variables are set
  # Initialize Google Cloud Storage client
    credentials = service_account.Credentials.from_service_account_file(service_account_file)
    storage_client = storage.Client(credentials=credentials)

    bucket_name = "dialogix-bucket1"
    template_path_gcs = "template.html"  # Update with your actual path on GCS

    # Download the template from Google Cloud Storage
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(template_path_gcs)
    template_content = blob.download_as_text()
    # Create a Jinja2 environment
    env = Environment(loader=FileSystemLoader('.'))
    # Load the template from the downloaded content
    template = env.from_string(template_content)

    # Render the template with variables 
    rendered_html = template.render(url=url, userOpenLine=userOpenLine, botName=botName)

    # Upload the rendered file to the specified directory
    output_blob_name = f"{output_directory}/{UserId}/{output_directory}.html"
    output_blob = bucket.blob(output_blob_name)
    output_blob.upload_from_string(rendered_html,content_type='text/html')
    
    print(f"Rendered HTML uploaded to: gs://{bucket_name}/{output_blob_name}")
    return f"Rendered HTML uploaded to: gs://{bucket_name}/{output_blob_name}"





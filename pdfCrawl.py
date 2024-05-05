import os
import PyPDF2
import requests
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}


def download_pdf(url,debug = False):

    # Send an HTTP GET request to the URL
    response = requests.get(url,headers=headers)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Get the content of the response
        pdf_content = response.content

        # Specify the local file path where you want to save the PDF
        local_pdf_filename = "tempPDF.pdf"

        # Save the PDF content to the local file
        with open(local_pdf_filename, "wb") as pdf_file:
            pdf_file.write(pdf_content)

        if debug: print(f"PDF downloaded and saved as {local_pdf_filename}")
    else:
        print(f"Failed to download PDF. Status code: {response.status_code}")


def pdf_to_txt(pdf_file_path, f,debug = False):

    with open(pdf_file_path, "rb") as pdf_file:
        # Create a PDF reader object
        pdf_reader = PyPDF2.PdfReader(pdf_file)

        # Initialize an empty string to store the extracted text
        extracted_text = ""

        # Iterate through each page of the PDF
        for page_num in range(len(pdf_reader.pages)):
            # Get the text content of the page
            page = pdf_reader.pages[page_num]
            page_text = page.extract_text()

            # Append the page text to the extracted_text string
            extracted_text += page_text

        # Close the PDF file
        pdf_file.close()

    # Specify the path for the TXT file where you want to save the extracted text
    f.write(extracted_text)
    if debug:
        print(f"Extracted text saved to {f}")


def delete_file(file_path,debug = False):
    # Check if the file exists before attempting to delete it
    if os.path.exists(file_path):
        # Delete the file
        os.remove(file_path)
        if debug: print(f"File {file_path} has been deleted.")
    else:
        print(f"File {file_path} does not exist.")


def is_pdf_url(url):
    # Split URL into path and extension
    path = os.path.splitext(url)[0]
    ext = os.path.splitext(url)[1]

    # Check if the extension is .pdf case-insensitive
    if ext.lower() == '.pdf':
        return True
    return False

import streamlit as st
import tempfile
import os
from pathlib import Path
from mistralai import Mistral
from mistralai import DocumentURLChunk, ImageURLChunk, TextChunk
from mistralai.models import OCRResponse
import json
from dotenv import load_dotenv

# Load environment variables from .env file (local development)
load_dotenv()

# Get API key from environment variables (works for both local and cloud deployment)
api_key = os.getenv('MISTRAL_API_KEY')
if not api_key:
    st.error("""
        Missing MISTRAL_API_KEY in environment variables. 
        Local users: Please check your .env file
        Cloud deployment: Ensure you've set up the secret in Streamlit Cloud
    """)
    st.stop()

# Initialize Mistral client
client = Mistral(api_key=api_key)

def replace_images_in_markdown(markdown_str: str, images_dict: dict) -> str:
    """Replace image placeholders with base64 encoded images in markdown."""
    for img_name, base64_str in images_dict.items():
        markdown_str = markdown_str.replace(f"![{img_name}]({img_name})", f"![{img_name}]({base64_str})")
    return markdown_str

def get_combined_markdown(ocr_response: OCRResponse) -> str:
    """Combine markdown from all pages with their respective images."""
    markdowns: list[str] = []
    for page in ocr_response.pages:
        image_data = {}
        for img in page.images:
            image_data[img.id] = img.image_base64
        markdowns.append(replace_images_in_markdown(page.markdown, image_data))

    return "\n\n".join(markdowns)

def process_file_to_markdown(file_path: str, file_type: str) -> str:
    """
    Convert PDF or image file to Markdown using Mistral OCR API
    Args:
        file_path (str): Path to the uploaded file
        file_type (str): Type of file ('pdf' or 'image')
    Returns:
        str: Converted markdown text
    """
    try:
        # Convert string path to Path object
        file = Path(file_path)
        
        # Upload file to Mistral
        uploaded_file = client.files.upload(
            file={
                "file_name": file.stem,
                "content": file.read_bytes(),
            },
            purpose="ocr",
        )

        # Get signed URL
        signed_url = client.files.get_signed_url(file_id=uploaded_file.id, expiry=1)

        # Process the file with OCR
        if file_type == 'pdf':
            response = client.ocr.process(
                document=DocumentURLChunk(document_url=signed_url.url),
                model="mistral-ocr-latest",
                include_image_base64=True
            )
        else:  # image
            response = client.ocr.process(
                document=ImageURLChunk(image_url=signed_url.url),
                model="mistral-ocr-latest",
                include_image_base64=True
            )

        # Convert to markdown
        markdown_text = get_combined_markdown(response)
        return markdown_text

    except Exception as e:
        st.error(f"Error in file conversion: {str(e)}")
        return None

def main():
    st.title("Document to Markdown Converter")
    st.write("Upload a PDF or image file and convert it to Markdown format")

    # File type selector
    file_type = st.radio(
        "Select file type",
        ["PDF", "Image"],
        horizontal=True
    )

    # File uploader with appropriate file types
    accepted_types = ['pdf'] if file_type == "PDF" else ['png', 'jpg', 'jpeg', 'tiff', 'bmp']
    file_type_label = "PDF file" if file_type == "PDF" else "image file"
    
    uploaded_file = st.file_uploader(f"Choose a {file_type_label}", type=accepted_types)

    if uploaded_file is not None:
        # Create a temporary file to store the uploaded file
        file_extension = '.pdf' if file_type == "PDF" else f".{uploaded_file.name.split('.')[-1]}"
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name

        try:
            with st.spinner('Converting to Markdown...'):
                # Convert file to Markdown
                markdown_text = process_file_to_markdown(
                    tmp_file_path,
                    'pdf' if file_type == "PDF" else 'image'
                )

            if markdown_text:
                # Display the converted markdown
                st.subheader("Converted Markdown:")
                st.markdown(markdown_text)  # Changed from text_area to markdown to render the content
                
                # Also show raw markdown
                st.subheader("Raw Markdown:")
                st.text_area("Raw Markdown Output", markdown_text, height=300)

                # Add a download button for the markdown
                st.download_button(
                    label="Download Markdown",
                    data=markdown_text,
                    file_name="converted.md",
                    mime="text/markdown"
                )
            else:
                st.error("Conversion failed. Please check the file.")

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

        finally:
            # Clean up the temporary file
            os.unlink(tmp_file_path)

if __name__ == "__main__":
    main() 
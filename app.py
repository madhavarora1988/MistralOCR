import streamlit as st
import tempfile
import os
from pathlib import Path
from mistralai import Mistral
from mistralai import DocumentURLChunk, ImageURLChunk, TextChunk # TextChunk not used in this snippet but good to keep if Mistral changes
from mistralai.models import OCRResponse
import json # Not explicitly used in this snippet, can be removed if not needed elsewhere
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

def process_file_to_markdown(file_path: str, file_type_for_api: str) -> str:
    """
    Convert PDF or image file to Markdown using Mistral OCR API
    Args:
        file_path (str): Path to the temporary file
        file_type_for_api (str): Type of file for API call ('pdf' or 'image')
    Returns:
        str: Converted markdown text
    """
    try:
        # Convert string path to Path object
        file = Path(file_path)
        
        # Upload file to Mistral
        uploaded_file_mistral = client.files.upload(
            file={
                "file_name": file.stem, # Use stem of the temp file for Mistral's reference
                "content": file.read_bytes(),
            },
            purpose="ocr",
        )

        # Get signed URL
        signed_url = client.files.get_signed_url(file_id=uploaded_file_mistral.id, expiry=1) # Short expiry as it's used immediately

        # Process the file with OCR
        if file_type_for_api == 'pdf':
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
    st.write("Convert a PDF, image file, or camera capture to Markdown format.")

    # Input method selector
    input_method = st.radio(
        "Choose an input method:",
        ("Upload PDF", "Upload Image File", "Take a Picture (Camera)"),
        horizontal=True,
        key="input_method_selector"
    )

    uploaded_file_streamlit = None  # To store the file object from Streamlit uploader/camera
    file_type_for_processing = None # This will be 'pdf' or 'image' for process_file_to_markdown

    if input_method == "Upload PDF":
        uploaded_file_streamlit = st.file_uploader(
            "Choose a PDF file",
            type=['pdf'],
            key="pdf_uploader"
        )
        if uploaded_file_streamlit:
            file_type_for_processing = 'pdf'
    elif input_method == "Upload Image File":
        uploaded_file_streamlit = st.file_uploader(
            "Choose an image file",
            type=['png', 'jpg', 'jpeg', 'tiff', 'bmp'],
            key="image_uploader"
        )
        if uploaded_file_streamlit:
            file_type_for_processing = 'image'
    elif input_method == "Take a Picture (Camera)":
        # camera_input returns an UploadedFile object or None
        camera_photo = st.camera_input("Take a picture", key="camera_input")
        if camera_photo:
            uploaded_file_streamlit = camera_photo
            file_type_for_processing = 'image' # Camera always produces an image

    if uploaded_file_streamlit is not None and file_type_for_processing is not None:
        # Determine file extension for temp file
        original_file_name = uploaded_file_streamlit.name # e.g., "my_doc.pdf" or "camera_input.png"
        file_extension = Path(original_file_name).suffix

        # Robust fallback for extension if name doesn't have one
        if not file_extension:
            if uploaded_file_streamlit.type == "application/pdf":
                file_extension = ".pdf"
            elif uploaded_file_streamlit.type == "image/png":
                file_extension = ".png"
            elif uploaded_file_streamlit.type == "image/jpeg":
                file_extension = ".jpg"
            elif uploaded_file_streamlit.type == "image/bmp":
                file_extension = ".bmp"
            elif uploaded_file_streamlit.type == "image/tiff":
                file_extension = ".tiff"
            else: 
                st.warning(f"Could not reliably determine file extension for {original_file_name} (type: {uploaded_file_streamlit.type}). Using '.tmp'.")
                file_extension = ".tmp" # Generic extension if all else fails
        
        # Create a temporary file to store the uploaded content
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
            tmp_file.write(uploaded_file_streamlit.getvalue())
            tmp_file_path = tmp_file.name

        try:
            with st.spinner('Converting to Markdown...'):
                # Convert file to Markdown
                markdown_text = process_file_to_markdown(
                    tmp_file_path,
                    file_type_for_processing 
                )

            if markdown_text:
                st.subheader("Converted Markdown:")
                st.markdown(markdown_text)
                
                st.subheader("Raw Markdown:")
                st.text_area("Raw Markdown Output", markdown_text, height=300)

                # Add a download button for the markdown
                download_file_name = f"{Path(original_file_name).stem}_converted.md"
                st.download_button(
                    label="Download Markdown",
                    data=markdown_text,
                    file_name=download_file_name,
                    mime="text/markdown"
                )
            else:
                st.error("Conversion failed. Please check the file or camera input.")

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

        finally:
            # Clean up the temporary file
            os.unlink(tmp_file_path)

if __name__ == "__main__":
    main()
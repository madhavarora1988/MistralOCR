# Document to Markdown Converter

A Streamlit application that converts PDF documents and images to Markdown format using Mistral OCR API.

## Local Setup

1. Clone the repository:
```bash
git clone <your-repository-url>
cd <repository-name>
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory with your Mistral API key:
```bash
MISTRAL_API_KEY=your_api_key_here
```

4. Run the application:
```bash
streamlit run app.py
```

## Deployment on Streamlit Cloud

1. Push your code to GitHub (ensure `.env` is not included)

2. Go to [Streamlit Cloud](https://streamlit.io/cloud)

3. Click on "New app" and select your repository

4. Configure the deployment:
   - Set the Python version (3.9 or higher recommended)
   - Set the main file path as `app.py`
   - In the "Advanced settings" section, add your secrets:
     - Key: `MISTRAL_API_KEY`
     - Value: Your actual Mistral API key

5. Click "Deploy"

Your app will be deployed and accessible via a public URL.

### Managing Secrets in Streamlit Cloud

To update or manage secrets after deployment:
1. Go to your app settings
2. Click on "Secrets"
3. Add or modify the secrets in TOML format:
```toml
MISTRAL_API_KEY = "your_api_key_here"
```

## Features

- Convert PDF documents to Markdown
- Convert images (PNG, JPG, JPEG, TIFF, BMP) to Markdown
- View both rendered and raw Markdown output
- Download converted Markdown files

## Environment Variables

The application requires the following environment variable:

- `MISTRAL_API_KEY`: Your Mistral API key for OCR services

You can obtain a Mistral API key from [Mistral AI's website](https://mistral.ai/).

## Security Notes

- Never commit your `.env` file to version control
- Keep your API key secure and don't share it publicly
- The `.env` file is included in `.gitignore` to prevent accidental commits
- When deploying, always use Streamlit Cloud's secrets management
- Monitor your API usage and set up appropriate rate limiting if needed 
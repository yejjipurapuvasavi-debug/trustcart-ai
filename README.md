# TrustCart AI — Web Prototype

## Requirements
- Python 3.10+
- VS Code
- Internet is only needed to install packages and load the Google Fonts in the UI; the sample backend runs locally.

## Start the backend
Open the VS Code terminal in this folder and run:

```bash
python -m venv .venv
```

Windows PowerShell:
```powershell
.\.venv\Scripts\Activate.ps1
```

Windows Command Prompt:
```bat
.venv\Scripts\activate.bat
```

Then:
```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

## Open the frontend
Open `index.html` in a browser (preferably using the VS Code Live Server extension).

The API runs at `http://127.0.0.1:8000`.

## Demo scenarios
- Ask: `What is the price of the AeroRun Blue Running Shoe?`
- Ask: `What is the price of blue running shoes?`
- Ask: `Do you sell iPhones?`
- Ask: `What is your return policy?`
- Ask: `Show me cotton products`, then `Under ₹2,000`

## Important limitations
- Product and policy records are illustrative sample data.
- This is not connected to the competition's 5,000-product catalogue, supplied models, hidden test questions, or `evaluate.py`.
- Latency is measured locally, but token cost is not available until the provided model is integrated.
- Do not claim official evaluation scores or real inventory accuracy from this demo.
- CORS is permissive for local development only; restrict allowed origins before deployment.

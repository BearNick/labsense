# Labsense

AI-powered analysis of laboratory reports (PDF).

Upload your lab report → get structured markers → clinical interpretation → lifestyle insights.

## Try it

https://labsense.app

## What it does

Labsense helps users understand laboratory reports by extracting markers from PDF files and generating a structured, medically cautious interpretation.

Current features:
- PDF lab report upload
- Marker extraction
- Reference range detection
- Risk/status summary
- AI interpretation
- Lifestyle recommendations
- EN / RU / ES interface
- Stripe and PayPal support

## Disclaimer

Labsense provides informational analysis only.  
It is not a diagnosis and does not replace medical advice.

## Structure

- `frontend/`: Next.js App Router frontend with Tailwind UI.
- `backend/`: Python parser, interpreter, clinical consistency logic, and tests.
- `api/`: FastAPI upload and analysis API used by the frontend.

## Backend entrypoint

```bash
cd /opt/labsense
uvicorn api.main:app --host 127.0.0.1 --port 8000

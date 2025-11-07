# PDF2AudioBook Frontend

This is the frontend for the PDF2AudioBook SaaS platform.

## Getting Started

First, install the dependencies:

```bash
npm install
```

Then, run the development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Environment Variables

Create a `.env.local` file in the root of the `frontend` directory and add the following environment variables:

```
# Point to your deployed backend (Render)
NEXT_PUBLIC_API_URL=https://pdf2audiobook.xyz

# Clerk (already configured in the shared pdf2audiobook.env used by Render)
# For local development, copy the relevant values:
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...

# Optional: enable local/dev testing mode to bypass payment gating
# (Frontend will treat this as a flag to show and test all payment flows without real charges)
NEXT_PUBLIC_DEV_BYPASS_PAYMENTS=true
```

The frontend will automatically route requests to the versioned API (`/api/v1`) under `NEXT_PUBLIC_API_URL`, so you should provide the base domain only (e.g. `https://pdf2audiobook.xyz` or your local `http://localhost:8000`).

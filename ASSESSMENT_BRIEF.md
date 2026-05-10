# Sunbird AI Internship Assessment Exercise

This assessment consists of 3 parts:
- Programming exercises.
- Build a simple command line app using the Sunbird AI API.

## Getting started
- Fork this repository to create your own copy. ([More info about forking a repository](https://docs.github.com/en/get-started/quickstart/fork-a-repo))
- Clone your repository to access it locally: `git clone https://github.com/<your-username>/internship-assessment.git`. (Replace `<your-username>` with your Github username.)
- Change directory into the `internship-assessment` folder after cloning the repository.
- Create a python virtual environment: `python -m venv venv`
- Activate the virtual environment: 
  - Linux/Mac: `source venv/bin/activate`
  - Windows: `venv\Scripts\activate.bat`
- Install the required python packages: `pip install -r requirements.txt`
- Run the command `pytest`. (The tests should be failing, it's your task to make them pass. See below for instructions)

## Part 1: Programming exercises
There are 2 programming exercises designed to test your competency with the python programming language. 

You can find the starter code and task descriptions in the `exercises/basics.py` file in this repo.

Run the following command: `pytest`. You will see that all the tests are failing.

Your goal is to implement the 2 functions `collatz` and `distinct_numbers` to make the above failing tests pass.

You can keep running the `pytest` command to see which tests are still failing and fix your code accordingly.

## Part 2: Build a GenAI Application with Sunbird AI

Build a small **Generative AI web application** powered by Sunbird AI's [Sunflower LLM](https://sunflower.sunbird.ai/) and the [Sunbird AI API](https://docs.sunbird.ai/introduction).

The application should let a user provide either **text** or an **audio file**, then run the input through this pipeline:

1. **Input** — accept either typed/pasted text **or** an uploaded audio file.
2. **Transcribe (audio only)** — if the input is audio, transcribe it to text using Sunbird's Speech-to-Text API.
3. **Summarise** — summarise the text (typed input or transcribed text) using the Sunflower LLM.
4. **Translate** — translate the summary into a chosen Ugandan local language (Luganda, Runyankole, Ateso, Lugbara, or Acholi) using the Sunflower LLM.
5. **Synthesise speech** — generate an audio clip of the translated summary using Sunbird's Text-to-Speech API.
6. **Output** — display the original text, the summary, the translated summary, and the generated audio (playable in the UI).

### Tech stack requirements

- **Backend:** Python (you may use FastAPI, Flask, or call the Sunbird API directly from your frontend framework — your choice).
- **Frontend:** one of [Gradio](https://www.gradio.app/), [Streamlit](https://streamlit.io/), or [Next.js](https://nextjs.org/docs).
- **APIs:** all AI capabilities **must** come from Sunbird AI. Do not call OpenAI, Anthropic, or any other model provider for the core pipeline.

### Sunbird AI API references

Read these docs carefully before implementing — they show the exact request/response shapes and authentication you'll need:

- **Speech-to-Text (STT):** https://docs.sunbird.ai/guides/speech-to-text
- **Text-to-Speech (TTS):** https://docs.sunbird.ai/guides/text-to-speech
- **Summarisation & Translation (Sunflower Simple Inference):** https://docs.sunbird.ai/guides/sunflower-chat
- **Full API reference:** https://docs.sunbird.ai/api-reference/introduction

You will need a Sunbird AI API token. Sign up and obtain one from the [Sunbird AI API portal](https://api.sunbird.ai/), then store it in a `.env` file as `SUNBIRD_API_TOKEN` (or equivalent). **Never commit your token to git.**

### Functional requirements

- Input switching: the UI must clearly let the user choose between text input and audio upload.
- Audio constraint: reject audio files longer than **5 minutes** with a clear error message.
- Language picker: allow the user to select the target local language for the translated summary.
- Visible intermediate results: the UI should show the transcript (when audio is used), the summary, the translated summary, and the generated audio player — not just the final audio.
- Sensible error handling: surface API failures to the user instead of silently failing.

### Suggested project layout

```
.
├── app.py                  # entry point (Gradio/Streamlit) OR Next.js app/
├── backend/
│   ├── sunbird_client.py   # thin wrapper around Sunbird API endpoints
│   ├── pipeline.py         # orchestrates STT -> summarise -> translate -> TTS
│   └── ...
├── requirements.txt        # or package.json if Next.js + Python backend
├── .env.example            # document required env vars (no real secrets)
└── README.md               # see Part 3
```

## Part 3: Documentation & Deployment

A working app you can't run isn't a working app. For this part, you must (a) document your project so a reviewer can run it locally, and (b) deploy it publicly so we can try it without setting anything up.

### README requirements

Replace this README (or add a `PROJECT_README.md` next to it) with documentation that includes:

- **Project description** — one paragraph on what the app does.
- **Architecture overview** — a short diagram or bullet list of the pipeline (input → STT → summarise → translate → TTS → output) and which Sunbird endpoints handle each step.
- **Local setup** — exact, copy-pasteable steps to clone, install dependencies, configure environment variables (with a `.env.example` reference), and run the app locally.
- **Environment variables** — list every required variable and what it does.
- **Usage** — a short walkthrough showing the app being used end-to-end (screenshots are encouraged).
- **Deployed link** — a public URL where reviewers can try the app.
- **Known limitations** — anything that doesn't work, or constraints (e.g. 5-minute audio cap, supported languages).

### Deployment

Deploy your app to a free hosting provider that fits your stack. Pick one:

#### Option A — Hugging Face Spaces (recommended for Gradio/Streamlit)

1. Create a free account at https://huggingface.co/join.
2. Create a new Space: https://huggingface.co/new-space — choose **Gradio** or **Streamlit** as the SDK and a public visibility.
3. Add your Sunbird API token as a Space secret: Space settings → **Variables and secrets** → **New secret** → name it `SUNBIRD_API_TOKEN`.
4. Push your code to the Space's git repo:
   ```bash
   git remote add space https://huggingface.co/spaces/<your-username>/<your-space-name>
   git push space main
   ```
5. Hugging Face will build and deploy automatically. Confirm your `requirements.txt` lists every Python dependency and that your entry file matches the SDK convention (`app.py` for both Gradio and Streamlit).

Reference: https://huggingface.co/docs/hub/spaces-overview

#### Option B — Vercel (recommended for Next.js + Python backend)

1. Create a free account at https://vercel.com/signup and install the CLI: `npm i -g vercel@latest`.
2. From your project root, link the project: `vercel link`.
3. Add your Sunbird API token as an environment variable for all environments:
   ```bash
   vercel env add SUNBIRD_API_TOKEN
   ```
   (You'll be prompted to select Development, Preview, and Production — select all that apply.)
4. Pull the env vars locally for development: `vercel env pull .env.local`.
5. Deploy:
   - Preview: `vercel`
   - Production: `vercel --prod`
6. If you have a Python backend (FastAPI/Flask), put it under an `api/` directory or a separate Python service — Vercel runs Python via Fluid Compute. See https://vercel.com/docs/functions/runtimes/python.

Reference: https://vercel.com/docs/getting-started-with-vercel

### Submission

Your final submission must include:

- A pull request (or repository link) with all your code.
- An updated README that meets the requirements above.
- **A working deployed link** that we can open and use end-to-end with at least one test input.


# CAA Writing Space

A Streamlit research tool for studying AI Cognitive Augmentation Agents (CAA) in student essay writing. The app compares a **Thinking Partner** (which guides reasoning without writing content) against a standard **Writing Helper** (a normal AI assistant), measuring effects on essay quality and reflection.

## Purpose

This tool supports a study on whether an AI that augments thinking, rather than providing answers, leads to better student essays and deeper reasoning. It is built around three cognitive augmentation functions: memory cueing, analogy generation, and reflection prompting.

## How it works

Participants are assigned to one of two groups:

- **Writing Helper (control):** a standard AI assistant that answers questions and helps write, similar to a general chatbot.
- **Thinking Partner (experimental):** the CAA. It never writes the essay, gives arguments, or states opinions. It asks questions, offers analogies, connects the student's earlier points, and answers only brief factual questions. All in simple, plain English.

Both groups write on the same essay question and are logged identically. The only difference is the type of support they receive, which isolates the effect of the CAA design.

## Features

- Two support modes sharing one interface
- Three CAA functions: reflection prompting, analogy generation, and always-on memory cueing built into the chat
- A no-answer guardrail that keeps the Thinking Partner from writing essay content
- Simple, plain-English responses for accessibility across English levels
- Session logging: participant ID, group, full essay, full conversation, duration, word count, and interaction count
- Data saved to a Google Sheet (cloud) and a local text file (backup)

## Data collected

Each submission records: participant ID, assigned group, start time, time on task, essay word count, number of interactions, the full essay text, and the full conversation with the tool. Data is stored in a private Google Sheet.

## Tech stack

- **Streamlit** for the web interface
- **Groq** (Llama 3.1 8B) for the language model
- **gspread** and **google-auth** for Google Sheets storage
- Deployed on Streamlit Community Cloud

## Running locally

1. Create and activate a Python virtual environment.
2. Install dependencies: `pip install -r requirements.txt`
3. Add secrets to `.streamlit/secrets.toml` (Groq API key and Sheet ID) and place the Google service account key at `.streamlit/service_account.json`.
4. Run: `streamlit run app.py`

## Notes

- Secrets and the service account key are excluded from version control and never committed.
- The study measures essay quality and reflection, not memory or neurological effects. Recall-based measures are noted as future work.
- Group assignment is set by the researcher for each participant.

## Author

Nivedita Saha

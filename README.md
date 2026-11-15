# ChainCheck — Streamlit edition

A runnable Streamlit file-integrity checker. It stores each file's SHA-256 fingerprint in a linked block. The file contents stay off the ledger.

## Run on your computer

Requires Python 3.10 or newer.

On Windows, double-click `run_app.bat`. It installs the requirements and starts the app.

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Register a file and save the displayed record ID. Then upload the same file under Verify, with that ID. Modify a copy and verify it to demonstrate mismatch detection. `blockchain.json` is created beside the app when the first file is registered.

## Deploy to Streamlit Community Cloud

1. Extract this project ZIP.
2. Create a GitHub repository and upload the files in this folder (`streamlit_app.py` and `requirements.txt` should be at the repository root).
3. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
4. Choose **Create app**, select your repository and branch, and set the app file path to `streamlit_app.py`.
5. Choose **Deploy**. Community Cloud installs dependencies from `requirements.txt`.

Community Cloud needs the source in GitHub. The app writes its ledger to a local JSON file; hosted local files may be reset when the app restarts or is redeployed, so this version is suitable for a demo rather than durable records. Use an external database for persistent public use.

## How the chain works

Each block stores the file fingerprint, timestamp, record ID, and previous block hash. Its own hash is calculated from all those fields. The app checks every block and link before accepting verification. This is a local blockchain simulation; it does not include peer-to-peer networking or consensus.

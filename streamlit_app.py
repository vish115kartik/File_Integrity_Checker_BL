from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import streamlit as st


st.set_page_config(page_title="ChainCheck | File Integrity", page_icon="⛓️", layout="centered")
CHAIN_FILE = Path(__file__).resolve().parent / "blockchain.json"
MAX_FILE_BYTES = 16 * 1024 * 1024
ZERO_HASH = "0" * 64

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
.stApp{background:#f8f8fb;color:#202333}.block-container{max-width:920px;padding-top:2rem}
h1,h2,h3,p,li,label,[data-testid="stMarkdownContainer"]{color:#202333!important}
[data-testid="stCaptionContainer"] p{color:#55596b!important}
[data-testid="stWidgetLabel"] p{color:#303447!important;font-weight:600!important}
[data-testid="stFileUploader"] section,[data-testid="stFileUploader"] small{color:#303447!important}
[data-testid="stFileUploader"] button{color:#fff!important;background:#5142c2!important;border:0!important}
[data-testid="stTextInput"] input{color:#202333!important;background:#fff!important;border-color:#b9bbca!important}
[data-testid="stForm"]{color:#202333!important}
h1,h2,h3{font-family:Manrope,'DM Sans',sans-serif;letter-spacing:-.7px}h1{font-size:3rem!important;line-height:1.1!important}
.eyebrow{font:500 10px 'DM Mono',monospace;letter-spacing:1.2px;color:#8175d9;margin:1.2rem 0 .5rem}
.subtle{color:#777b8b;font-size:14px;max-width:600px;line-height:1.6;margin-bottom:1.7rem}
[data-testid="stVerticalBlockBorderWrapper"]{background:#fff;border-color:#e8e8ee!important;border-radius:14px;padding:1.15rem 1.25rem}
[data-testid="stFileUploader"]{background:#fcfcfe;border:1px dashed #d8d7e4;border-radius:10px;padding:.5rem}
.stButton button{border-radius:8px;font-weight:600;min-height:2.6rem}
.stButton button[kind="primary"]{background:#5142c2!important;color:#fff!important;border:0!important}
.stButton button[kind="secondary"]{background:#25283a!important;color:#fff!important;border:0!important}
code{font-family:'DM Mono',monospace!important}
</style>
""", unsafe_allow_html=True)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def block_hash(block: dict) -> str:
    payload = {key: value for key, value in block.items() if key != "block_hash"}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return digest(canonical)


def load_chain() -> list[dict]:
    if not CHAIN_FILE.exists():
        return []
    value = json.loads(CHAIN_FILE.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ValueError("The ledger file is not a valid list of blocks.")
    return value


def save_chain(chain: list[dict]) -> None:
    temporary = CHAIN_FILE.with_suffix(".tmp")
    temporary.write_text(json.dumps(chain, indent=2), encoding="utf-8")
    temporary.replace(CHAIN_FILE)


def check_chain(chain: list[dict]) -> tuple[bool, str]:
    previous = ZERO_HASH
    for index, block in enumerate(chain):
        if block.get("index") != index:
            return False, f"Block {index} has an invalid index."
        if block.get("previous_hash") != previous:
            return False, f"Block {index} has a broken previous-hash link."
        if block.get("block_hash") != block_hash(block):
            return False, f"Block {index} contents do not match its hash."
        previous = block["block_hash"]
    return True, "All block hashes and links are valid."


def register_file(name: str, content: bytes) -> dict:
    chain = load_chain()
    valid, detail = check_chain(chain)
    if not valid:
        raise ValueError(f"Cannot add a record: {detail}")
    block = {
        "index": len(chain),
        "record_id": uuid4().hex[:12].upper(),
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "filename": Path(name).name,
        "file_size": len(content),
        "file_hash": digest(content),
        "previous_hash": chain[-1]["block_hash"] if chain else ZERO_HASH,
    }
    block["block_hash"] = block_hash(block)
    chain.append(block)
    save_chain(chain)
    return block


st.markdown('<div class="eyebrow">● &nbsp; FILE INTEGRITY, MADE VISIBLE</div>', unsafe_allow_html=True)
st.title("Trust the file.\nVerify the fingerprint.")
st.markdown('<div class="subtle">Anchor a file’s SHA-256 fingerprint to a linked chain. Verify it again whenever you need proof it has not changed.</div>', unsafe_allow_html=True)

try:
    chain = load_chain()
    chain_valid, chain_message = check_chain(chain)
except (OSError, json.JSONDecodeError, ValueError) as exc:
    chain, chain_valid, chain_message = [], False, f"Could not read the ledger: {exc}"

col_a, col_b = st.columns(2, gap="medium")
with col_a:
    with st.container(border=True):
        st.caption("STEP 01")
        st.subheader("Register a file")
        st.write("Create a fingerprint record for a file.")
        with st.form("register_form", clear_on_submit=True):
            register_upload = st.file_uploader("Choose a file to anchor (max 16 MB)", key="register_upload")
            register_submit = st.form_submit_button("Register file  →", type="primary", use_container_width=True)
        if register_submit:
            if register_upload is None:
                st.warning("Choose a file first.")
            elif register_upload.size > MAX_FILE_BYTES:
                st.error("Files must be 16 MB or smaller.")
            else:
                try:
                    new_block = register_file(register_upload.name, register_upload.getvalue())
                    chain.append(new_block)
                    chain_valid, chain_message = check_chain(chain)
                    st.success(f"Registered. Save record ID: {new_block['record_id']}")
                except (OSError, ValueError, json.JSONDecodeError) as exc:
                    st.error(str(exc))
        st.caption("🔒 File contents are not saved in the ledger.")

with col_b:
    with st.container(border=True):
        st.caption("STEP 02")
        st.subheader("Verify a file")
        st.write("Compare a file against its registered fingerprint.")
        with st.form("verify_form", clear_on_submit=True):
            record_id = st.text_input("RECORD ID", placeholder="e.g. A1B2C3D4E5F6").strip().upper()
            verify_upload = st.file_uploader("Choose file to verify", key="verify_upload")
            verify_submit = st.form_submit_button("Verify integrity  →", use_container_width=True)
        if verify_submit:
            if not record_id or verify_upload is None:
                st.warning("Enter the record ID and choose a file.")
            elif not chain_valid:
                st.error(f"Verification blocked because the chain is invalid: {chain_message}")
            else:
                match = next((item for item in chain if item.get("record_id") == record_id), None)
                if match is None:
                    st.error("No record found with that ID.")
                elif digest(verify_upload.getvalue()) == match.get("file_hash"):
                    st.success(f"Verified: the file matches record {record_id}.")
                else:
                    st.error(f"Mismatch: this file does not match record {record_id}.")

st.divider()
st.caption("THE LEDGER")
st.subheader(f"Chain records  ·  {len(chain)}")
if chain_valid:
    st.success(f"Chain is valid — {chain_message}")
else:
    st.error(f"Chain integrity issue — {chain_message}")

if chain:
    for block in reversed(chain):
        with st.container(border=True):
            left, right = st.columns([5, 1])
            with left:
                st.markdown(f"**Block {block['index']:02d} · {block['filename']}**")
                st.caption(f"ID `{block['record_id']}` · {block['file_size']:,} bytes · {block['timestamp']}")
                st.code(f"SHA-256  {block['file_hash']}", language=None)
            with right:
                st.metric("LINKED", "✓")
else:
    st.info("Your chain starts here. Register a file to create the first block.")

st.caption("CHAINCHECK · BLOCKCHAIN MINI PROJECT · SHA-256 + LINKED RECORDS")

import streamlit as st
import fitz
import anthropic
import pandas as pd
import json
import io
import sys
import time
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="BookKeeper AI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

client = anthropic.Anthropic(timeout=120.0)

# --- SIDEBAR ---
st.sidebar.title("📚 BookKeeper AI")
st.sidebar.write("Your intelligent bookkeeping assistant")
st.sidebar.divider()

# --- UTILITY FUNCTIONS ---
def clean_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

def read_pdf(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text

def call_claude(system_prompt, user_message, max_tokens=1024):
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}]
    )
    return response.content[0].text

# --- TABS ---
tab1, tab2, tab3, tab4 = st.tabs([
    "🧾 Invoice extraction",
    "💬 Chat with files",
    "📂 Document classification",
    "🔄 Data reconciliation"
])

# ==========================================
# MODULE 1: INVOICE EXTRACTION
# ==========================================
with tab1:
    st.header("🧾 Automatic invoice data extraction")
    st.write("Upload your invoices and let AI extract all the data in one click.")

    PROMPT_INVOICE = """You are an assistant specialized in extracting data from invoices.
Extract the information and return ONLY a valid JSON object:
{
    "invoice_number": "string",
    "date": "DD/MM/YYYY",
    "vendor": "string",
    "client": "string",
    "line_items": [{"description": "string", "quantity": 0, "unit_price": 0.00, "line_total": 0.00}],
    "subtotal": 0.00,
    "tax": 0.00,
    "total": 0.00,
    "payment_terms": "string or null"
}
Amounts as numbers, dates as DD/MM/YYYY. Return ONLY the JSON."""

    invoices_upload = st.file_uploader(
        "Upload your invoices (PDF)",
        type=["pdf"],
        accept_multiple_files=True,
        key="invoices"
    )

    if invoices_upload and "invoices_result" not in st.session_state:
        if st.button("Extract data", key="btn_invoices"):
            st.session_state.invoices_result = []
            progress = st.progress(0)

            for i, file in enumerate(invoices_upload):
                st.write(f"Extracting {file.name}...")
                text = read_pdf(file.read())
                response = call_claude(PROMPT_INVOICE, f"Invoice:\n\n{text}")
                response = clean_json(response)
                try:
                    data = json.loads(response)
                    data["source_file"] = file.name
                    st.session_state.invoices_result.append(data)
                except:
                    pass
                progress.progress((i + 1) / len(invoices_upload))
                if i < len(invoices_upload) - 1:
                    time.sleep(3)
            st.rerun()

    if "invoices_result" in st.session_state and st.session_state.invoices_result:
        results = st.session_state.invoices_result

        summary = [{
            "Invoice #": r["invoice_number"],
            "Date": r["date"],
            "Vendor": r["vendor"],
            "Client": r["client"],
            "Subtotal": r["subtotal"],
            "Tax": r["tax"],
            "Total": r["total"]
        } for r in results]

        df = pd.DataFrame(summary)
        st.dataframe(df, use_container_width=True)

        col1, col2, col3 = st.columns(3)
        col1.metric("Invoices processed", len(df))
        col2.metric("Subtotal", f"${df['Subtotal'].sum():,.2f}")
        col3.metric("Total", f"${df['Total'].sum():,.2f}")

        for r in results:
            with st.expander(f"{r['invoice_number']} — {r['vendor']}"):
                for item in r["line_items"]:
                    st.write(f"- {item['description']}: {item['quantity']} x ${item['unit_price']} = ${item['line_total']}")

        # Excel export
        detail = []
        for r in results:
            for item in r["line_items"]:
                detail.append({
                    "Invoice #": r["invoice_number"],
                    "Vendor": r["vendor"],
                    "Description": item["description"],
                    "Quantity": item["quantity"],
                    "Unit price": item["unit_price"],
                    "Line total": item["line_total"]
                })
        df_detail = pd.DataFrame(detail)

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Summary", index=False)
            df_detail.to_excel(writer, sheet_name="Line items", index=False)

        st.download_button(
            label="Download Excel report",
            data=buffer.getvalue(),
            file_name="invoices_extracted.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    if st.button("Reset invoices", key="reset_invoices"):
        st.session_state.pop("invoices_result", None)
        st.rerun()

# ==========================================
# MODULE 2: CHAT WITH FILES
# ==========================================
with tab2:
    st.header("💬 Chat with your Excel/CSV files")
    st.write("Upload a file and ask questions in plain English.")

    chat_file = st.file_uploader("Upload a file", type=["csv", "xlsx"], key="chat_file")

    if chat_file and "chat_df" not in st.session_state:
        if chat_file.name.endswith(".csv"):
            st.session_state.chat_df = pd.read_csv(chat_file)
        else:
            st.session_state.chat_df = pd.read_excel(chat_file)

        df = st.session_state.chat_df
        st.session_state.chat_info = f"""DataFrame 'df' loaded.
COLUMNS: {df.columns.tolist()}
TYPES: {df.dtypes.to_dict()}
ROWS: {len(df)}
PREVIEW:
{df.head(5).to_string()}
UNIQUE VALUES PER COLUMN:
{chr(10).join(f'- {col}: {df[col].nunique()} unique values' for col in df.columns if df[col].dtype == 'object')}
"""

    if "chat_df" in st.session_state:
        with st.expander("Data preview"):
            st.dataframe(st.session_state.chat_df.head(10), use_container_width=True)

    tools = [{
        "name": "run_pandas",
        "description": "Execute pandas code on the DataFrame 'df'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Pandas code. The DataFrame is called 'df'."}
            },
            "required": ["code"]
        }
    }]

    def run_pandas(code):
        try:
            if "\n" not in code and not code.startswith("print"):
                result = eval(code, {"df": st.session_state.chat_df, "pd": pd, "__builtins__": __builtins__})
                return str(result)
            else:
                old_stdout = sys.stdout
                sys.stdout = buffer = io.StringIO()
                exec(code, {"df": st.session_state.chat_df, "pd": pd, "__builtins__": __builtins__})
                sys.stdout = old_stdout
                return buffer.getvalue() or "Code executed"
        except Exception as e:
            return f"Error: {e}"

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    if "chat_display" not in st.session_state:
        st.session_state.chat_display = []

    for msg in st.session_state.chat_display:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if prompt := st.chat_input("Ask a question about your data...", key="chat_input"):
        if "chat_df" not in st.session_state:
            st.warning("Please upload a file first!")
        else:
            st.session_state.chat_display.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Analyzing..."):
                    st.session_state.chat_messages.append({"role": "user", "content": prompt})

                    while True:
                        response = client.messages.create(
                            model="claude-haiku-4-5-20251001",
                            max_tokens=1024,
                            system=f"""You are an expert bookkeeping assistant.
Use the run_pandas tool to analyze the data.
Answer in English with precise numbers.
{st.session_state.chat_info}""",
                            tools=tools,
                            messages=st.session_state.chat_messages
                        )

                        if response.stop_reason == "end_turn":
                            reply = "".join(b.text for b in response.content if b.type == "text")
                            st.write(reply)
                            st.session_state.chat_messages.append({"role": "assistant", "content": response.content})
                            st.session_state.chat_display.append({"role": "assistant", "content": reply})
                            break

                        if response.stop_reason == "tool_use":
                            st.session_state.chat_messages.append({"role": "assistant", "content": response.content})
                            tool_results = []
                            for block in response.content:
                                if block.type == "tool_use":
                                    result = run_pandas(block.input["code"])
                                    tool_results.append({
                                        "type": "tool_result",
                                        "tool_use_id": block.id,
                                        "content": result
                                    })
                            st.session_state.chat_messages.append({"role": "user", "content": tool_results})

    if st.button("Reset chat", key="reset_chat"):
        for k in ["chat_df", "chat_info", "chat_messages", "chat_display"]:
            st.session_state.pop(k, None)
        st.rerun()

# ==========================================
# MODULE 3: DOCUMENT CLASSIFICATION
# ==========================================
with tab3:
    st.header("📂 Automatic document classification")
    st.write("Upload documents and AI classifies them by type.")

    PROMPT_CLASSIF = """Analyze the document and return ONLY a JSON:
{
    "document_type": "invoice | quote | purchase_order | bank_statement | contract | expense_report | other",
    "confidence": 0.95,
    "issuer": "name or null",
    "date": "date or null",
    "main_amount": 0.00,
    "summary": "one sentence summary"
}
Return ONLY the JSON."""

    classif_files = st.file_uploader(
        "Upload your documents",
        type=["pdf"],
        accept_multiple_files=True,
        key="classif"
    )

    if classif_files and st.button("Classify documents", key="btn_classif"):
        classif_results = []
        progress = st.progress(0)

        for i, file in enumerate(classif_files):
            st.write(f"Classifying {file.name}...")
            text = read_pdf(file.read())
            response = call_claude(PROMPT_CLASSIF, f"Document:\n\n{text[:3000]}")
            response = clean_json(response)
            try:
                data = json.loads(response)
                data["file"] = file.name
                classif_results.append(data)
            except:
                pass
            progress.progress((i + 1) / len(classif_files))
            if i < len(classif_files) - 1:
                time.sleep(3)

        if classif_results:
            df_classif = pd.DataFrame(classif_results)
            st.dataframe(
                df_classif[["file", "document_type", "confidence", "summary", "main_amount"]],
                use_container_width=True
            )
            for r in classif_results:
                with st.expander(f"{r['file']} -> {r['document_type']}"):
                    st.write(f"Issuer: {r.get('issuer', 'N/A')}")
                    st.write(f"Date: {r.get('date', 'N/A')}")
                    st.write(f"Amount: ${r.get('main_amount', 'N/A')}")
                    st.write(f"Summary: {r['summary']}")

# ==========================================
# MODULE 4: DATA RECONCILIATION
# ==========================================
with tab4:
    st.header("🔄 Data reconciliation")
    st.write("Compare two files to find matches and discrepancies.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("File 1")
        reconc_file1 = st.file_uploader("General ledger", type=["csv", "xlsx"], key="reconc1")

    with col2:
        st.subheader("File 2")
        reconc_file2 = st.file_uploader("Bank statement", type=["csv", "xlsx"], key="reconc2")

    if reconc_file1 and reconc_file2 and st.button("Reconcile", key="btn_reconc"):
        with st.spinner("Reconciliation in progress..."):
            if reconc_file1.name.endswith(".csv"):
                ledger = pd.read_csv(reconc_file1)
            else:
                ledger = pd.read_excel(reconc_file1)

            if reconc_file2.name.endswith(".csv"):
                statement = pd.read_csv(reconc_file2)
            else:
                statement = pd.read_excel(reconc_file2)

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("General ledger")
                st.dataframe(ledger, use_container_width=True)
            with col2:
                st.subheader("Bank statement")
                st.dataframe(statement, use_container_width=True)

            prompt_reconc = f"""Here are two files to reconcile:

GENERAL LEDGER:
{ledger.to_string(index=False)}

BANK STATEMENT:
{statement.to_string(index=False)}

Analyze and:
1. Identify matching entries (by date and amount)
2. List entries in the ledger but missing from the statement
3. List entries in the statement but missing from the ledger
4. Calculate balances
5. Provide recommendations

Format clearly with sections."""

            response = call_claude(
                "You are an expert accountant specialized in bank reconciliation. Answer in English.",
                prompt_reconc,
                max_tokens=2048
            )

            st.subheader("Analysis")
            st.write(response)
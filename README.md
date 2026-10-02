# 🥧 SnapSplit — AI Receipt & Expense Tracker / Bill Splitter

SnapSplit is a modern, student-friendly AI-powered receipt and expense assistant built with Streamlit and the Google Gemini API (`google-genai`).

Instead of rigid traditional OCR, SnapSplit leverages Gemini Vision to understand complex receipts, extract readable items and taxes, answer conversational questions about your expenses, calculate accurate bill splits between friends, and deliver clean itemized summaries directly to your email using Gmail SMTP.

---

## ✨ Features

- 📸 **AI Receipt Analysis**: Upload or snap receipt photos (`.jpg`, `.jpeg`, `.png`) for instant visual comprehension.
- 🔍 **Intelligent Expense Extraction**: Automatically extracts merchant name, date, itemized list with prices, subtotal, taxes, fees, discounts, and total.
- 💬 **Conversational Follow-Up**: Ask natural follow-up questions (e.g. *"How much did the drinks cost?"* or *"Was any tax applied?"*).
- 👥 **Smart Bill Splitting**: Request equal bill splits (e.g. *"Split this between 4 people"*), with automatic calculation and clear per-person breakdowns.
- 📧 **Direct Email Summaries**: Send an itemized expense and bill-split summary straight to your inbox via secure Gmail SMTP (port 465 SSL).
- 🔒 **Zero Hardcoded Secrets**: Secure credentials management via Streamlit Secrets (`st.secrets`).

---

## 🛠️ Technology Stack

- **Frontend & Web Framework**: [Streamlit](https://streamlit.io/)
- **AI & Vision Model**: [Google GenAI Python SDK (`google-genai`)](https://github.com/google-gemini/deprecations) with Gemini Vision
- **Email Delivery**: Python built-in `smtplib` & `email.mime` (Gmail SMTP over SSL)
- **Deployment**: Streamlit Community Cloud & GitHub

---

## 📁 Project Structure

```
snapsplit/
│
├── app.py                      # Main Streamlit application
├── prompts.py                  # System prompts and templates for Gemini
├── requirements.txt            # Minimal required dependencies
├── README.md                   # Documentation and deployment guide
├── .gitignore                  # Git ignore rules (protects real secrets)
│
└── .streamlit/
    └── secrets.toml.example    # Template for Streamlit secrets
```

---

## 🚀 Local Setup & Installation

**Prerequisites**: Python 3.9+ installed.

### 1. Clone the Repository
```bash
git clone https://github.com/dhilipdinesh100-del/snapsplit.git
cd snapsplit
```

### 2. Create and Activate a Virtual Environment
- **Windows (PowerShell)**:
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  ```
- **macOS / Linux**:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### 3. Install Required Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Streamlit Secrets
Duplicate the example secrets file:
```bash
# Windows PowerShell
copy .streamlit\secrets.toml.example .streamlit\secrets.toml

# macOS / Linux
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Open `.streamlit/secrets.toml` in your editor and provide your credentials:
```toml
GEMINI_API_KEY = "your-gemini-api-key-here"
GMAIL_ADDRESS = "your-gmail-address@gmail.com"
GMAIL_APP_PASSWORD = "your-16-character-app-password"
```

> ⚠️ **Important Security Notes**:
> - **Never** commit `.streamlit/secrets.toml` to GitHub. It is already included in `.gitignore`.
> - For Gmail, **do not** use your regular Google account password. You must use an **App Password**:
>   1. Enable **2-Step Verification** on your Google Account.
>   2. Go to **Google Account Settings** > **Security** > **App Passwords** (or search "App passwords").
>   3. Generate a 16-character password for "SnapSplit" and paste it into `GMAIL_APP_PASSWORD`.
> - Obtain a free Gemini API key from [Google AI Studio](https://aistudio.google.com/).

### 5. Run the Application
```bash
streamlit run app.py
```

The application will launch automatically in your browser at:
```
http://localhost:8501
```

---

## 🧪 Testing the Application

1. **Onboarding**:
   - Enter your Name and Email address.
   - Click **"Let's go 🚀"**.
2. **Receipt Analysis**:
   - In the chat input at the bottom, click the **+** (attachment icon) to upload a receipt photo.
   - Press **Enter** (or type a question like *"Analyze this bill"*).
   - Gemini Vision will output the merchant, itemized prices, subtotal, taxes, and final total.
3. **Bill Splitting**:
   - Type: `"Split this between 3 people."`
   - Gemini will extract the total, divide by 3, and display the per-person amount.
4. **Email Summary**:
   - Click the **"📧 Send Summary to Email"** button at the top right.
   - Check your inbox for the formatted summary sent via Gmail SMTP.

---

## ☁️ Deployment on Streamlit Community Cloud

SnapSplit is pre-configured for one-click deployment to [Streamlit Community Cloud](https://streamlit.io/cloud):

1. **Push your code to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Prepare SnapSplit for deployment"
   git branch -M main
   git remote add origin https://github.com/dhilipdinesh100-del/snapsplit.git
   git push -u origin main
   ```
2. **Go to Streamlit Community Cloud**:
   - Sign in at [share.streamlit.io](https://share.streamlit.io/).
   - Click **"New app"**.
3. **Repository Settings**:
   - Select your GitHub repository.
   - Branch: `main`
   - Main file path: `app.py`
4. **Configure Secrets**:
   - Click **Advanced Settings** > **Secrets**.
   - Copy the contents of your local `.streamlit/secrets.toml` and paste them into the secrets textarea:
     ```toml
     GEMINI_API_KEY = "your-gemini-api-key"
     GMAIL_ADDRESS = "your-gmail@gmail.com"
     GMAIL_APP_PASSWORD = "your-gmail-app-password"
     ```
5. **Deploy**:
   - Click **Deploy**! Your app will be live on a public URL.

---

## 📄 License
This project is open-source and created for educational and student portfolio purposes.

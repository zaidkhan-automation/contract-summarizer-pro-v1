# 📝 Contract Summarizer — Pro v1  

A compact AI-powered tool that extracts text from PDF/DOCX contracts, chunks it intelligently, and generates concise summaries.  
Supports fallback extractive summaries (no API key) or abstractive legal summaries (if OpenAI API key is provided).  

---

## ✨ Features  
- 📂 Upload *contracts in PDF/DOCX* format  
- 🧹 Cleans and chunks text with sentence awareness  
- 🤖 Summarizes with *OpenAI GPT models* (optional)  
- 📝 Fallback extractive summaries if no API key provided  
- 💾 Download summaries in TXT format  
- 🔍 Expand and preview contract chunks  

---

## 🚀 Live App  
👉 [*Try it here*](https://your-streamlit-deploy-link.streamlit.app)  

---

## 📸 Screenshots  
Before (uploading a contract):  
![Before](assets/before.png)  

After (summary generated):  
![After](assets/after.png)  

---

## 🎥 Demo Video  
▶ [Watch demo](demo.mp4)  

---

## 🛠 How to Run Locally  

```bash
# Clone the repo
git clone https://github.com/zaidkhan-automation/contract-summarizer-pro-v1
cd contract-summarizer-pro-v1

# Create virtual environment
python -m venv venv
# Windows
.\venv\Scripts\Activate
# Linux/Mac
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run app
streamlit run src/app.py
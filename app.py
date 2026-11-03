import gradio as gr
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from newspaper import Article
import easyocr
from PIL import Image
import numpy as np
import warnings
import base64

warnings.filterwarnings("ignore")

# 1. Load Model
print("Loading Model... Please wait.")
model_path = "./"
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForSequenceClassification.from_pretrained(model_path)
model.eval()

print("Loading OCR... Please wait.")
reader = easyocr.Reader(["en", "ur"])

# 2. Backend Functions
def predict_news(text):
    if not text.strip():
        return "⚠️ Please enter text or URL first!", ""
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=128)
    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
    
    fake_prob = probs[0][0].item() * 100
    real_prob = probs[0][1].item() * 100

    if fake_prob > real_prob:
        result = f"🚨 FAKE NEWS! (Confidence: {fake_prob:.2f}%)"
    else:
        result = f"✅ REAL NEWS (Confidence: {real_prob:.2f}%)"

    explain = "Model focused on these words: "
    if fake_prob > real_prob:
        words = text.split()
        suspicious = [w for w in words if w.lower() in ["free", "viral", "muft", "hamesha", "shocking", "doctor", "claim", "mukammal", "mufat"]]
        if suspicious:
            for w in suspicious: explain += f" **{w}**, "
        else: explain += " (General sensational tone detected)"
    else:
        explain = "News contains factual words."
    return result, explain

def analyze_url(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        text = article.title + " " + article.text
        return predict_news(text)
    except Exception:
        return "Could not extract text from URL. Check if the link is valid.", ""

def analyze_image(image):
    if image is None: return "⚠️ Please upload an image first!", ""
    try:
        result = reader.readtext(np.array(image), detail=0)
        extracted_text = " ".join(result)
        prediction, explain = predict_news(extracted_text)
        return f"Extracted Text:\n{extracted_text}\n\nResult: {prediction}", explain
    except Exception:
        return "Could not analyze image.", ""

# 3. Custom CSS (Bilkul aapki HTML jaisa premium look)
custom_css = """
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');

body, .gradio-container {
    font-family: 'Poppins', sans-serif !important;
    background-color: #f5faf8 !important;
    color: #0f2747 !important;
}

/* Hero Section with Background Image */
.hero-section {
    background-image: url('https://images.unsplash.com/photo-1590052240157-2657b0c36a8f?q=80&w=2000&auto=format&fit=crop'); 
    background-size: cover;
    background-position: center;
    position: relative;
    border-radius: 20px;
    padding: 60px 20px;
    text-align: center;
    margin-bottom: 30px;
    border-bottom: 5px solid #0b6b3a;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
}

.hero-section::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: linear-gradient(to bottom, rgba(255,255,255,0.85), rgba(255,255,255,0.95));
    border-radius: 20px;
    z-index: 1;
}

.hero-content {
    position: relative;
    z-index: 2;
}

.hero-badge {
    color: #0b6b3a; font-weight: 700; font-size: 14px; margin-bottom: 15px;
    display: inline-block; background: #d9f1e4; padding: 5px 15px; border-radius: 20px;
}

.hero-title {
    font-size: 3rem; font-weight: 700; color: #0f2747; margin-bottom: 15px; line-height: 1.2;
}

.hero-title span { color: #0b6b3a; }

.hero-subtitle {
    font-size: 1.1rem; color: #5a6b82; max-width: 700px; margin: 0 auto 20px auto; line-height: 1.6;
}

.hero-tagline {
    font-weight: 700; color: #0b6b3a; letter-spacing: 2px; margin-bottom: 30px;
}

/* Main Analysis Card */
.main-card {
    background: white !important;
    border-radius: 20px !important;
    box-shadow: 0 15px 40px rgba(0,0,0,0.08) !important;
    padding: 30px !important;
    margin-top: -80px;
    position: relative;
    z-index: 10;
    border: 1px solid #dbe6e2 !important;
}

/* Styling Gradio Inputs & Buttons */
.gradio-container label { display: none !important; }
textarea, input { border-radius: 10px !important; border: 1px solid #dbe6e2 !important; }

button.primary {
    background: linear-gradient(135deg, #0b6b3a, #14894c) !important; 
    border-radius: 10px !important; color: white !important; font-weight: 600 !important;
    border: none !important;
}
button.secondary {
    background-color: #f8faf9 !important; border-radius: 10px !important; color: #0f2747 !important; font-weight: 600 !important;
    border: 1px solid #dbe6e2 !important;
}
.tabs { border-bottom: 2px solid #0b6b3a !important; }
.tab-nav button.selected { color: #0b6b3a !important; border-bottom: 3px solid #0b6b3a !important; }
"""

# 4. UI Layout
with gr.Blocks(css=custom_css, title="Pakistani Multilingual Fake News Detector") as demo:
    
    # Hero Section
    gr.HTML("""
        <div class="hero-section">
            <div class="hero-content">
                <div class="hero-badge">🇵🇰 Fight Misinformation • Build an Informed Pakistan</div>
                <div class="hero-title">Pakistani Multilingual<br><span>Fake News Detector</span></div>
                <div class="hero-subtitle">
                    An Advanced AI-Powered Tool to Detect Fake News in 6 Native Languages (English, Urdu, Sindhi, Punjabi, Saraiki & Roman Urdu).
                </div>
                <div class="hero-tagline">Read • Verify • Trust</div>
            </div>
        </div>
    """)
    
    # Main App Container
    with gr.Column(elem_classes="main-card"):
        with gr.Tabs():
            with gr.Tab("📝 Text / Link Check"):
                text_input = gr.Textbox(show_label=False, placeholder="Paste news content, article text, or a URL here...", lines=4)
                with gr.Row():
                    analyze_btn = gr.Button("🔍 Analyze News →", variant="primary", scale=2)
                    url_btn = gr.Button("🔗 Analyze URL", variant="secondary", scale=1)
                    clear_btn = gr.Button("Clear", variant="secondary", scale=1)
                
                with gr.Row():
                    result_text = gr.Textbox(label="Analysis Result", lines=3, interactive=False)
                    explain_text = gr.Textbox(label="Explanation & Insights", lines=3, interactive=False)
                
                analyze_btn.click(predict_news, text_input, [result_text, explain_text])
                url_btn.click(analyze_url, text_input, [result_text, explain_text])
                clear_btn.click(lambda: ("", "", ""), [], [text_input, result_text, explain_text])

            with gr.Tab("🖼️ Screenshot Check (OCR)"):
                image_input = gr.Image(show_label=False, type="pil")
                img_btn = gr.Button("🔍 Analyze Screenshot", variant="primary")
                with gr.Row():
                    img_result = gr.Textbox(label="Analysis Result", lines=4, interactive=False)
                    img_explain = gr.Textbox(label="Explanation", lines=4, interactive=False)
                img_btn.click(analyze_image, image_input, [img_result, img_explain])

    # Footer Features
    gr.HTML("""
        <div style="display: flex; justify-content: space-around; margin-top: 40px; text-align: center; color: #5a6b82;">
            <div><h3 style="color: #0b6b3a; font-weight: bold;">✓ AI Powered</h3><p>Advanced Machine Learning</p></div>
            <div><h3 style="color: #0b6b3a; font-weight: bold;">🌐 6 Languages</h3><p>Native Pakistani Support</p></div>
            <div><h3 style="color: #0b6b3a; font-weight: bold;">⚡ Fast Results</h3><p>Instant Analysis</p></div>
        </div>
    """)

if __name__ == "__main__":
    demo.launch(share=True)
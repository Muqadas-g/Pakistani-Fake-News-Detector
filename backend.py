from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from newspaper import Article
import torch
import warnings

warnings.filterwarnings("ignore")

app = FastAPI()

# CORS setup (taake HTML is server se baat kar sake)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Model Load
model_path = "./"
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForSequenceClassification.from_pretrained(model_path)
model.eval()

class TextRequest(BaseModel):
    text: str
    language: str

class UrlRequest(BaseModel):
    url: str
    language: str

def process_text(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=128)
    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
    
    fake_prob = probs[0][0].item() * 100
    real_prob = probs[0][1].item() * 100
    
    if fake_prob > real_prob:
        return {"label": "fake", "confidence": round(fake_prob, 2)}
    else:
        return {"label": "real", "confidence": round(real_prob, 2)}

@app.post("/api/analyze-text")
async def analyze_text(req: TextRequest):
    return process_text(req.text)

@app.post("/api/analyze-url")
async def analyze_url(req: UrlRequest):
    try:
        article = Article(req.url)
        article.download()
        article.parse()
        text = article.title + " " + article.text
        if not text.strip():
            raise ValueError("No text found")
        return process_text(text)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Could not extract text from this URL.")
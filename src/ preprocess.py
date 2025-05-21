# src/preprocess.py

import re
import os
import json
import pandas as pd
import torch
import logging
from langdetect import detect
from transformers import AutoTokenizer, AutoModel
import py_vncorenlp

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Predefined scam keywords for heuristic
SCAM_KEYWORDS = [
    'giveaway', 'đầu tư', 'trúng thưởng', 'miễn phí', 'link',
    'bitcoin', 'ether', 'crypto', 'liên hệ', 'zalo'
]

# Load VnCoreNLP for Vietnamese word segmentation
VNC_PATH = '/absolute/path/to/vncorenlp'  # cập nhật đường dẫn
py_vncorenlp.download_model(save_dir=VNC_PATH)
segmenter = py_vncorenlp.VnCoreNLP(annotators=["wseg"], save_dir=VNC_PATH)

# Load PhoBERT tokenizer & model
PHOBERT_NAME = "vinai/phobert-base-v2"
tokenizer = AutoTokenizer.from_pretrained(PHOBERT_NAME)
model = AutoModel.from_pretrained(PHOBERT_NAME)
model.eval()

@torch.no_grad()
def get_phobert_embedding(text: str) -> list:
    """
    Trích xuất embedding CLS từ PhoBERT cho văn bản đã được tách từ.
    """
    inputs = tokenizer.encode_plus(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=128,
        add_special_tokens=True
    )
    outputs = model(**inputs)
    return outputs.last_hidden_state[:, 0, :].squeeze().tolist()


def detect_language(text: str) -> str:
    """
    Phát hiện ngôn ngữ văn bản.
    """
    try:
        return detect(text)
    except:
        return 'unknown'


def clean_text(text: str) -> str:
    """
    Loại bỏ HTML, emoji, ký tự đặc biệt, chuyển chữ thường.
    """
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'[^0-9A-Za-zÀ-ỹ\s,.!?]', ' ', text)
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)
    return text


def tokenize_vi(text: str) -> str:
    """
    Tách từ tiếng Việt bằng VnCoreNLP, trả về chuỗi đã tách (dùng '_' nối từ).
    """
    sentences = segmenter.word_segment(text)
    # word_segment trả về list câu; nối thành chuỗi
    return ' '.join(sentences)


def extract_urls_and_domains(text: str) -> tuple:
    """
    Trích URL và domain trong văn bản.
    """
    urls = re.findall(r'https?://[^\s]+', text)
    domains = []
    for url in urls:
        m = re.match(r'https?://([^/]+)/?', url)
        if m:
            domains.append(m.group(1))
    return urls, domains


def process_comments(in_path: str, out_path: str):
    """
    Xử lý CSV bình luận đầu vào, trích feature và embedding.
    """
    df = pd.read_csv(in_path)
    records = []
    for _, row in df.iterrows():
        raw = row.get('text', '')
        if detect_language(raw) != 'vi':
            continue
        clean = clean_text(raw)
        tokens = tokenize_vi(clean)
        urls, domains = extract_urls_and_domains(raw)
        num_scam = sum(1 for kw in SCAM_KEYWORDS if kw in clean)
        emb = get_phobert_embedding(tokens)
        records.append({
            'comment_id': row['comment_id'],
            'video_id': row['video_id'],
            'text_clean': clean,
            'tokens': tokens,
            'num_words': len(tokens.split()),
            'num_urls': len(urls),
            'domains': ';'.join(domains),
            'num_scam_keywords': num_scam,
            'phobert_emb': '|'.join(f"{x:.6f}" for x in emb)
        })
    df_out = pd.DataFrame(records)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    df_out.to_csv(out_path, index=False)
    logger.info(f"Saved features and embeddings to {out_path} (records: {len(df_out)})")


if __name__ == '__main__':
    process_comments('data/demo_comments.csv', 'data/features_initial.csv')
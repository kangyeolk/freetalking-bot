"""
Vocabulary analyzer using OpenAI API for Japanese conversation learning
"""

import openai
import json
import streamlit as st
from typing import List, Dict, Optional
from datetime import datetime
import re

class VocabularyAnalyzer:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
        self.session_vocabulary = []
        self.analyzed_texts = set()  # Track already analyzed texts
        
    def analyze_conversation(self, text: str, role: str = 'assistant') -> List[Dict]:
        """Analyze Japanese text and extract vocabulary with LLM"""
        
        # Skip if already analyzed or too short
        if text in self.analyzed_texts or len(text) < 3:
            return []
        
        # Only analyze assistant messages (Japanese)
        if role != 'assistant':
            return []
            
        self.analyzed_texts.add(text)
        
        prompt = f"""
        다음 일본어 텍스트에서 학습에 유용한 단어와 표현을 추출하고 분석해주세요.
        중요한 단어, 문법 포인트, 관용구를 중심으로 선택해주세요.
        
        텍스트: {text}
        
        다음 형식의 JSON으로 응답해주세요:
        {{
            "vocabulary": [
                {{
                    "word": "원형 또는 표면형",
                    "reading": "히라가나 읽기",
                    "meaning_kr": "한국어 뜻",
                    "meaning_en": "영어 뜻 (옵션)",
                    "pos": "품사 (명사/동사/형용사 등)",
                    "level": "JLPT 레벨 (N5-N1)",
                    "example": "예문 (있으면)",
                    "notes": "문법 설명이나 사용법 팁 (옵션)"
                }}
            ]
        }}
        
        주의사항:
        - 너무 기초적인 조사나 대명사는 제외
        - 학습 가치가 있는 단어 중심으로 5-10개 선택
        - 문맥에서의 실제 의미를 반영
        - JLPT 레벨을 정확히 판단
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-5-nano",
                messages=[
                    {"role": "system", "content": "You are a Japanese language teacher helping Korean students learn vocabulary."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            vocabulary = result.get('vocabulary', [])
            
            # Add timestamp and source text
            for word in vocabulary:
                word['source_text'] = text[:50] + "..." if len(text) > 50 else text
                word['timestamp'] = datetime.now().isoformat()
                
                # Check if word already exists in session
                exists = any(
                    w.get('word') == word['word'] 
                    for w in self.session_vocabulary
                )
                if not exists:
                    self.session_vocabulary.append(word)
            
            return vocabulary
            
        except Exception as e:
            st.error(f"Vocabulary analysis error: {e}")
            return []
    
    def get_session_vocabulary(self) -> List[Dict]:
        """Get all vocabulary from current session"""
        return self.session_vocabulary
    
    def get_vocabulary_by_level(self) -> Dict[str, List[Dict]]:
        """Group vocabulary by JLPT level"""
        grouped = {
            'N5': [],
            'N4': [],
            'N3': [],
            'N2': [],
            'N1': []
        }
        
        for word in self.session_vocabulary:
            level = word.get('level', 'N3')
            if level in grouped:
                grouped[level].append(word)
        
        return grouped
    
    def export_vocabulary(self) -> str:
        """Export vocabulary as formatted text"""
        output = "📚 Today's Vocabulary List\n"
        output += "=" * 40 + "\n\n"
        
        grouped = self.get_vocabulary_by_level()
        
        for level in ['N5', 'N4', 'N3', 'N2', 'N1']:
            if grouped[level]:
                output += f"📊 {level} Level\n"
                output += "-" * 20 + "\n"
                
                for word in grouped[level]:
                    output += f"• {word['word']} ({word.get('reading', '')})\n"
                    output += f"  → {word.get('meaning_kr', '')}\n"
                    if word.get('example'):
                        output += f"  例: {word['example']}\n"
                    output += "\n"
        
        return output
    
    def clear_session(self):
        """Clear session vocabulary"""
        self.session_vocabulary.clear()
        self.analyzed_texts.clear()
    
    def save_to_file(self, filename: str = "vocabulary.json"):
        """Save vocabulary to file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.session_vocabulary, f, ensure_ascii=False, indent=2)
    
    def load_from_file(self, filename: str = "vocabulary.json"):
        """Load vocabulary from file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                self.session_vocabulary = json.load(f)
        except FileNotFoundError:
            pass
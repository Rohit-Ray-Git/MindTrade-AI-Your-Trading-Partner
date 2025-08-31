"""
Psychology Journal Page
Track trading psychology and emotional patterns
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from models.database import init_db
from models.dal import TradeDAL, PsychologyDAL, get_db_session
from utils.ai_integration import GeminiAI

# Page config
st.set_page_config(
    page_title="Psychology Journal",
    page_icon="🧠",
    layout="wide"
)

# Initialize
init_db()
ai_engine = GeminiAI()

st.title("🧠 Psychology & Trading Journal")

# Add psychology note
st.subheader("📝 Add Psychology Note")

with st.form("psychology_form"):
    note_text = st.text_area("Note", placeholder="How did you feel about this trade? What emotions did you experience?")
    
    col1, col2 = st.columns(2)
    with col1:
        confidence_level = st.slider("Confidence Level", 1, 10, 5)
    with col2:
        emotional_state = st.selectbox("Emotional State", 
            ["Confident", "Anxious", "Excited", "Fearful", "Greedy", "Patient", "Impatient", "Frustrated", "Calm"])
    
    submitted = st.form_submit_button("💾 Add Note", type="primary")
    
    if submitted and note_text:
        db = get_db_session()
        psych_dal = PsychologyDAL(db)
        
        # Get recent trade ID if available
        trade_dal = TradeDAL(db)
        recent_trades = trade_dal.get_trades(limit=1)
        trade_id = recent_trades[0].id if recent_trades else None
        
        # Convert confidence level to confidence score (0-1 scale)
        confidence_score = confidence_level / 10.0
        
        # Create tags based on emotional state
        emotional_tags = [emotional_state.lower()]
        
        note_data = {
            'trade_id': trade_id,
            'note_text': note_text,
            'confidence_score': confidence_score,
            'self_tags': emotional_tags
        }
        
        try:
            note = psych_dal.create_note(note_data)
            st.success("✅ Psychology note added successfully!")
            
            # AI Analysis
            if ai_engine.enabled:
                with st.spinner("🤖 AI is analyzing your psychology..."):
                    analysis = ai_engine.analyze_psychology_with_image(note_text)
                    
                    if analysis:
                        st.subheader("🤖 AI Psychology Analysis")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            sentiment = analysis.get('sentiment_score', 0)
                            st.metric("Sentiment", f"{sentiment:.2f}", help="Range: -1 (negative) to +1 (positive)")
                        with col2:
                            confidence = analysis.get('confidence_score', 0)
                            st.metric("Confidence", f"{confidence:.2f}", help="Range: 0 to 1")
                        with col3:
                            fear = analysis.get('fear_score', 0)
                            st.metric("Fear Level", f"{fear:.2f}", help="Range: 0 to 1")
                        
                        if 'key_insights' in analysis:
                            st.subheader("🧠 AI Insights")
                            for insight in analysis['key_insights']:
                                st.write(f"• {insight}")
        
        except Exception as e:
            st.error(f"Error adding psychology note: {e}")
        
        db.close()

# Recent psychology notes
st.subheader("📋 Recent Psychology Notes")

db = get_db_session()
psych_dal = PsychologyDAL(db)
recent_notes = psych_dal.get_recent_notes(limit=10)

if recent_notes:
    for note in recent_notes:
        with st.expander(f"Note from {note.created_at.strftime('%Y-%m-%d %H:%M')}"):
            st.write(note.note_text)
            if note.confidence_score is not None:
                confidence_level = int(note.confidence_score * 10)
                st.write(f"**Confidence:** {confidence_level}/10")
            if note.self_tags:
                st.write(f"**Tags:** {', '.join(note.self_tags)}")
            if note.sentiment_score is not None:
                sentiment_emoji = "😊" if note.sentiment_score > 0 else "😔" if note.sentiment_score < 0 else "😐"
                st.write(f"**Sentiment:** {sentiment_emoji} {note.sentiment_score:.2f}")
else:
    st.info("No psychology notes yet. Start by adding your thoughts and feelings about trades!")

db.close()

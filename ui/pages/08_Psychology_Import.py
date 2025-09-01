"""
Psychology Import Page
Bulk import psychology notes and emotional patterns
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
from models.dal import PsychologyDAL, get_db_session
from utils.ai_integration import GeminiAI

# Page config
st.set_page_config(
    page_title="Psychology Import",
    page_icon="🧠",
    layout="wide"
)

# Initialize
init_db()
ai_engine = GeminiAI()

st.title("🧠 Psychology & Emotional Patterns Import")

st.markdown("""
### 📋 Import Your Trading Psychology Data

This page allows you to import your psychology notes, emotional patterns, and trading mindset data.
You can upload CSV files or manually enter psychology data for analysis.
""")

# File upload section
st.subheader("📁 Upload Psychology Data")

upload_option = st.radio(
    "Choose import method:",
    ["CSV File Upload", "Manual Entry", "Text File Upload"]
)

if upload_option == "CSV File Upload":
    st.markdown("""
    **CSV Format Expected:**
    - Date/Time, Trade_ID (optional), Emotional_State, Confidence_Level, Notes, Tags
    - Example: `2024-01-01, 123, Confident, 8, "Felt good about this setup", "patient,calm"`
    """)
    
    uploaded_file = st.file_uploader(
        "Upload psychology CSV file",
        type=['csv'],
        help="Upload a CSV file with your psychology notes and emotional patterns"
    )
    
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            st.success(f"✅ Loaded {len(df)} psychology records")
            
            # Show preview
            st.subheader("📊 Data Preview")
            st.dataframe(df.head())
            
            # Column mapping
            st.subheader("🎯 Column Mapping")
            col1, col2 = st.columns(2)
            
            with col1:
                date_col = st.selectbox("Date/Time Column", df.columns.tolist())
                emotion_col = st.selectbox("Emotional State Column", df.columns.tolist())
                confidence_col = st.selectbox("Confidence Level Column", df.columns.tolist())
            
            with col2:
                notes_col = st.selectbox("Notes Column", df.columns.tolist())
                tags_col = st.selectbox("Tags Column", df.columns.tolist())
                trade_id_col = st.selectbox("Trade ID Column (optional)", ["None"] + df.columns.tolist())
            
            if st.button("💾 Import Psychology Data", type="primary"):
                with st.spinner("Importing psychology data..."):
                    db = get_db_session()
                    psych_dal = PsychologyDAL(db)
                    
                    imported_count = 0
                    for index, row in df.iterrows():
                        try:
                            # Parse date
                            date_val = pd.to_datetime(row[date_col])
                            
                            # Parse confidence (1-10 scale)
                            confidence = float(row[confidence_col]) / 10.0 if confidence_col != "None" else 0.5
                            
                            # Create tags
                            tags = []
                            if tags_col != "None" and pd.notna(row[tags_col]):
                                tags = [tag.strip().lower() for tag in str(row[tags_col]).split(',')]
                            
                            # Create psychology note
                            note_data = {
                                'note_text': str(row[notes_col]) if notes_col != "None" else "",
                                'confidence_score': confidence,
                                'self_tags': tags,
                                'created_at': date_val
                            }
                            
                            # Add trade_id if available
                            if trade_id_col != "None" and pd.notna(row[trade_id_col]):
                                note_data['trade_id'] = int(row[trade_id_col])
                            
                            # Create note
                            psych_dal.create_psychology_note(note_data)
                            imported_count += 1
                            
                        except Exception as e:
                            st.warning(f"Error importing row {index}: {str(e)}")
                            continue
                    
                    st.success(f"✅ Successfully imported {imported_count} psychology records!")
                    
                    # AI Analysis
                    if ai_engine.enabled:
                        st.subheader("🤖 AI Psychology Analysis")
                        with st.spinner("Analyzing emotional patterns..."):
                            try:
                                # Get all notes for analysis
                                all_notes = psych_dal.get_recent_notes(limit=1000)
                                
                                if all_notes:
                                    # Prepare data for AI analysis
                                    psychology_text = "\n".join([note.note_text for note in all_notes if note.note_text])
                                    
                                    if psychology_text:
                                        analysis = ai_engine.analyze_psychology_with_image(psychology_text)
                                        
                                        if analysis:
                                            col1, col2, col3 = st.columns(3)
                                            with col1:
                                                st.metric("Overall Sentiment", f"{analysis.get('sentiment_score', 0):.2f}")
                                            with col2:
                                                st.metric("Confidence Trend", f"{analysis.get('confidence_score', 0):.2f}")
                                            with col3:
                                                st.metric("Emotional Stability", f"{analysis.get('fear_score', 0):.2f}")
                                            
                                            if 'key_insights' in analysis:
                                                st.subheader("🧠 Key Psychology Insights")
                                                for insight in analysis['key_insights']:
                                                    st.write(f"• {insight}")
                            except Exception as e:
                                st.warning(f"AI analysis failed: {str(e)}")
        except Exception as e:
            st.error(f"Error reading CSV file: {str(e)}")

elif upload_option == "Manual Entry":
    st.subheader("✍️ Manual Psychology Entry")
    
    with st.form("psychology_manual_form"):
        date = st.date_input("Date", value=datetime.now().date())
        time = st.time_input("Time", value=datetime.now().time())
        
        emotional_state = st.selectbox(
            "Emotional State",
            ["Confident", "Anxious", "Excited", "Fearful", "Greedy", "Patient", "Impatient", "Frustrated", "Calm", "Stressed", "Optimistic", "Pessimistic"]
        )
        
        confidence_level = st.slider("Confidence Level", 1, 10, 5)
        
        notes = st.text_area(
            "Psychology Notes",
            placeholder="Describe your emotional state, mindset, and thoughts about trading..."
        )
        
        tags = st.text_input(
            "Tags (comma-separated)",
            placeholder="patient, calm, focused, etc."
        )
        
        trade_id = st.number_input("Trade ID (optional)", min_value=1, value=None, step=1)
        
        submitted = st.form_submit_button("💾 Add Psychology Note", type="primary")
        
        if submitted and notes:
            try:
                db = get_db_session()
                psych_dal = PsychologyDAL(db)
                
                # Combine date and time
                timestamp = datetime.combine(date, time)
                
                # Parse tags
                tag_list = [tag.strip().lower() for tag in tags.split(',')] if tags else []
                
                note_data = {
                    'note_text': notes,
                    'confidence_score': confidence_level / 10.0,
                    'self_tags': tag_list,
                    'created_at': timestamp
                }
                
                if trade_id:
                    note_data['trade_id'] = trade_id
                
                psych_dal.create_psychology_note(note_data)
                st.success("✅ Psychology note added successfully!")
                
            except Exception as e:
                st.error(f"Error adding psychology note: {e}")

elif upload_option == "Text File Upload":
    st.subheader("📄 Text File Upload")
    
    st.markdown("""
    **Text Format Expected:**
    - One psychology note per line
    - Format: `YYYY-MM-DD HH:MM | Emotional_State | Confidence | Notes`
    - Example: `2024-01-01 14:30 | Confident | 8 | Felt good about this setup, patient waiting`
    """)
    
    uploaded_text = st.file_uploader(
        "Upload psychology text file",
        type=['txt'],
        help="Upload a text file with your psychology notes"
    )
    
    if uploaded_text:
        content = uploaded_text.read().decode('utf-8')
        lines = content.strip().split('\n')
        
        st.success(f"✅ Loaded {len(lines)} psychology notes")
        
        # Show preview
        st.subheader("📊 Data Preview")
        st.text_area("Preview", content[:500] + "..." if len(content) > 500 else content, height=200)
        
        if st.button("💾 Import Psychology Notes", type="primary"):
            with st.spinner("Importing psychology notes..."):
                db = get_db_session()
                psych_dal = PsychologyDAL(db)
                
                imported_count = 0
                for line in lines:
                    try:
                        if '|' in line:
                            parts = [part.strip() for part in line.split('|')]
                            if len(parts) >= 4:
                                timestamp_str, emotion, confidence_str, notes = parts[:4]
                                
                                # Parse timestamp
                                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M')
                                
                                # Parse confidence
                                confidence = float(confidence_str) / 10.0
                                
                                # Create psychology note
                                note_data = {
                                    'note_text': notes,
                                    'confidence_score': confidence,
                                    'self_tags': [emotion.lower()],
                                    'created_at': timestamp
                                }
                                
                                psych_dal.create_psychology_note(note_data)
                                imported_count += 1
                                
                    except Exception as e:
                        st.warning(f"Error importing line: {line[:50]}... - {str(e)}")
                        continue
                
                st.success(f"✅ Successfully imported {imported_count} psychology notes!")

# Psychology Analysis Section
st.markdown("---")
st.subheader("📊 Psychology Analysis")

db = get_db_session()
psych_dal = PsychologyDAL(db)
recent_notes = psych_dal.get_recent_notes(limit=50)

if recent_notes:
    st.success(f"📈 Found {len(recent_notes)} psychology records in database")
    
    # Show recent psychology notes
    st.subheader("📋 Recent Psychology Notes")
    for note in recent_notes[:10]:
        with st.expander(f"{note.created_at.strftime('%Y-%m-%d %H:%M')} - {', '.join(note.self_tags) if note.self_tags else 'No tags'}"):
            st.write(note.note_text)
            if note.confidence_score:
                st.write(f"**Confidence:** {int(note.confidence_score * 10)}/10")
else:
    st.info("No psychology data found. Start by importing your psychology notes!")

db.close()

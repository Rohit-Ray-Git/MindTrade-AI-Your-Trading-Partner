"""
Psychology Analyzer Agent - Analyzes trading psychology and emotions
"""
import os
from typing import Dict, Any, Optional, List
from crewai import Agent, Task, Crew
from crewai_tools import BaseTool
from langchain_google_genai import ChatGoogleGenerativeAI
from loguru import logger
import json
import re

class SentimentAnalysisTool(BaseTool):
    """Custom tool for sentiment analysis of trading notes"""
    name: str = "sentiment_analysis_tool"
    description: str = "Analyzes sentiment and emotions in trading psychology notes"
    
    def _run(self, note_text: str) -> str:
        """Analyze sentiment of psychology note"""
        try:
            # Simple keyword-based sentiment analysis as fallback
            fear_keywords = ["scared", "afraid", "fear", "panic", "nervous", "worried", "anxious"]
            greed_keywords = ["greedy", "more", "bigger", "maximum", "all-in", "leverage"]
            fomo_keywords = ["fomo", "missing", "everyone", "late", "catch up"]
            revenge_keywords = ["revenge", "get back", "angry", "frustrated", "mad"]
            patience_keywords = ["patient", "wait", "calm", "disciplined", "planned"]
            confidence_keywords = ["confident", "sure", "certain", "strong", "conviction"]
            
            text_lower = note_text.lower()
            
            fear_score = sum(1 for keyword in fear_keywords if keyword in text_lower) / len(fear_keywords)
            greed_score = sum(1 for keyword in greed_keywords if keyword in text_lower) / len(greed_keywords)
            fomo_score = sum(1 for keyword in fomo_keywords if keyword in text_lower) / len(fomo_keywords)
            revenge_score = sum(1 for keyword in revenge_keywords if keyword in text_lower) / len(revenge_keywords)
            patience_score = sum(1 for keyword in patience_keywords if keyword in text_lower) / len(patience_keywords)
            confidence_score = sum(1 for keyword in confidence_keywords if keyword in text_lower) / len(confidence_keywords)
            
            # Calculate overall sentiment
            positive_indicators = patience_score + confidence_score
            negative_indicators = fear_score + greed_score + fomo_score + revenge_score
            sentiment_score = positive_indicators - negative_indicators
            
            result = {
                "sentiment_score": max(-1, min(1, sentiment_score)),
                "fear_score": min(1, fear_score * 2),
                "greed_score": min(1, greed_score * 2),
                "fomo_score": min(1, fomo_score * 2),
                "revenge_score": min(1, revenge_score * 2),
                "patience_score": min(1, patience_score * 2),
                "confidence_score": min(1, confidence_score * 2)
            }
            
            return json.dumps(result)
            
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            return json.dumps({"error": str(e)})

class PsychologyAgent:
    """Psychology Analyzer Agent for trading psychology analysis"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        
        # Initialize LLM
        if self.api_key:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                google_api_key=self.api_key,
                temperature=0.4,
                max_output_tokens=2048
            )
            self.enabled = True
        else:
            self.llm = None
            self.enabled = False
            logger.warning("No Google API key found. Psychology Agent disabled.")
        
        # Initialize tools
        self.sentiment_tool = SentimentAnalysisTool()
        
        # Create agent
        if self.enabled:
            self.agent = Agent(
                role="Trading Psychology Specialist",
                goal="Analyze trading psychology patterns, emotions, and behavioral tendencies to improve trading performance",
                backstory="""You are a certified trading psychologist with expertise in behavioral finance 
                and emotional intelligence. You help traders identify their psychological patterns, emotional 
                triggers, and behavioral biases that impact their trading performance. Your approach combines 
                NLP analysis with psychological insights to provide actionable recommendations for mental 
                discipline and emotional control in trading.""",
                verbose=True,
                allow_delegation=False,
                llm=self.llm,
                tools=[self.sentiment_tool]
            )
    
    def analyze_psychology_note(self, note_text: str, trade_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze a psychology note for emotional patterns and insights"""
        if not self.enabled:
            return self._get_default_psychology_analysis()
        
        try:
            # Prepare context
            context = f"""
            Psychology Note: "{note_text}"
            """
            
            if trade_data:
                context += f"""
                
                Trade Context:
                - Symbol: {trade_data.get('symbol')}
                - P&L: ${trade_data.get('pnl', 0)}
                - R-Multiple: {trade_data.get('r_multiple', 0)}
                - Setup: {trade_data.get('setup_name', 'Unknown')}
                - Outcome: {'Winning' if trade_data.get('pnl', 0) > 0 else 'Losing'} trade
                """
            
            # Create analysis task
            task_description = f"""
            Analyze this trading psychology note for emotional patterns and behavioral insights:
            
            {context}
            
            Your analysis should include:
            1. Emotion Detection: Identify primary emotions (fear, greed, FOMO, revenge, patience, confidence)
            2. Sentiment Analysis: Overall sentiment score (-1 to 1)
            3. Behavioral Patterns: Identify any recurring behavioral patterns
            4. Psychological State: Assess the trader's mental state during this trade
            5. Risk Factors: Identify psychological risk factors that might affect future trades
            6. Recommendations: Specific psychological strategies and improvements
            7. NLP Tags: Extract relevant psychological tags from the text
            
            Use the sentiment_analysis_tool to get quantitative emotion scores.
            
            Provide your analysis in structured JSON format with detailed insights.
            """
            
            task = Task(
                description=task_description,
                agent=self.agent,
                expected_output="Detailed psychology analysis in JSON format with emotion scores, patterns, and recommendations"
            )
            
            # Create crew and execute
            crew = Crew(
                agents=[self.agent],
                tasks=[task],
                verbose=True
            )
            
            result = crew.kickoff()
            
            # Parse result
            try:
                if isinstance(result, str):
                    # Try to extract JSON from the result
                    json_match = re.search(r'\{.*\}', result, re.DOTALL)
                    if json_match:
                        analysis = json.loads(json_match.group())
                    else:
                        # Fallback to structured response
                        analysis = self._structure_psychology_response(result, note_text)
                else:
                    analysis = result
                
                # Ensure we have sentiment scores using our tool
                sentiment_result = json.loads(self.sentiment_tool._run(note_text))
                if "error" not in sentiment_result:
                    analysis.update(sentiment_result)
                
                logger.info(f"Psychology analysis completed for note: {note_text[:50]}...")
                return analysis
                
            except json.JSONDecodeError:
                # If JSON parsing fails, structure the response
                return self._structure_psychology_response(str(result), note_text)
            
        except Exception as e:
            logger.error(f"Error in psychology analysis: {e}")
            return self._get_default_psychology_analysis()
    
    def analyze_multiple_notes(self, notes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze multiple psychology notes to identify patterns"""
        if not self.enabled:
            return self._get_default_pattern_analysis()
        
        try:
            # Prepare notes context
            notes_context = ""
            for i, note in enumerate(notes[:10], 1):  # Limit to 10 recent notes
                notes_context += f"""
                Note {i}:
                - Text: "{note.get('note_text', '')}"
                - Date: {note.get('created_at', '')}
                - Trade P&L: ${note.get('trade_pnl', 0)}
                - Symbol: {note.get('symbol', '')}
                ---
                """
            
            # Create pattern analysis task
            task_description = f"""
            Analyze these trading psychology notes to identify recurring patterns and trends:
            
            {notes_context}
            
            Your analysis should include:
            1. Emotional Patterns: Recurring emotional states and triggers
            2. Behavioral Trends: Consistent behavioral patterns across trades
            3. Performance Correlation: How emotions correlate with trade performance
            4. Risk Behaviors: Identify risky psychological behaviors
            5. Positive Patterns: Identify beneficial psychological patterns
            6. Evolution Analysis: How the trader's psychology has evolved over time
            7. Recommendations: Strategic psychological improvements
            
            Provide your analysis in structured JSON format.
            """
            
            task = Task(
                description=task_description,
                agent=self.agent,
                expected_output="Pattern analysis in JSON format with trends, correlations, and strategic recommendations"
            )
            
            # Create crew and execute
            crew = Crew(
                agents=[self.agent],
                tasks=[task],
                verbose=True
            )
            
            result = crew.kickoff()
            
            # Parse result
            try:
                if isinstance(result, str):
                    json_match = re.search(r'\{.*\}', result, re.DOTALL)
                    if json_match:
                        analysis = json.loads(json_match.group())
                    else:
                        analysis = self._structure_pattern_response(result)
                else:
                    analysis = result
                
                logger.info("Psychology pattern analysis completed")
                return analysis
                
            except json.JSONDecodeError:
                return self._structure_pattern_response(str(result))
            
        except Exception as e:
            logger.error(f"Error in psychology pattern analysis: {e}")
            return self._get_default_pattern_analysis()
    
    def _structure_psychology_response(self, analysis_text: str, note_text: str) -> Dict[str, Any]:
        """Structure the psychology response when JSON parsing fails"""
        # Get sentiment scores
        sentiment_result = json.loads(self.sentiment_tool._run(note_text))
        
        return {
            "sentiment_score": sentiment_result.get("sentiment_score", 0.0),
            "confidence_score": sentiment_result.get("confidence_score", 0.5),
            "fear_score": sentiment_result.get("fear_score", 0.0),
            "greed_score": sentiment_result.get("greed_score", 0.0),
            "patience_score": sentiment_result.get("patience_score", 0.5),
            "fomo_score": sentiment_result.get("fomo_score", 0.0),
            "revenge_score": sentiment_result.get("revenge_score", 0.0),
            "nlp_tags": self._extract_tags(note_text),
            "key_insights": ["Analyzed using Psychology Agent"],
            "behavioral_patterns": ["Standard trading psychology patterns detected"],
            "recommendations": [
                "Maintain emotional discipline",
                "Focus on process over outcome",
                "Practice mindfulness while trading"
            ],
            "agent_analysis": analysis_text[:500] + "..." if len(analysis_text) > 500 else analysis_text
        }
    
    def _structure_pattern_response(self, analysis_text: str) -> Dict[str, Any]:
        """Structure the pattern response when JSON parsing fails"""
        return {
            "emotional_patterns": ["Fear during losses", "Greed during wins"],
            "behavioral_trends": ["Impulsive decision making", "Size increase after wins"],
            "performance_correlation": {
                "fear_impact": "Negative correlation with performance",
                "patience_impact": "Positive correlation with performance"
            },
            "risk_behaviors": ["Revenge trading", "Overconfidence after wins"],
            "positive_patterns": ["Following trading plan", "Proper risk management"],
            "evolution_analysis": "Trader psychology evolving positively",
            "recommendations": [
                "Implement pre-trade emotional check-ins",
                "Develop meditation routine",
                "Keep psychology journal"
            ],
            "agent_analysis": analysis_text[:500] + "..." if len(analysis_text) > 500 else analysis_text
        }
    
    def _extract_tags(self, note_text: str) -> List[str]:
        """Extract NLP tags from note text"""
        tags = []
        text_lower = note_text.lower()
        
        tag_keywords = {
            "fear": ["scared", "afraid", "fear", "panic", "nervous"],
            "greed": ["greedy", "more", "bigger", "maximum"],
            "fomo": ["fomo", "missing", "late"],
            "revenge": ["revenge", "angry", "frustrated"],
            "patience": ["patient", "wait", "calm", "disciplined"],
            "confidence": ["confident", "sure", "strong"],
            "stress": ["stress", "pressure", "overwhelming"],
            "discipline": ["discipline", "plan", "rules"],
            "excitement": ["excited", "euphoric", "high"],
            "doubt": ["doubt", "uncertain", "confused"]
        }
        
        for tag, keywords in tag_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                tags.append(tag)
        
        return tags if tags else ["neutral"]
    
    def _get_default_psychology_analysis(self) -> Dict[str, Any]:
        """Default psychology analysis when agent is disabled"""
        return {
            "sentiment_score": 0.0,
            "confidence_score": 0.5,
            "fear_score": 0.0,
            "greed_score": 0.0,
            "patience_score": 0.5,
            "fomo_score": 0.0,
            "revenge_score": 0.0,
            "nlp_tags": ["neutral"],
            "key_insights": ["Psychology Agent not available"],
            "behavioral_patterns": ["Enable AI features for pattern analysis"],
            "recommendations": ["Enable AI features for personalized recommendations"]
        }
    
    def _get_default_pattern_analysis(self) -> Dict[str, Any]:
        """Default pattern analysis when agent is disabled"""
        return {
            "emotional_patterns": [],
            "behavioral_trends": [],
            "performance_correlation": {},
            "risk_behaviors": [],
            "positive_patterns": [],
            "evolution_analysis": "Psychology Agent not available",
            "recommendations": ["Enable AI features for pattern analysis"]
        }

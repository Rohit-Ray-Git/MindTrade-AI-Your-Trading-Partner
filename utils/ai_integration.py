"""
AI Integration with Google Gemini 2.5 Flash
"""
import os
import json
import base64
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage
from loguru import logger
from PIL import Image
import io
from datetime import datetime

class GeminiAI:
    """Google Gemini AI integration for trading analysis with image support"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Gemini AI"""
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            logger.warning("No Google API key found. AI features will be disabled.")
            self.enabled = False
            return
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.enabled = True
        
        # Initialize LangChain integration
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=self.api_key,
            temperature=0.3,
            max_output_tokens=2048
        )
        
        # Create images directory
        self.images_dir = Path("data/images")
        self.images_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("Gemini AI initialized successfully with image support")
    
    def save_image(self, image_data: Union[str, bytes], trade_id: int, image_type: str = "screenshot") -> str:
        """Save image to disk with organized structure"""
        try:
            # Create trade-specific directory
            trade_dir = self.images_dir / f"trade_{trade_id}"
            trade_dir.mkdir(exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{image_type}_{timestamp}.png"
            filepath = trade_dir / filename
            
            # Save image
            if isinstance(image_data, str):
                # Base64 encoded image
                image_bytes = base64.b64decode(image_data)
            else:
                image_bytes = image_data
            
            with open(filepath, 'wb') as f:
                f.write(image_bytes)
            
            logger.info(f"Image saved: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error saving image: {e}")
            return ""
    
    def analyze_trade_with_image(self, trade_data: Dict[str, Any], image_path: Optional[str] = None) -> Dict[str, Any]:
        """Analyze trade with optional image using Gemini"""
        if not self.enabled:
            return self._get_default_trade_analysis()
        
        try:
            # Prepare trade information
            trade_info = f"""
            Trade Data:
            - Symbol: {trade_data.get('symbol')}
            - Direction: {trade_data.get('direction')}
            - Entry: ${trade_data.get('entry_price')}
            - Stop: ${trade_data.get('stop_price')}
            - Exit: ${trade_data.get('exit_price')}
            - P&L: ${trade_data.get('pnl')}
            - R-Multiple: {trade_data.get('r_multiple')}
            - Setup: {trade_data.get('setup_name', 'Unknown')}
            - Logic: {trade_data.get('logic', 'No logic provided')}
            """
            
            if image_path and os.path.exists(image_path):
                # Load and analyze image
                image = Image.open(image_path)
                
                prompt = f"""
                Analyze this trading screenshot and the trade data to provide comprehensive insights.
                
                {trade_info}
                
                Please analyze the chart/screenshot and provide a JSON response with the following structure:
                {{
                    "chart_analysis": {{
                        "market_structure": "string (trending/ranging/consolidating)",
                        "key_levels": ["level1", "level2"],
                        "setup_quality": "excellent/good/fair/poor",
                        "entry_timing": "good/fair/poor",
                        "exit_timing": "good/fair/poor",
                        "risk_reward_ratio": "string",
                        "market_context": "string"
                    }},
                    "trade_quality_score": float (0 to 1),
                    "risk_management_score": float (0 to 1),
                    "execution_score": float (0 to 1),
                    "setup_analysis": {{
                        "setup_quality": "excellent/good/fair/poor",
                        "setup_notes": "string",
                        "chart_patterns": ["pattern1", "pattern2"]
                    }},
                    "risk_analysis": {{
                        "position_sizing": "appropriate/too_large/too_small",
                        "stop_placement": "good/fair/poor",
                        "risk_notes": "string"
                    }},
                    "execution_analysis": {{
                        "entry_timing": "good/fair/poor",
                        "exit_timing": "good/fair/poor",
                        "execution_notes": "string"
                    }},
                    "improvement_suggestions": ["suggestion1", "suggestion2"],
                    "key_learnings": ["learning1", "learning2"],
                    "chart_insights": ["insight1", "insight2"]
                }}
                
                Focus on providing actionable insights based on both the trade data and chart analysis.
                """
                
                response = self.model.generate_content([prompt, image])
            else:
                # Text-only analysis
                prompt = f"""
                Analyze the following trade and provide structured insights:
                
                {trade_info}
                
                Please provide a JSON response with the following structure:
                {{
                    "trade_quality_score": float (0 to 1),
                    "risk_management_score": float (0 to 1),
                    "execution_score": float (0 to 1),
                    "setup_analysis": {{
                        "setup_quality": "excellent/good/fair/poor",
                        "setup_notes": "string"
                    }},
                    "risk_analysis": {{
                        "position_sizing": "appropriate/too_large/too_small",
                        "stop_placement": "good/fair/poor",
                        "risk_notes": "string"
                    }},
                    "execution_analysis": {{
                        "entry_timing": "good/fair/poor",
                        "exit_timing": "good/fair/poor",
                        "execution_notes": "string"
                    }},
                    "improvement_suggestions": ["suggestion1", "suggestion2"],
                    "key_learnings": ["learning1", "learning2"]
                }}
                
                Focus on providing actionable insights for trade improvement.
                """
                
                response = self.model.generate_content(prompt)
            
            result = json.loads(response.text)
            
            logger.info(f"Trade analysis completed for {trade_data.get('symbol')} with image: {bool(image_path)}")
            return result
            
        except Exception as e:
            logger.error(f"Error in trade analysis: {e}")
            return self._get_default_trade_analysis()
    
    def analyze_market_screenshot(self, image_path: str, context: str = "") -> Dict[str, Any]:
        """Analyze market screenshot for setup identification and analysis"""
        if not self.enabled:
            return self._get_default_market_analysis()
        
        try:
            image = Image.open(image_path)
            
            prompt = f"""
            Analyze this market screenshot and identify potential trading setups and opportunities.
            
            Context: {context}
            
            Please provide a JSON response with the following structure:
            {{
                "market_analysis": {{
                    "market_structure": "string (trending/ranging/consolidating)",
                    "timeframe": "string (if visible)",
                    "key_levels": ["level1", "level2", "level3"],
                    "support_resistance": ["support1", "resistance1"],
                    "volume_analysis": "string",
                    "momentum": "string"
                }},
                "potential_setups": [
                    {{
                        "setup_type": "string",
                        "confidence": float (0 to 1),
                        "entry_zone": "string",
                        "stop_loss": "string",
                        "target": "string",
                        "risk_reward": "string",
                        "reasoning": "string"
                    }}
                ],
                "risk_assessment": {{
                    "market_volatility": "low/medium/high",
                    "setup_quality": "excellent/good/fair/poor",
                    "risk_level": "low/medium/high",
                    "notes": "string"
                }},
                "recommendations": ["rec1", "rec2"],
                "key_observations": ["obs1", "obs2"]
            }}
            
            Focus on identifying high-probability setups and providing actionable trading insights.
            """
            
            response = self.model.generate_content([prompt, image])
            result = json.loads(response.text)
            
            logger.info(f"Market screenshot analysis completed")
            return result
            
        except Exception as e:
            logger.error(f"Error in market screenshot analysis: {e}")
            return self._get_default_market_analysis()
    
    def analyze_psychology_with_image(self, note_text: str, image_path: Optional[str] = None) -> Dict[str, Any]:
        """Analyze psychology note with optional image (e.g., journal entry, mood tracking)"""
        if not self.enabled:
            return self._get_default_psychology_analysis()
        
        try:
            prompt = f"""
            Analyze the following trading psychology note and provide structured insights:
            
            Note: "{note_text}"
            
            Please provide a JSON response with the following structure:
            {{
                "sentiment_score": float (-1 to 1, where -1 is very negative, 1 is very positive),
                "confidence_score": float (0 to 1),
                "fear_score": float (0 to 1),
                "greed_score": float (0 to 1),
                "patience_score": float (0 to 1),
                "fomo_score": float (0 to 1),
                "revenge_score": float (0 to 1),
                "nlp_tags": ["tag1", "tag2", "tag3"],
                "key_insights": ["insight1", "insight2"],
                "behavioral_patterns": ["pattern1", "pattern2"],
                "recommendations": ["rec1", "rec2"]
            }}
            
            Focus on identifying emotional states, behavioral patterns, and actionable insights for trading psychology improvement.
            """
            
            if image_path and os.path.exists(image_path):
                image = Image.open(image_path)
                response = self.model.generate_content([prompt, image])
            else:
                response = self.model.generate_content(prompt)
            
            result = json.loads(response.text)
            
            logger.info(f"Psychology analysis completed for note: {note_text[:50]}...")
            return result
            
        except Exception as e:
            logger.error(f"Error in psychology analysis: {e}")
            return self._get_default_psychology_analysis()
    
    def generate_coaching_advice(self, recent_trades: List[Dict[str, Any]], psychology_notes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate personalized coaching advice"""
        if not self.enabled:
            return self._get_default_coaching_advice()
        
        try:
            # Prepare trade summary
            total_trades = len(recent_trades)
            winning_trades = len([t for t in recent_trades if t.get('pnl', 0) > 0])
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            total_pnl = sum(t.get('pnl', 0) for t in recent_trades)
            
            # Prepare psychology summary
            avg_sentiment = sum(n.get('sentiment_score', 0) for n in psychology_notes) / len(psychology_notes) if psychology_notes else 0
            common_emotions = self._extract_common_emotions(psychology_notes)
            
            prompt = f"""
            Generate personalized coaching advice based on the following trading performance and psychology data:
            
            Performance Summary:
            - Total Trades: {total_trades}
            - Win Rate: {win_rate:.1f}%
            - Total P&L: ${total_pnl:.2f}
            - Average Sentiment: {avg_sentiment:.2f}
            - Common Emotions: {', '.join(common_emotions)}
            
            Recent Trades: {json.dumps(recent_trades[:5], indent=2)}
            Psychology Notes: {json.dumps(psychology_notes[:5], indent=2)}
            
            Please provide a JSON response with the following structure:
            {{
                "overall_assessment": {{
                    "strengths": ["strength1", "strength2"],
                    "weaknesses": ["weakness1", "weakness2"],
                    "current_state": "excellent/good/fair/needs_improvement"
                }},
                "psychology_coaching": {{
                    "emotional_patterns": ["pattern1", "pattern2"],
                    "mindset_advice": ["advice1", "advice2"],
                    "stress_management": ["tip1", "tip2"]
                }},
                "technical_coaching": {{
                    "setup_improvements": ["improvement1", "improvement2"],
                    "risk_management": ["tip1", "tip2"],
                    "execution_tips": ["tip1", "tip2"]
                }},
                "action_plan": {{
                    "immediate_actions": ["action1", "action2"],
                    "weekly_goals": ["goal1", "goal2"],
                    "monthly_objectives": ["objective1", "objective2"]
                }},
                "motivational_message": "string"
            }}
            
            Focus on providing actionable, specific advice that addresses both technical and psychological aspects of trading.
            """
            
            response = self.model.generate_content(prompt)
            result = json.loads(response.text)
            
            logger.info("Coaching advice generated successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error generating coaching advice: {e}")
            return self._get_default_coaching_advice()
    
    def detect_patterns(self, trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect trading patterns using Gemini"""
        if not self.enabled:
            return self._get_default_pattern_analysis()
        
        try:
            prompt = f"""
            Analyze the following trades to detect patterns and recurring behaviors:
            
            Trades: {json.dumps(trades, indent=2)}
            
            Please provide a JSON response with the following structure:
            {{
                "setup_patterns": [
                    {{
                        "pattern_name": "string",
                        "frequency": int,
                        "win_rate": float,
                        "avg_r_multiple": float,
                        "description": "string"
                    }}
                ],
                "timing_patterns": [
                    {{
                        "pattern_name": "string",
                        "frequency": int,
                        "description": "string"
                    }}
                ],
                "risk_patterns": [
                    {{
                        "pattern_name": "string",
                        "frequency": int,
                        "impact": "positive/negative",
                        "description": "string"
                    }}
                ],
                "behavioral_patterns": [
                    {{
                        "pattern_name": "string",
                        "frequency": int,
                        "impact": "positive/negative",
                        "description": "string"
                    }}
                ],
                "recommendations": ["rec1", "rec2"]
            }}
            
            Focus on identifying both profitable and problematic patterns that can inform trading decisions.
            """
            
            response = self.model.generate_content(prompt)
            result = json.loads(response.text)
            
            logger.info("Pattern analysis completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error in pattern detection: {e}")
            return self._get_default_pattern_analysis()
    
    def _extract_common_emotions(self, psychology_notes: List[Dict[str, Any]]) -> List[str]:
        """Extract common emotions from psychology notes"""
        emotions = []
        for note in psychology_notes:
            if note.get('fear_score', 0) > 0.5:
                emotions.append('Fear')
            if note.get('greed_score', 0) > 0.5:
                emotions.append('Greed')
            if note.get('patience_score', 0) > 0.5:
                emotions.append('Patience')
            if note.get('fomo_score', 0) > 0.5:
                emotions.append('FOMO')
            if note.get('revenge_score', 0) > 0.5:
                emotions.append('Revenge')
        
        # Return unique emotions
        return list(set(emotions))
    
    def _get_default_psychology_analysis(self) -> Dict[str, Any]:
        """Default psychology analysis when AI is disabled"""
        return {
            "sentiment_score": 0.0,
            "confidence_score": 0.5,
            "fear_score": 0.0,
            "greed_score": 0.0,
            "patience_score": 0.5,
            "fomo_score": 0.0,
            "revenge_score": 0.0,
            "nlp_tags": ["neutral"],
            "key_insights": ["AI analysis not available"],
            "behavioral_patterns": ["No patterns detected"],
            "recommendations": ["Enable AI features for detailed analysis"]
        }
    
    def _get_default_trade_analysis(self) -> Dict[str, Any]:
        """Default trade analysis when AI is disabled"""
        return {
            "trade_quality_score": 0.5,
            "risk_management_score": 0.5,
            "execution_score": 0.5,
            "setup_analysis": {
                "setup_quality": "fair",
                "setup_notes": "AI analysis not available"
            },
            "risk_analysis": {
                "position_sizing": "fair",
                "stop_placement": "fair",
                "risk_notes": "Enable AI features for detailed analysis"
            },
            "execution_analysis": {
                "entry_timing": "fair",
                "exit_timing": "fair",
                "execution_notes": "AI analysis not available"
            },
            "improvement_suggestions": ["Enable AI features for detailed suggestions"],
            "key_learnings": ["Enable AI features for detailed insights"]
        }
    
    def _get_default_market_analysis(self) -> Dict[str, Any]:
        """Default market analysis when AI is disabled"""
        return {
            "market_analysis": {
                "market_structure": "unknown",
                "timeframe": "unknown",
                "key_levels": [],
                "support_resistance": [],
                "volume_analysis": "AI analysis not available",
                "momentum": "unknown"
            },
            "potential_setups": [],
            "risk_assessment": {
                "market_volatility": "unknown",
                "setup_quality": "fair",
                "risk_level": "medium",
                "notes": "Enable AI features for detailed analysis"
            },
            "recommendations": ["Enable AI features for setup identification"],
            "key_observations": ["Enable AI features for detailed observations"]
        }
    
    def _get_default_coaching_advice(self) -> Dict[str, Any]:
        """Default coaching advice when AI is disabled"""
        return {
            "overall_assessment": {
                "strengths": ["Enable AI for detailed assessment"],
                "weaknesses": ["Enable AI for detailed assessment"],
                "current_state": "fair"
            },
            "psychology_coaching": {
                "emotional_patterns": ["Enable AI for pattern detection"],
                "mindset_advice": ["Enable AI features for personalized advice"],
                "stress_management": ["Enable AI features for stress management tips"]
            },
            "technical_coaching": {
                "setup_improvements": ["Enable AI for setup analysis"],
                "risk_management": ["Enable AI for risk management tips"],
                "execution_tips": ["Enable AI for execution analysis"]
            },
            "action_plan": {
                "immediate_actions": ["Enable AI features"],
                "weekly_goals": ["Enable AI for goal setting"],
                "monthly_objectives": ["Enable AI for objective planning"]
            },
            "motivational_message": "Enable AI features for personalized coaching and insights."
        }
    
    def _get_default_pattern_analysis(self) -> Dict[str, Any]:
        """Default pattern analysis when AI is disabled"""
        return {
            "setup_patterns": [],
            "timing_patterns": [],
            "risk_patterns": [],
            "behavioral_patterns": [],
            "recommendations": ["Enable AI features for pattern detection"]
        }

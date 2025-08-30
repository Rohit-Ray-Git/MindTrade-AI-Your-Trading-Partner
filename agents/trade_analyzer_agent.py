"""
Trade Analyzer Agent - Analyzes individual trades with chart screenshots
"""
import os
from typing import Dict, Any, Optional
from crewai import Agent, Task, Crew
from crewai_tools import FileReadTool, BaseTool
from langchain_google_genai import ChatGoogleGenerativeAI
from utils.ai_integration import GeminiAI
from loguru import logger
import json
from PIL import Image

class ChartAnalysisTool(BaseTool):
    """Custom tool for chart analysis"""
    name: str = "chart_analysis_tool"
    description: str = "Analyzes trading charts and screenshots to identify patterns, levels, and trade quality"
    
    def __init__(self):
        super().__init__()
        self.gemini_ai = GeminiAI()
    
    def _run(self, image_path: str, trade_data: str) -> str:
        """Analyze chart with trade data"""
        try:
            trade_info = json.loads(trade_data)
            if self.gemini_ai.enabled and os.path.exists(image_path):
                analysis = self.gemini_ai.analyze_trade_with_image(trade_info, image_path)
                return json.dumps(analysis, indent=2)
            else:
                return json.dumps({"error": "AI not enabled or image not found"})
        except Exception as e:
            logger.error(f"Chart analysis error: {e}")
            return json.dumps({"error": str(e)})

class TradeAnalyzerAgent:
    """Trade Analyzer Agent for detailed trade analysis"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        
        # Initialize LLM
        if self.api_key:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                google_api_key=self.api_key,
                temperature=0.3,
                max_output_tokens=2048
            )
            self.enabled = True
        else:
            self.llm = None
            self.enabled = False
            logger.warning("No Google API key found. Trade Analyzer Agent disabled.")
        
        # Initialize tools
        self.chart_tool = ChartAnalysisTool()
        self.file_tool = FileReadTool()
        
        # Create agent
        if self.enabled:
            self.agent = Agent(
                role="Senior Trading Analyst",
                goal="Analyze trades comprehensively including chart patterns, risk management, and execution quality",
                backstory="""You are a professional trading analyst with 15+ years of experience in 
                financial markets. You specialize in technical analysis, risk management, and trade 
                execution assessment. Your expertise includes identifying chart patterns, support/resistance 
                levels, and providing actionable insights for trade improvement.""",
                verbose=True,
                allow_delegation=False,
                llm=self.llm,
                tools=[self.chart_tool, self.file_tool]
            )
    
    def analyze_trade(self, trade_data: Dict[str, Any], image_path: Optional[str] = None) -> Dict[str, Any]:
        """Analyze a single trade with optional chart screenshot"""
        if not self.enabled:
            return self._get_default_analysis()
        
        try:
            # Prepare trade information
            trade_context = f"""
            Trade Details:
            - Symbol: {trade_data.get('symbol')}
            - Direction: {trade_data.get('direction')}
            - Entry Price: ${trade_data.get('entry_price')}
            - Stop Loss: ${trade_data.get('stop_price')}
            - Exit Price: ${trade_data.get('exit_price')}
            - Quantity: {trade_data.get('quantity')}
            - P&L: ${trade_data.get('pnl')}
            - R-Multiple: {trade_data.get('r_multiple')}
            - Setup Type: {trade_data.get('setup_name', 'Unknown')}
            - Trade Logic: {trade_data.get('logic', 'No logic provided')}
            - Trade Time: {trade_data.get('trade_time')}
            """
            
            # Create analysis task
            if image_path and os.path.exists(image_path):
                task_description = f"""
                Analyze this trade comprehensively using both the trade data and chart screenshot:
                
                {trade_context}
                
                Chart Screenshot Path: {image_path}
                
                Your analysis should include:
                1. Chart Analysis: Market structure, key levels, pattern recognition
                2. Trade Quality Assessment: Entry timing, exit timing, setup quality
                3. Risk Management Evaluation: Position sizing, stop placement, R:R ratio
                4. Execution Assessment: Was the trade executed according to plan?
                5. Improvement Suggestions: Specific actionable recommendations
                6. Key Learnings: What can be learned from this trade?
                
                Provide your analysis in structured JSON format with detailed insights.
                Use the chart_analysis_tool to analyze the screenshot.
                """
            else:
                task_description = f"""
                Analyze this trade based on the available data:
                
                {trade_context}
                
                Your analysis should include:
                1. Trade Quality Assessment: Based on the numerical data
                2. Risk Management Evaluation: Position sizing, stop placement, R:R ratio
                3. Setup Analysis: Evaluate the stated setup type and logic
                4. Performance Assessment: P&L and R-multiple analysis
                5. Improvement Suggestions: Specific actionable recommendations
                6. Key Learnings: What can be learned from this trade?
                
                Provide your analysis in structured JSON format.
                """
            
            task = Task(
                description=task_description,
                agent=self.agent,
                expected_output="Detailed trade analysis in JSON format with scores, insights, and recommendations"
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
                    import re
                    json_match = re.search(r'\{.*\}', result, re.DOTALL)
                    if json_match:
                        analysis = json.loads(json_match.group())
                    else:
                        # Fallback to structured response
                        analysis = self._structure_analysis_response(result, trade_data)
                else:
                    analysis = result
                
                logger.info(f"Trade analysis completed for {trade_data.get('symbol')}")
                return analysis
                
            except json.JSONDecodeError:
                # If JSON parsing fails, structure the response
                return self._structure_analysis_response(str(result), trade_data)
            
        except Exception as e:
            logger.error(f"Error in trade analysis: {e}")
            return self._get_default_analysis()
    
    def _structure_analysis_response(self, analysis_text: str, trade_data: Dict[str, Any]) -> Dict[str, Any]:
        """Structure the analysis response when JSON parsing fails"""
        return {
            "trade_id": trade_data.get('id'),
            "symbol": trade_data.get('symbol'),
            "analysis_summary": analysis_text[:500] + "..." if len(analysis_text) > 500 else analysis_text,
            "trade_quality_score": 0.7,  # Default score
            "risk_management_score": 0.7,
            "execution_score": 0.7,
            "setup_analysis": {
                "setup_quality": "fair",
                "setup_notes": "Analyzed using AI agent",
                "chart_patterns": []
            },
            "risk_analysis": {
                "position_sizing": "appropriate",
                "stop_placement": "fair",
                "risk_notes": "Standard risk management applied"
            },
            "execution_analysis": {
                "entry_timing": "fair",
                "exit_timing": "fair",
                "execution_notes": "Trade executed as planned"
            },
            "improvement_suggestions": [
                "Consider tighter risk management",
                "Improve entry timing",
                "Document trade logic more clearly"
            ],
            "key_learnings": [
                "Follow your trading plan",
                "Maintain proper risk management",
                "Keep detailed trade records"
            ],
            "agent_analysis": analysis_text
        }
    
    def _get_default_analysis(self) -> Dict[str, Any]:
        """Default analysis when agent is disabled"""
        return {
            "trade_quality_score": 0.5,
            "risk_management_score": 0.5,
            "execution_score": 0.5,
            "setup_analysis": {
                "setup_quality": "unknown",
                "setup_notes": "Trade Analyzer Agent not available",
                "chart_patterns": []
            },
            "risk_analysis": {
                "position_sizing": "unknown",
                "stop_placement": "unknown",
                "risk_notes": "Enable AI features for detailed analysis"
            },
            "execution_analysis": {
                "entry_timing": "unknown",
                "exit_timing": "unknown",
                "execution_notes": "Trade Analyzer Agent not available"
            },
            "improvement_suggestions": ["Enable AI features for detailed suggestions"],
            "key_learnings": ["Enable AI features for detailed insights"],
            "agent_analysis": "Trade Analyzer Agent is not enabled. Please add Google API key."
        }

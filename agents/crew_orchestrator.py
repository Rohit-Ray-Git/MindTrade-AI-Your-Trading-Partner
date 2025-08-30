"""
CrewAI Orchestrator for Trading Analysis
Coordinates multiple AI agents for comprehensive trading insights
"""

import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from loguru import logger

try:
    from crewai import Agent, Task, Crew, Process
    from crewai_tools import BaseTool
    CREWAI_AVAILABLE = True
except ImportError:
    logger.warning("CrewAI not available. Using fallback implementation.")
    CREWAI_AVAILABLE = False

from .trade_analyzer_agent import TradeAnalyzerAgent
from .psychology_agent import PsychologyAgent
from .pattern_finder_agent import PatternFinderAgent
from .coach_agent import CoachAgent

@dataclass
class AnalysisResult:
    """Result container for crew analysis"""
    trade_analysis: Dict[str, Any]
    psychology_analysis: Dict[str, Any]
    pattern_analysis: Dict[str, Any]
    coaching_advice: Dict[str, Any]
    summary: str

class TradingCrewOrchestrator:
    """Orchestrates multiple AI agents for comprehensive trading analysis"""
    
    def __init__(self):
        """Initialize the crew orchestrator"""
        self.enabled = CREWAI_AVAILABLE and bool(os.getenv("GOOGLE_API_KEY"))
        
        if self.enabled:
            self._initialize_crew()
        else:
            logger.warning("CrewAI orchestrator disabled - using individual agents")
            self._initialize_fallback_agents()
    
    def _initialize_crew(self):
        """Initialize CrewAI agents and crew"""
        try:
            # Set up Gemini LLM for CrewAI
            from langchain_google_genai import ChatGoogleGenerativeAI
            
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-exp",
                google_api_key=os.getenv("GOOGLE_API_KEY"),
                temperature=0.3,
                max_output_tokens=2048
            )
            
            # Define agents with Gemini LLM
            self.trade_agent = Agent(
                role='Senior Trade Analyst',
                goal='Analyze trading performance and execution quality',
                backstory="""You are an expert trading analyst with 15 years of experience 
                           in financial markets. You specialize in evaluating trade execution, 
                           risk management, and setup quality.""",
                verbose=True,
                allow_delegation=False,
                max_iter=3,
                llm=llm
            )
            
            self.psychology_agent = Agent(
                role='Trading Psychology Specialist',
                goal='Analyze trader psychology and emotional patterns',
                backstory="""You are a trading psychology expert who helps traders 
                           understand their emotional patterns and develop better 
                           mental frameworks for consistent performance.""",
                verbose=True,
                allow_delegation=False,
                max_iter=3,
                llm=llm
            )
            
            self.pattern_agent = Agent(
                role='Pattern Recognition Expert',
                goal='Identify recurring patterns in trading behavior and performance',
                backstory="""You are a quantitative analyst specializing in pattern 
                           recognition and behavioral analysis. You excel at finding 
                           hidden patterns in trading data.""",
                verbose=True,
                allow_delegation=False,
                max_iter=3,
                llm=llm
            )
            
            self.coach_agent = Agent(
                role='Personal Trading Coach',
                goal='Provide actionable coaching advice and improvement strategies',
                backstory="""You are a professional trading coach who helps traders 
                           improve their performance through structured feedback and 
                           personalized development plans.""",
                verbose=True,
                allow_delegation=False,
                max_iter=3,
                llm=llm
            )
            
            logger.info("CrewAI agents initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing CrewAI agents: {e}")
            self.enabled = False
            self._initialize_fallback_agents()
    
    def _initialize_fallback_agents(self):
        """Initialize fallback individual agents"""
        self.trade_analyzer = TradeAnalyzerAgent()
        self.psychology_analyzer = PsychologyAgent()
        self.pattern_finder = PatternFinderAgent()
        self.coach = CoachAgent()
        
        logger.info("Fallback agents initialized")
    
    def analyze_trade(self, trade_data: Dict[str, Any], image_path: Optional[str] = None) -> str:
        """Analyze a single trade using the crew"""
        if not self.enabled:
            return self._analyze_trade_fallback(trade_data, image_path)
        
        try:
            # Define tasks
            trade_analysis_task = Task(
                description=f"""
                Analyze the following trade for quality, execution, and risk management:
                
                Trade Data: {trade_data}
                Image Path: {image_path if image_path else 'None'}
                
                Provide a comprehensive analysis covering:
                1. Trade execution quality
                2. Risk management effectiveness
                3. Setup quality and timing
                4. Areas for improvement
                """,
                agent=self.trade_agent,
                expected_output="Detailed trade analysis with scores and recommendations"
            )
            
            psychology_task = Task(
                description=f"""
                Analyze the psychological aspects of this trade:
                
                Trade Data: {trade_data}
                
                Focus on:
                1. Emotional state indicators
                2. Decision-making patterns
                3. Psychological strengths and weaknesses
                4. Mental game recommendations
                """,
                agent=self.psychology_agent,
                expected_output="Psychology analysis with emotional scores and insights"
            )
            
            coaching_task = Task(
                description=f"""
                Based on the trade and psychology analysis, provide coaching advice:
                
                Trade Data: {trade_data}
                
                Provide:
                1. Specific improvement recommendations
                2. Action plan for next trades
                3. Skill development priorities
                4. Motivational guidance
                """,
                agent=self.coach_agent,
                expected_output="Actionable coaching advice and development plan",
                dependencies=[trade_analysis_task, psychology_task]
            )
            
            # Create and run crew
            crew = Crew(
                agents=[self.trade_agent, self.psychology_agent, self.coach_agent],
                tasks=[trade_analysis_task, psychology_task, coaching_task],
                process=Process.sequential,
                verbose=True
            )
            
            result = crew.kickoff()
            
            logger.info("CrewAI trade analysis completed")
            return str(result)
            
        except Exception as e:
            logger.error(f"Error in CrewAI trade analysis: {e}")
            return self._analyze_trade_fallback(trade_data, image_path)
    
    def analyze_portfolio(self, trades: List[Dict[str, Any]], psychology_notes: List[Dict[str, Any]]) -> str:
        """Analyze entire portfolio using the crew"""
        if not self.enabled:
            return self._analyze_portfolio_fallback(trades, psychology_notes)
        
        try:
            # Pattern analysis task
            pattern_task = Task(
                description=f"""
                Analyze the following trading portfolio for patterns:
                
                Trades: {trades[:10]}  # Limit to recent trades
                Psychology Notes: {psychology_notes[:10]}
                
                Find patterns in:
                1. Setup preferences and performance
                2. Timing patterns
                3. Risk management patterns
                4. Behavioral patterns
                """,
                agent=self.pattern_agent,
                expected_output="Comprehensive pattern analysis with insights"
            )
            
            # Portfolio coaching task
            portfolio_coaching_task = Task(
                description=f"""
                Provide portfolio-level coaching based on overall performance:
                
                Total Trades: {len(trades)}
                Recent Performance: {trades[-5:] if trades else []}
                
                Provide:
                1. Overall performance assessment
                2. Portfolio-level recommendations
                3. Strategic development plan
                4. Long-term improvement roadmap
                """,
                agent=self.coach_agent,
                expected_output="Strategic coaching plan for portfolio improvement",
                dependencies=[pattern_task]
            )
            
            # Create and run crew
            crew = Crew(
                agents=[self.pattern_agent, self.coach_agent],
                tasks=[pattern_task, portfolio_coaching_task],
                process=Process.sequential,
                verbose=True
            )
            
            result = crew.kickoff()
            
            logger.info("CrewAI portfolio analysis completed")
            return str(result)
            
        except Exception as e:
            logger.error(f"Error in CrewAI portfolio analysis: {e}")
            return self._analyze_portfolio_fallback(trades, psychology_notes)
    
    def _analyze_trade_fallback(self, trade_data: Dict[str, Any], image_path: Optional[str] = None) -> str:
        """Fallback trade analysis using individual agents"""
        try:
            # Analyze with individual agents
            trade_analysis = self.trade_analyzer.analyze_trade(trade_data)
            psychology_analysis = self.psychology_analyzer.analyze_trade_psychology(trade_data)
            coaching_advice = self.coach.generate_trade_coaching(trade_data, trade_analysis)
            
            # Combine results
            result = f"""
            🔍 TRADE ANALYSIS REPORT
            ========================
            
            📊 TRADE PERFORMANCE:
            {trade_analysis.get('summary', 'Analysis not available')}
            
            🧠 PSYCHOLOGY INSIGHTS:
            {psychology_analysis.get('summary', 'Analysis not available')}
            
            🎯 COACHING RECOMMENDATIONS:
            {coaching_advice.get('recommendations', 'Recommendations not available')}
            
            ⭐ KEY TAKEAWAYS:
            - Trade Quality: {trade_analysis.get('quality_score', 'N/A')}/10
            - Psychology Score: {psychology_analysis.get('psychology_score', 'N/A')}/10
            - Areas for Improvement: {', '.join(coaching_advice.get('improvement_areas', ['Enable AI for detailed analysis']))}
            """
            
            return result
            
        except Exception as e:
            logger.error(f"Error in fallback trade analysis: {e}")
            return "Trade analysis temporarily unavailable. Please check your configuration."
    
    def _analyze_portfolio_fallback(self, trades: List[Dict[str, Any]], psychology_notes: List[Dict[str, Any]]) -> str:
        """Fallback portfolio analysis using individual agents"""
        try:
            # Analyze with individual agents
            pattern_analysis = self.pattern_finder.find_patterns(trades)
            portfolio_coaching = self.coach.generate_portfolio_coaching(trades, psychology_notes)
            
            # Combine results
            result = f"""
            📈 PORTFOLIO ANALYSIS REPORT
            ============================
            
            🔍 PATTERN INSIGHTS:
            {pattern_analysis.get('summary', 'Pattern analysis not available')}
            
            🎯 PORTFOLIO COACHING:
            {portfolio_coaching.get('summary', 'Coaching not available')}
            
            📊 KEY METRICS:
            - Total Trades Analyzed: {len(trades)}
            - Patterns Identified: {len(pattern_analysis.get('patterns', []))}
            - Top Recommendation: {portfolio_coaching.get('top_recommendation', 'Enable AI for detailed analysis')}
            """
            
            return result
            
        except Exception as e:
            logger.error(f"Error in fallback portfolio analysis: {e}")
            return "Portfolio analysis temporarily unavailable. Please check your configuration."
    
    def get_crew_status(self) -> Dict[str, Any]:
        """Get status of the crew orchestrator"""
        return {
            "enabled": self.enabled,
            "crewai_available": CREWAI_AVAILABLE,
            "google_api_configured": bool(os.getenv("GOOGLE_API_KEY")),
            "agent_count": 4 if self.enabled else 4,  # Same agents, different implementation
            "mode": "CrewAI" if self.enabled else "Fallback"
        }

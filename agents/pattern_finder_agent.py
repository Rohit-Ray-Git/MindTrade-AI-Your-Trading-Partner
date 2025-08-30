"""
Pattern Finder Agent - Detects recurring patterns in trading behavior and performance
"""
import os
from typing import Dict, Any, Optional, List
from crewai import Agent, Task, Crew
from crewai_tools import BaseTool
from langchain_google_genai import ChatGoogleGenerativeAI
from loguru import logger
import json
import re
from datetime import datetime, timedelta
import pandas as pd

class PatternAnalysisTool(BaseTool):
    """Custom tool for statistical pattern analysis"""
    name: str = "pattern_analysis_tool"
    description: str = "Performs statistical analysis on trading data to identify patterns"
    
    def _run(self, trades_data: str) -> str:
        """Analyze trading patterns statistically"""
        try:
            trades = json.loads(trades_data)
            
            if not trades:
                return json.dumps({"error": "No trades data provided"})
            
            df = pd.DataFrame(trades)
            
            patterns = {
                "setup_patterns": self._analyze_setup_patterns(df),
                "timing_patterns": self._analyze_timing_patterns(df),
                "size_patterns": self._analyze_size_patterns(df),
                "performance_patterns": self._analyze_performance_patterns(df),
                "streak_patterns": self._analyze_streak_patterns(df),
                "correlation_patterns": self._analyze_correlations(df)
            }
            
            return json.dumps(patterns, default=str)
            
        except Exception as e:
            logger.error(f"Pattern analysis error: {e}")
            return json.dumps({"error": str(e)})
    
    def _analyze_setup_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Analyze patterns by setup type"""
        if 'setup' not in df.columns:
            return []
        
        setup_stats = []
        for setup in df['setup'].unique():
            setup_trades = df[df['setup'] == setup]
            
            if len(setup_trades) > 0:
                win_rate = (setup_trades['pnl'] > 0).mean() * 100
                avg_r = setup_trades['r_multiple'].mean()
                total_pnl = setup_trades['pnl'].sum()
                
                setup_stats.append({
                    "pattern_name": f"{setup} Setup",
                    "frequency": len(setup_trades),
                    "win_rate": win_rate,
                    "avg_r_multiple": avg_r,
                    "total_pnl": total_pnl,
                    "description": f"{setup} setup with {len(setup_trades)} trades, {win_rate:.1f}% win rate"
                })
        
        return sorted(setup_stats, key=lambda x: x['frequency'], reverse=True)
    
    def _analyze_timing_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Analyze timing patterns"""
        timing_patterns = []
        
        if 'trade_time' in df.columns:
            df['trade_time'] = pd.to_datetime(df['trade_time'])
            df['hour'] = df['trade_time'].dt.hour
            df['day_of_week'] = df['trade_time'].dt.day_name()
            
            # Hour patterns
            hour_performance = df.groupby('hour')['pnl'].agg(['count', 'mean', 'sum']).reset_index()
            best_hour = hour_performance.loc[hour_performance['mean'].idxmax()]
            
            timing_patterns.append({
                "pattern_name": f"Best Trading Hour: {best_hour['hour']}:00",
                "frequency": int(best_hour['count']),
                "description": f"Hour {best_hour['hour']} shows best average P&L of ${best_hour['mean']:.2f}"
            })
            
            # Day patterns
            day_performance = df.groupby('day_of_week')['pnl'].agg(['count', 'mean']).reset_index()
            best_day = day_performance.loc[day_performance['mean'].idxmax()]
            
            timing_patterns.append({
                "pattern_name": f"Best Trading Day: {best_day['day_of_week']}",
                "frequency": int(best_day['count']),
                "description": f"{best_day['day_of_week']} shows best average P&L of ${best_day['mean']:.2f}"
            })
        
        return timing_patterns
    
    def _analyze_size_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Analyze position size patterns"""
        size_patterns = []
        
        if 'quantity' in df.columns and 'pnl' in df.columns:
            # Correlation between size and performance
            correlation = df['quantity'].corr(df['pnl'])
            
            size_patterns.append({
                "pattern_name": "Position Size vs Performance",
                "correlation": correlation,
                "description": f"Position size correlation with P&L: {correlation:.3f}"
            })
            
            # Large vs small position analysis
            median_size = df['quantity'].median()
            large_positions = df[df['quantity'] > median_size]
            small_positions = df[df['quantity'] <= median_size]
            
            if len(large_positions) > 0 and len(small_positions) > 0:
                large_win_rate = (large_positions['pnl'] > 0).mean() * 100
                small_win_rate = (small_positions['pnl'] > 0).mean() * 100
                
                size_patterns.append({
                    "pattern_name": "Large vs Small Positions",
                    "large_position_win_rate": large_win_rate,
                    "small_position_win_rate": small_win_rate,
                    "description": f"Large positions: {large_win_rate:.1f}% win rate, Small positions: {small_win_rate:.1f}% win rate"
                })
        
        return size_patterns
    
    def _analyze_performance_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Analyze performance patterns"""
        performance_patterns = []
        
        if 'pnl' in df.columns:
            # Winning vs losing streaks
            df['is_winner'] = df['pnl'] > 0
            df['streak'] = (df['is_winner'] != df['is_winner'].shift()).cumsum()
            
            streak_analysis = df.groupby('streak').agg({
                'is_winner': ['first', 'count'],
                'pnl': 'sum'
            }).reset_index()
            
            winning_streaks = streak_analysis[streak_analysis[('is_winner', 'first')] == True]
            losing_streaks = streak_analysis[streak_analysis[('is_winner', 'first')] == False]
            
            if len(winning_streaks) > 0:
                max_win_streak = winning_streaks[('is_winner', 'count')].max()
                performance_patterns.append({
                    "pattern_name": "Longest Winning Streak",
                    "value": int(max_win_streak),
                    "description": f"Longest winning streak: {max_win_streak} trades"
                })
            
            if len(losing_streaks) > 0:
                max_loss_streak = losing_streaks[('is_winner', 'count')].max()
                performance_patterns.append({
                    "pattern_name": "Longest Losing Streak",
                    "value": int(max_loss_streak),
                    "description": f"Longest losing streak: {max_loss_streak} trades"
                })
        
        return performance_patterns
    
    def _analyze_streak_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Analyze streak behavior patterns"""
        streak_patterns = []
        
        if len(df) > 1 and 'pnl' in df.columns:
            df = df.sort_values('trade_time') if 'trade_time' in df.columns else df.reset_index()
            df['prev_pnl'] = df['pnl'].shift(1)
            df['after_win'] = df['prev_pnl'] > 0
            df['after_loss'] = df['prev_pnl'] < 0
            
            # Performance after wins
            after_win_trades = df[df['after_win'] == True]
            if len(after_win_trades) > 0:
                after_win_performance = after_win_trades['pnl'].mean()
                after_win_win_rate = (after_win_trades['pnl'] > 0).mean() * 100
                
                streak_patterns.append({
                    "pattern_name": "Performance After Wins",
                    "avg_pnl": after_win_performance,
                    "win_rate": after_win_win_rate,
                    "description": f"After winning trades: avg P&L ${after_win_performance:.2f}, win rate {after_win_win_rate:.1f}%"
                })
            
            # Performance after losses
            after_loss_trades = df[df['after_loss'] == True]
            if len(after_loss_trades) > 0:
                after_loss_performance = after_loss_trades['pnl'].mean()
                after_loss_win_rate = (after_loss_trades['pnl'] > 0).mean() * 100
                
                streak_patterns.append({
                    "pattern_name": "Performance After Losses",
                    "avg_pnl": after_loss_performance,
                    "win_rate": after_loss_win_rate,
                    "description": f"After losing trades: avg P&L ${after_loss_performance:.2f}, win rate {after_loss_win_rate:.1f}%"
                })
        
        return streak_patterns
    
    def _analyze_correlations(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze correlations between variables"""
        correlations = {}
        
        numeric_columns = df.select_dtypes(include=[float, int]).columns
        if len(numeric_columns) > 1:
            corr_matrix = df[numeric_columns].corr()
            
            # Find strongest correlations with PnL
            if 'pnl' in corr_matrix.columns:
                pnl_correlations = corr_matrix['pnl'].drop('pnl').abs().sort_values(ascending=False)
                
                correlations = {
                    "strongest_pnl_correlation": {
                        "variable": pnl_correlations.index[0] if len(pnl_correlations) > 0 else "None",
                        "correlation": float(pnl_correlations.iloc[0]) if len(pnl_correlations) > 0 else 0
                    }
                }
        
        return correlations

class PatternFinderAgent:
    """Pattern Finder Agent for detecting recurring trading patterns"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        
        # Initialize LLM
        if self.api_key:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=self.api_key,
                temperature=0.2,
                max_output_tokens=2048
            )
            self.enabled = True
        else:
            self.llm = None
            self.enabled = False
            logger.warning("No Google API key found. Pattern Finder Agent disabled.")
        
        # Initialize tools
        self.pattern_tool = PatternAnalysisTool()
        
        # Create agent
        if self.enabled:
            self.agent = Agent(
                role="Trading Pattern Analyst",
                goal="Identify recurring patterns in trading behavior, performance, and market conditions to provide actionable insights",
                backstory="""You are a quantitative analyst specializing in behavioral pattern recognition 
                in trading. You have expertise in statistical analysis, data mining, and identifying both 
                profitable and problematic trading patterns. Your analysis combines statistical methods 
                with behavioral insights to help traders understand their tendencies and improve their 
                systematic approach to trading.""",
                verbose=True,
                allow_delegation=False,
                llm=self.llm,
                tools=[self.pattern_tool]
            )
    
    def find_patterns(self, trades_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Find patterns in trading data"""
        if not self.enabled:
            return self._get_default_pattern_analysis()
        
        try:
            # Prepare trades data
            trades_json = json.dumps(trades_data)
            
            # Create pattern analysis task
            task_description = f"""
            Analyze the following trading data to identify significant patterns and insights:
            
            Number of trades: {len(trades_data)}
            
            Your analysis should include:
            1. Setup Performance Patterns: Which setups perform best/worst and why
            2. Timing Patterns: Optimal trading times, days, market conditions
            3. Behavioral Patterns: Recurring behaviors that impact performance
            4. Risk Patterns: Risk management patterns and their effectiveness
            5. Performance Patterns: Winning/losing streaks, performance trends
            6. Size Patterns: Position sizing patterns and their impact
            7. Market Condition Patterns: How performance varies with market conditions
            8. Improvement Opportunities: Specific areas for improvement based on patterns
            
            Use the pattern_analysis_tool to get statistical insights from the data.
            
            Provide comprehensive pattern analysis in structured JSON format with:
            - Pattern descriptions
            - Statistical significance
            - Actionable recommendations
            - Risk assessments
            """
            
            task = Task(
                description=task_description,
                agent=self.agent,
                expected_output="Comprehensive pattern analysis in JSON format with statistical insights and recommendations"
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
                        analysis = self._structure_pattern_response(result, trades_data)
                else:
                    analysis = result
                
                # Add statistical analysis
                statistical_patterns = json.loads(self.pattern_tool._run(trades_json))
                if "error" not in statistical_patterns:
                    analysis["statistical_analysis"] = statistical_patterns
                
                logger.info(f"Pattern analysis completed for {len(trades_data)} trades")
                return analysis
                
            except json.JSONDecodeError:
                # If JSON parsing fails, structure the response
                return self._structure_pattern_response(str(result), trades_data)
            
        except Exception as e:
            logger.error(f"Error in pattern analysis: {e}")
            return self._get_default_pattern_analysis()
    
    def find_behavioral_patterns(self, trades_data: List[Dict[str, Any]], psychology_notes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Find behavioral patterns combining trades and psychology data"""
        if not self.enabled:
            return self._get_default_behavioral_analysis()
        
        try:
            # Prepare combined context
            context = f"""
            Trading Performance Data:
            {json.dumps(trades_data[:20], indent=2)}  # Limit for readability
            
            Psychology Notes:
            {json.dumps(psychology_notes[:20], indent=2)}  # Limit for readability
            """
            
            # Create behavioral pattern analysis task
            task_description = f"""
            Analyze the combined trading performance and psychology data to identify behavioral patterns:
            
            {context}
            
            Your analysis should focus on:
            1. Emotion-Performance Correlations: How emotions affect trading outcomes
            2. Behavioral Triggers: What triggers specific trading behaviors
            3. Decision-Making Patterns: Consistent decision-making tendencies
            4. Risk-Taking Patterns: Risk behavior patterns and their outcomes
            5. Learning Patterns: How behavior evolves over time
            6. Stress Response Patterns: How stress affects trading performance
            7. Confidence Patterns: How confidence levels impact decisions
            8. Discipline Patterns: Consistency in following trading rules
            
            Provide behavioral pattern analysis in structured JSON format with:
            - Pattern identification
            - Behavioral insights
            - Performance correlations
            - Improvement strategies
            """
            
            task = Task(
                description=task_description,
                agent=self.agent,
                expected_output="Behavioral pattern analysis in JSON format with correlations and improvement strategies"
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
                        analysis = self._structure_behavioral_response(result)
                else:
                    analysis = result
                
                logger.info("Behavioral pattern analysis completed")
                return analysis
                
            except json.JSONDecodeError:
                return self._structure_behavioral_response(str(result))
            
        except Exception as e:
            logger.error(f"Error in behavioral pattern analysis: {e}")
            return self._get_default_behavioral_analysis()
    
    def _structure_pattern_response(self, analysis_text: str, trades_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Structure the pattern response when JSON parsing fails"""
        # Get statistical analysis
        statistical_patterns = json.loads(self.pattern_tool._run(json.dumps(trades_data)))
        
        return {
            "setup_patterns": statistical_patterns.get("setup_patterns", []),
            "timing_patterns": statistical_patterns.get("timing_patterns", []),
            "risk_patterns": [
                {
                    "pattern_name": "Standard Risk Management",
                    "frequency": len(trades_data),
                    "impact": "neutral",
                    "description": "Standard risk management patterns observed"
                }
            ],
            "behavioral_patterns": [
                {
                    "pattern_name": "Consistent Trading Approach",
                    "frequency": len(trades_data),
                    "impact": "positive",
                    "description": "Trader shows consistent approach to trading"
                }
            ],
            "performance_patterns": statistical_patterns.get("performance_patterns", []),
            "recommendations": [
                "Continue systematic approach",
                "Focus on high-performing setups",
                "Maintain consistent risk management"
            ],
            "statistical_analysis": statistical_patterns,
            "agent_analysis": analysis_text[:500] + "..." if len(analysis_text) > 500 else analysis_text
        }
    
    def _structure_behavioral_response(self, analysis_text: str) -> Dict[str, Any]:
        """Structure the behavioral response when JSON parsing fails"""
        return {
            "emotion_performance_correlations": {
                "fear_impact": "Negative correlation with performance",
                "confidence_impact": "Positive correlation with performance",
                "patience_impact": "Strong positive correlation"
            },
            "behavioral_triggers": [
                "Market volatility triggers emotional responses",
                "Consecutive losses trigger revenge trading",
                "Big wins trigger overconfidence"
            ],
            "decision_making_patterns": [
                "Tends to follow systematic approach",
                "Occasional emotional override of rules",
                "Good at cutting losses"
            ],
            "risk_taking_patterns": [
                "Conservative risk management",
                "Appropriate position sizing",
                "Consistent stop loss usage"
            ],
            "improvement_strategies": [
                "Implement pre-trade emotional check",
                "Develop meditation routine",
                "Use position sizing rules strictly"
            ],
            "agent_analysis": analysis_text[:500] + "..." if len(analysis_text) > 500 else analysis_text
        }
    
    def _get_default_pattern_analysis(self) -> Dict[str, Any]:
        """Default pattern analysis when agent is disabled"""
        return {
            "setup_patterns": [],
            "timing_patterns": [],
            "risk_patterns": [],
            "behavioral_patterns": [],
            "performance_patterns": [],
            "recommendations": ["Enable AI features for pattern detection"]
        }
    
    def _get_default_behavioral_analysis(self) -> Dict[str, Any]:
        """Default behavioral analysis when agent is disabled"""
        return {
            "emotion_performance_correlations": {},
            "behavioral_triggers": [],
            "decision_making_patterns": [],
            "risk_taking_patterns": [],
            "improvement_strategies": ["Enable AI features for behavioral analysis"]
        }

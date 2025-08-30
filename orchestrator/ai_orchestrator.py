"""
AI Orchestrator - Coordinates all AI agents for comprehensive trading analysis
"""
import os
from typing import Dict, Any, Optional, List
from crewai import Agent, Task, Crew
from langchain_google_genai import ChatGoogleGenerativeAI
from loguru import logger
import json
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Import our agents
from agents.trade_analyzer_agent import TradeAnalyzerAgent
from agents.psychology_agent import PsychologyAgent
from agents.pattern_finder_agent import PatternFinderAgent
from agents.coach_agent import CoachAgent

class AIOrchestrator:
    """Main orchestrator for coordinating all AI agents"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        
        # Initialize all agents
        self.trade_analyzer = TradeAnalyzerAgent(api_key=self.api_key)
        self.psychology_agent = PsychologyAgent(api_key=self.api_key)
        self.pattern_finder = PatternFinderAgent(api_key=self.api_key)
        self.coach = CoachAgent(api_key=self.api_key)
        
        # Check if orchestrator is enabled
        self.enabled = all([
            self.trade_analyzer.enabled,
            self.psychology_agent.enabled,
            self.pattern_finder.enabled,
            self.coach.enabled
        ])
        
        if self.enabled:
            logger.info("AI Orchestrator initialized with all agents enabled")
        else:
            logger.warning("AI Orchestrator partially enabled - some agents disabled")
    
    def process_new_trade(self, trade_data: Dict[str, Any], image_path: Optional[str] = None, psychology_note: Optional[str] = None) -> Dict[str, Any]:
        """Process a new trade through all relevant agents"""
        logger.info(f"Processing new trade: {trade_data.get('symbol')} - {trade_data.get('direction')}")
        
        results = {
            "trade_id": trade_data.get('id'),
            "symbol": trade_data.get('symbol'),
            "timestamp": datetime.now().isoformat(),
            "analysis_complete": False
        }
        
        try:
            # 1. Trade Analysis
            logger.info("Running trade analysis...")
            trade_analysis = self.trade_analyzer.analyze_trade(trade_data, image_path)
            results["trade_analysis"] = trade_analysis
            
            # 2. Psychology Analysis (if note provided)
            if psychology_note:
                logger.info("Running psychology analysis...")
                psychology_analysis = self.psychology_agent.analyze_psychology_note(psychology_note, trade_data)
                results["psychology_analysis"] = psychology_analysis
            
            # 3. Quick coaching insights for this trade
            logger.info("Generating trade-specific coaching...")
            coaching_insights = self._generate_trade_coaching(trade_analysis, psychology_analysis if psychology_note else None)
            results["coaching_insights"] = coaching_insights
            
            results["analysis_complete"] = True
            logger.info(f"Trade processing complete for {trade_data.get('symbol')}")
            
        except Exception as e:
            logger.error(f"Error processing trade: {e}")
            results["error"] = str(e)
        
        return results
    
    def run_comprehensive_analysis(self, 
                                  trades_data: List[Dict[str, Any]], 
                                  psychology_notes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run comprehensive analysis across all historical data"""
        logger.info(f"Running comprehensive analysis on {len(trades_data)} trades and {len(psychology_notes)} psychology notes")
        
        results = {
            "analysis_timestamp": datetime.now().isoformat(),
            "data_summary": {
                "total_trades": len(trades_data),
                "psychology_notes": len(psychology_notes)
            },
            "analysis_complete": False
        }
        
        try:
            # Run all analyses in parallel for better performance
            with ThreadPoolExecutor(max_workers=4) as executor:
                # Submit all tasks
                future_pattern_analysis = executor.submit(self.pattern_finder.find_patterns, trades_data)
                future_behavioral_patterns = executor.submit(
                    self.pattern_finder.find_behavioral_patterns, 
                    trades_data, 
                    psychology_notes
                )
                future_psychology_patterns = executor.submit(
                    self.psychology_agent.analyze_multiple_notes, 
                    psychology_notes
                )
                
                # Collect results
                logger.info("Analyzing trading patterns...")
                pattern_analysis = future_pattern_analysis.result()
                results["pattern_analysis"] = pattern_analysis
                
                logger.info("Analyzing behavioral patterns...")
                behavioral_patterns = future_behavioral_patterns.result()
                results["behavioral_patterns"] = behavioral_patterns
                
                logger.info("Analyzing psychology patterns...")
                psychology_patterns = future_psychology_patterns.result()
                results["psychology_patterns"] = psychology_patterns
            
            # Generate comprehensive coaching plan
            logger.info("Generating comprehensive coaching plan...")
            performance_data = self._extract_performance_data(trades_data)
            coaching_plan = self.coach.generate_coaching_plan(
                performance_data, 
                psychology_patterns, 
                pattern_analysis
            )
            results["coaching_plan"] = coaching_plan
            
            # Generate overall insights
            results["overall_insights"] = self._generate_overall_insights(
                pattern_analysis, behavioral_patterns, psychology_patterns, coaching_plan
            )
            
            results["analysis_complete"] = True
            logger.info("Comprehensive analysis complete")
            
        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {e}")
            results["error"] = str(e)
        
        return results
    
    def generate_daily_insights(self, recent_trades: List[Dict[str, Any]], current_mood: str = "neutral") -> Dict[str, Any]:
        """Generate daily insights and coaching"""
        logger.info("Generating daily insights...")
        
        try:
            # Get daily coaching
            daily_coaching = self.coach.generate_daily_coaching(recent_trades, current_mood)
            
            # Quick pattern check on recent trades
            recent_patterns = None
            if len(recent_trades) >= 5:
                recent_patterns = self.pattern_finder.find_patterns(recent_trades[-10:])
            
            insights = {
                "date": datetime.now().date().isoformat(),
                "daily_coaching": daily_coaching,
                "recent_performance": self._summarize_recent_performance(recent_trades),
                "daily_focus_areas": self._generate_daily_focus(recent_trades, daily_coaching),
                "motivation_level": self._assess_motivation_level(recent_trades, current_mood)
            }
            
            if recent_patterns:
                insights["recent_patterns"] = recent_patterns
            
            logger.info("Daily insights generated")
            return insights
            
        except Exception as e:
            logger.error(f"Error generating daily insights: {e}")
            return {"error": str(e)}
    
    def generate_weekly_review(self, week_trades: List[Dict[str, Any]], week_psychology: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate weekly review and analysis"""
        logger.info(f"Generating weekly review for {len(week_trades)} trades")
        
        try:
            # Get weekly coaching review
            weekly_coaching = self.coach.generate_weekly_review(week_trades, week_psychology)
            
            # Analyze week's patterns
            week_patterns = None
            if len(week_trades) >= 3:
                week_patterns = self.pattern_finder.find_patterns(week_trades)
            
            # Psychology analysis for the week
            week_psychology_analysis = None
            if week_psychology:
                week_psychology_analysis = self.psychology_agent.analyze_multiple_notes(week_psychology)
            
            review = {
                "week_ending": datetime.now().date().isoformat(),
                "weekly_coaching": weekly_coaching,
                "week_performance": self._calculate_week_performance(week_trades),
                "week_patterns": week_patterns,
                "psychology_insights": week_psychology_analysis,
                "improvements_made": self._identify_weekly_improvements(week_trades, week_psychology),
                "next_week_goals": self._set_next_week_goals(weekly_coaching, week_patterns)
            }
            
            logger.info("Weekly review generated")
            return review
            
        except Exception as e:
            logger.error(f"Error generating weekly review: {e}")
            return {"error": str(e)}
    
    def analyze_market_screenshot(self, image_path: str, context: str = "") -> Dict[str, Any]:
        """Analyze market screenshot for trading opportunities"""
        logger.info("Analyzing market screenshot...")
        
        try:
            # Use the enhanced Gemini AI for market analysis
            from utils.ai_integration import GeminiAI
            gemini_ai = GeminiAI(self.api_key)
            
            if gemini_ai.enabled:
                analysis = gemini_ai.analyze_market_screenshot(image_path, context)
                
                # Add coaching perspective on the setups
                coaching_perspective = self._add_coaching_perspective(analysis)
                analysis["coaching_perspective"] = coaching_perspective
                
                logger.info("Market screenshot analysis complete")
                return analysis
            else:
                return {"error": "AI not enabled for market analysis"}
                
        except Exception as e:
            logger.error(f"Error analyzing market screenshot: {e}")
            return {"error": str(e)}
    
    def _generate_trade_coaching(self, trade_analysis: Dict[str, Any], psychology_analysis: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate coaching insights for a specific trade"""
        insights = {
            "immediate_feedback": [],
            "learning_points": [],
            "improvement_suggestions": []
        }
        
        # Trade quality feedback
        trade_score = trade_analysis.get("trade_quality_score", 0)
        if trade_score > 0.8:
            insights["immediate_feedback"].append("Excellent trade execution!")
        elif trade_score > 0.6:
            insights["immediate_feedback"].append("Good trade with room for improvement")
        else:
            insights["immediate_feedback"].append("This trade has significant learning opportunities")
        
        # Psychology feedback
        if psychology_analysis:
            sentiment = psychology_analysis.get("sentiment_score", 0)
            if sentiment < -0.3:
                insights["improvement_suggestions"].append("Work on maintaining positive mindset during trades")
            
            fear_score = psychology_analysis.get("fear_score", 0)
            if fear_score > 0.7:
                insights["improvement_suggestions"].append("Practice fear management techniques")
        
        # Learning points from trade analysis
        if "key_learnings" in trade_analysis:
            insights["learning_points"] = trade_analysis["key_learnings"]
        
        return insights
    
    def _extract_performance_data(self, trades_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract performance metrics from trades data"""
        if not trades_data:
            return {"total_trades": 0, "win_rate": 0, "avg_r_multiple": 0, "total_pnl": 0}
        
        total_trades = len(trades_data)
        winning_trades = len([t for t in trades_data if t.get('pnl', 0) > 0])
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        total_pnl = sum(t.get('pnl', 0) for t in trades_data)
        avg_r_multiple = sum(t.get('r_multiple', 0) for t in trades_data) / total_trades if total_trades > 0 else 0
        
        # Calculate max drawdown (simplified)
        cumulative_pnl = 0
        peak = 0
        max_drawdown = 0
        
        for trade in sorted(trades_data, key=lambda x: x.get('trade_time', datetime.now())):
            cumulative_pnl += trade.get('pnl', 0)
            if cumulative_pnl > peak:
                peak = cumulative_pnl
            drawdown = peak - cumulative_pnl
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        return {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "win_rate": win_rate,
            "total_pnl": total_pnl,
            "avg_r_multiple": avg_r_multiple,
            "max_drawdown": max_drawdown
        }
    
    def _generate_overall_insights(self, pattern_analysis: Dict[str, Any], behavioral_patterns: Dict[str, Any], 
                                 psychology_patterns: Dict[str, Any], coaching_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Generate high-level insights from all analyses"""
        insights = {
            "key_findings": [],
            "critical_areas": [],
            "strengths": [],
            "action_priorities": []
        }
        
        # Extract key findings from patterns
        if pattern_analysis.get("setup_patterns"):
            best_setup = max(pattern_analysis["setup_patterns"], key=lambda x: x.get("win_rate", 0))
            insights["key_findings"].append(f"Best performing setup: {best_setup.get('pattern_name', 'Unknown')}")
        
        # Extract psychology insights
        if psychology_patterns.get("emotional_patterns"):
            insights["key_findings"].extend(psychology_patterns["emotional_patterns"][:2])
        
        # Extract coaching priorities
        if coaching_plan.get("action_plan", {}).get("immediate_actions"):
            insights["action_priorities"] = coaching_plan["action_plan"]["immediate_actions"]
        
        return insights
    
    def _summarize_recent_performance(self, recent_trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize recent trading performance"""
        if not recent_trades:
            return {"message": "No recent trades to analyze"}
        
        recent_pnl = sum(t.get('pnl', 0) for t in recent_trades[-5:])
        recent_wins = len([t for t in recent_trades[-5:] if t.get('pnl', 0) > 0])
        
        return {
            "last_5_trades_pnl": recent_pnl,
            "last_5_trades_wins": recent_wins,
            "recent_trend": "positive" if recent_pnl > 0 else "needs_attention"
        }
    
    def _generate_daily_focus(self, recent_trades: List[Dict[str, Any]], daily_coaching: Dict[str, Any]) -> List[str]:
        """Generate specific focus areas for today"""
        focus_areas = []
        
        # From coaching
        if daily_coaching.get("daily_focus"):
            focus_areas.extend(daily_coaching["daily_focus"])
        
        # From recent performance
        if recent_trades:
            recent_pnl = sum(t.get('pnl', 0) for t in recent_trades[-3:])
            if recent_pnl < 0:
                focus_areas.append("Focus on capital preservation today")
        
        return focus_areas[:3]  # Limit to 3 focus areas
    
    def _assess_motivation_level(self, recent_trades: List[Dict[str, Any]], current_mood: str) -> str:
        """Assess current motivation level"""
        if current_mood in ["excited", "confident"]:
            return "high"
        elif current_mood in ["frustrated", "angry", "sad"]:
            return "low"
        
        # Check recent performance
        if recent_trades:
            recent_pnl = sum(t.get('pnl', 0) for t in recent_trades[-5:])
            if recent_pnl > 0:
                return "high"
            elif recent_pnl < -100:  # Adjust threshold as needed
                return "low"
        
        return "moderate"
    
    def _calculate_week_performance(self, week_trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate weekly performance metrics"""
        if not week_trades:
            return {"total_trades": 0, "weekly_pnl": 0, "win_rate": 0}
        
        total_trades = len(week_trades)
        wins = len([t for t in week_trades if t.get('pnl', 0) > 0])
        weekly_pnl = sum(t.get('pnl', 0) for t in week_trades)
        win_rate = (wins / total_trades) * 100 if total_trades > 0 else 0
        
        return {
            "total_trades": total_trades,
            "winning_trades": wins,
            "weekly_pnl": weekly_pnl,
            "win_rate": win_rate,
            "daily_average": weekly_pnl / 7  # Assuming 7 trading days
        }
    
    def _identify_weekly_improvements(self, week_trades: List[Dict[str, Any]], week_psychology: List[Dict[str, Any]]) -> List[str]:
        """Identify improvements made during the week"""
        improvements = []
        
        if week_trades:
            # Check for consistency
            if len(set(t.get('setup', 'unknown') for t in week_trades)) <= 3:
                improvements.append("Maintained setup focus and consistency")
            
            # Check for risk management
            if all(t.get('r_multiple', 0) >= -1 for t in week_trades):
                improvements.append("Maintained proper risk management")
        
        if week_psychology:
            # Check for emotional improvements
            recent_sentiment = [n.get('sentiment_score', 0) for n in week_psychology[-3:]]
            if recent_sentiment and sum(recent_sentiment) / len(recent_sentiment) > 0:
                improvements.append("Maintained positive trading mindset")
        
        return improvements if improvements else ["Continue working on trading fundamentals"]
    
    def _set_next_week_goals(self, weekly_coaching: Dict[str, Any], week_patterns: Optional[Dict[str, Any]]) -> List[str]:
        """Set goals for next week"""
        goals = []
        
        # From coaching insights
        if weekly_coaching.get("next_week_focus"):
            goals.extend(weekly_coaching["next_week_focus"])
        
        # From pattern analysis
        if week_patterns and week_patterns.get("recommendations"):
            goals.extend(week_patterns["recommendations"][:2])
        
        # Default goals if none found
        if not goals:
            goals = [
                "Maintain trading discipline",
                "Focus on high-probability setups",
                "Complete daily trading reviews"
            ]
        
        return goals[:3]  # Limit to 3 goals
    
    def _add_coaching_perspective(self, market_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Add coaching perspective to market analysis"""
        perspective = {
            "trading_advice": [],
            "risk_considerations": [],
            "setup_quality_assessment": "fair"
        }
        
        # Assess setup quality
        if market_analysis.get("potential_setups"):
            setups = market_analysis["potential_setups"]
            high_confidence_setups = [s for s in setups if s.get("confidence", 0) > 0.7]
            
            if high_confidence_setups:
                perspective["setup_quality_assessment"] = "good"
                perspective["trading_advice"].append("Multiple high-confidence setups identified")
            
            # Risk considerations
            risk_level = market_analysis.get("risk_assessment", {}).get("risk_level", "medium")
            if risk_level == "high":
                perspective["risk_considerations"].append("High risk environment - reduce position sizes")
            
        return perspective
    
    def get_orchestrator_status(self) -> Dict[str, Any]:
        """Get status of all agents in the orchestrator"""
        return {
            "orchestrator_enabled": self.enabled,
            "agents_status": {
                "trade_analyzer": self.trade_analyzer.enabled,
                "psychology_agent": self.psychology_agent.enabled,
                "pattern_finder": self.pattern_finder.enabled,
                "coach": self.coach.enabled
            },
            "api_key_configured": bool(self.api_key),
            "ready_for_analysis": self.enabled
        }

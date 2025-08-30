"""
Coach Agent - Provides personalized coaching and mentorship for trading improvement
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

class CoachingFrameworkTool(BaseTool):
    """Custom tool for coaching framework and methodology"""
    name: str = "coaching_framework_tool"
    description: str = "Applies structured coaching frameworks to trading improvement"
    
    def _run(self, performance_data: str, goals: str = "improve_trading") -> str:
        """Apply coaching framework to performance data"""
        try:
            data = json.loads(performance_data)
            
            # GROW Model Framework (Goal, Reality, Options, Way Forward)
            coaching_framework = {
                "grow_model": {
                    "goal": self._identify_goals(data),
                    "reality": self._assess_reality(data),
                    "options": self._generate_options(data),
                    "way_forward": self._create_action_plan(data)
                },
                "strengths_analysis": self._analyze_strengths(data),
                "improvement_areas": self._identify_improvements(data),
                "action_priorities": self._prioritize_actions(data),
                "success_metrics": self._define_metrics(data)
            }
            
            return json.dumps(coaching_framework, default=str)
            
        except Exception as e:
            logger.error(f"Coaching framework error: {e}")
            return json.dumps({"error": str(e)})
    
    def _identify_goals(self, data: Dict[str, Any]) -> List[str]:
        """Identify coaching goals based on performance"""
        goals = []
        
        # Performance-based goals
        win_rate = data.get('win_rate', 0)
        if win_rate < 50:
            goals.append("Improve win rate to above 50%")
        
        avg_r = data.get('avg_r_multiple', 0)
        if avg_r < 1.5:
            goals.append("Increase average R-multiple to 1.5+")
        
        total_pnl = data.get('total_pnl', 0)
        if total_pnl < 0:
            goals.append("Achieve consistent profitability")
        
        # Psychology-based goals
        if data.get('emotional_volatility', 0) > 0.5:
            goals.append("Develop emotional discipline")
        
        return goals if goals else ["Maintain current performance and continue growth"]
    
    def _assess_reality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess current trading reality"""
        return {
            "current_performance": {
                "win_rate": data.get('win_rate', 0),
                "avg_r_multiple": data.get('avg_r_multiple', 0),
                "total_pnl": data.get('total_pnl', 0),
                "total_trades": data.get('total_trades', 0)
            },
            "strengths": data.get('strengths', []),
            "challenges": data.get('challenges', []),
            "patterns": data.get('patterns', [])
        }
    
    def _generate_options(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate improvement options"""
        options = []
        
        win_rate = data.get('win_rate', 0)
        if win_rate < 50:
            options.append({
                "category": "Setup Selection",
                "option": "Focus on highest-performing setups only",
                "impact": "High",
                "effort": "Medium"
            })
        
        avg_r = data.get('avg_r_multiple', 0)
        if avg_r < 1.5:
            options.append({
                "category": "Risk Management",
                "option": "Improve target selection and trade management",
                "impact": "High", 
                "effort": "Medium"
            })
        
        if data.get('emotional_issues', False):
            options.append({
                "category": "Psychology",
                "option": "Implement meditation and emotional regulation practices",
                "impact": "High",
                "effort": "High"
            })
        
        return options
    
    def _create_action_plan(self, data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Create actionable steps"""
        actions = []
        
        # Immediate actions (this week)
        actions.append({
            "timeframe": "This Week",
            "action": "Review and document your top 3 performing setups",
            "outcome": "Clear focus on profitable patterns"
        })
        
        # Short-term actions (this month)
        actions.append({
            "timeframe": "This Month", 
            "action": "Implement strict rules for setup selection",
            "outcome": "Improved trade selection discipline"
        })
        
        # Long-term actions (next quarter)
        actions.append({
            "timeframe": "Next Quarter",
            "action": "Develop advanced risk management system",
            "outcome": "Consistent profitability"
        })
        
        return actions
    
    def _analyze_strengths(self, data: Dict[str, Any]) -> List[str]:
        """Analyze trading strengths"""
        strengths = []
        
        if data.get('win_rate', 0) > 60:
            strengths.append("High win rate indicates good setup selection")
        
        if data.get('avg_r_multiple', 0) > 2:
            strengths.append("Excellent risk-reward management")
        
        if data.get('consistency_score', 0) > 0.7:
            strengths.append("Consistent trading approach")
        
        return strengths if strengths else ["Systematic approach to trading"]
    
    def _identify_improvements(self, data: Dict[str, Any]) -> List[str]:
        """Identify improvement areas"""
        improvements = []
        
        if data.get('win_rate', 0) < 45:
            improvements.append("Setup selection needs improvement")
        
        if data.get('avg_r_multiple', 0) < 1:
            improvements.append("Risk-reward ratios need optimization")
        
        if data.get('emotional_volatility', 0) > 0.6:
            improvements.append("Emotional discipline requires development")
        
        return improvements if improvements else ["Fine-tune existing strategies"]
    
    def _prioritize_actions(self, data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Prioritize improvement actions"""
        priorities = []
        
        # High priority
        if data.get('total_pnl', 0) < 0:
            priorities.append({
                "priority": "High",
                "action": "Focus on capital preservation",
                "reason": "Currently losing money"
            })
        
        # Medium priority  
        if data.get('win_rate', 0) < 50:
            priorities.append({
                "priority": "Medium",
                "action": "Improve setup selection",
                "reason": "Low win rate affecting confidence"
            })
        
        # Low priority
        priorities.append({
            "priority": "Low", 
            "action": "Optimize profit targets",
            "reason": "Fine-tuning for better performance"
        })
        
        return priorities
    
    def _define_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Define success metrics"""
        return {
            "performance_metrics": {
                "target_win_rate": max(55, data.get('win_rate', 0) + 5),
                "target_r_multiple": max(1.5, data.get('avg_r_multiple', 0) + 0.2),
                "target_monthly_return": "5-10%"
            },
            "behavioral_metrics": {
                "trade_plan_adherence": "95%+",
                "emotional_control_score": "8/10+",
                "setup_selectivity": "Only A+ setups"
            },
            "review_frequency": {
                "daily_review": "Required",
                "weekly_analysis": "Required", 
                "monthly_assessment": "Required"
            }
        }

class CoachAgent:
    """Coach Agent for personalized trading mentorship and improvement"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        
        # Initialize LLM
        if self.api_key:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=self.api_key,
                temperature=0.4,
                max_output_tokens=3000
            )
            self.enabled = True
        else:
            self.llm = None
            self.enabled = False
            logger.warning("No Google API key found. Coach Agent disabled.")
        
        # Initialize tools
        self.coaching_tool = CoachingFrameworkTool()
        
        # Create agent
        if self.enabled:
            self.agent = Agent(
                role="Senior Trading Coach & Mentor",
                goal="Provide personalized coaching, mentorship, and actionable improvement strategies for traders",
                backstory="""You are an experienced trading coach with 20+ years in financial markets 
                and 10+ years coaching traders. You combine technical expertise with psychology, using 
                proven coaching methodologies like the GROW model. Your approach is supportive yet direct, 
                focusing on sustainable improvement and long-term success. You understand that trading 
                success requires both technical skills and psychological mastery.""",
                verbose=True,
                allow_delegation=False,
                llm=self.llm,
                tools=[self.coaching_tool]
            )
    
    def generate_coaching_plan(self, 
                             performance_data: Dict[str, Any], 
                             psychology_data: Dict[str, Any],
                             pattern_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive coaching plan"""
        if not self.enabled:
            return self._get_default_coaching_plan()
        
        try:
            # Prepare comprehensive context
            context = f"""
            Trading Performance Data:
            - Total Trades: {performance_data.get('total_trades', 0)}
            - Win Rate: {performance_data.get('win_rate', 0):.1f}%
            - Average R-Multiple: {performance_data.get('avg_r_multiple', 0):.2f}
            - Total P&L: ${performance_data.get('total_pnl', 0):.2f}
            - Max Drawdown: ${performance_data.get('max_drawdown', 0):.2f}
            
            Psychology Analysis:
            {json.dumps(psychology_data, indent=2)}
            
            Pattern Analysis:
            {json.dumps(pattern_data, indent=2)}
            """
            
            # Create coaching plan task
            task_description = f"""
            As a senior trading coach, create a comprehensive coaching plan based on this trader's data:
            
            {context}
            
            Your coaching plan should include:
            
            1. OVERALL ASSESSMENT:
               - Current trading level (Beginner/Intermediate/Advanced)
               - Key strengths to build upon
               - Critical weaknesses to address
               - Overall trajectory and potential
            
            2. PERFORMANCE COACHING:
               - Technical skill gaps and improvements
               - Setup optimization strategies
               - Risk management enhancements
               - Execution improvements
            
            3. PSYCHOLOGY COACHING:
               - Emotional patterns and triggers
               - Mental discipline strategies
               - Confidence building approaches
               - Stress management techniques
            
            4. STRUCTURED ACTION PLAN:
               - Immediate actions (this week)
               - Short-term goals (this month)
               - Long-term objectives (next quarter)
               - Success metrics and milestones
            
            5. PERSONALIZED RECOMMENDATIONS:
               - Daily routines and habits
               - Study and practice suggestions
               - Tools and resources
               - Review and feedback schedule
            
            6. MOTIVATIONAL GUIDANCE:
               - Encouragement based on progress
               - Realistic expectations
               - Milestone celebrations
               - Long-term vision
            
            Use the coaching_framework_tool to apply structured coaching methodologies.
            
            Provide a comprehensive, supportive, and actionable coaching plan in JSON format.
            """
            
            task = Task(
                description=task_description,
                agent=self.agent,
                expected_output="Comprehensive coaching plan in JSON format with assessment, strategies, and action plans"
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
                        coaching_plan = json.loads(json_match.group())
                    else:
                        # Fallback to structured response
                        coaching_plan = self._structure_coaching_response(result, performance_data)
                else:
                    coaching_plan = result
                
                # Add coaching framework analysis
                framework_data = {
                    "win_rate": performance_data.get('win_rate', 0),
                    "avg_r_multiple": performance_data.get('avg_r_multiple', 0),
                    "total_pnl": performance_data.get('total_pnl', 0),
                    "strengths": psychology_data.get('strengths', []),
                    "challenges": psychology_data.get('challenges', [])
                }
                framework_analysis = json.loads(self.coaching_tool._run(json.dumps(framework_data)))
                if "error" not in framework_analysis:
                    coaching_plan["coaching_framework"] = framework_analysis
                
                logger.info("Comprehensive coaching plan generated")
                return coaching_plan
                
            except json.JSONDecodeError:
                # If JSON parsing fails, structure the response
                return self._structure_coaching_response(str(result), performance_data)
            
        except Exception as e:
            logger.error(f"Error generating coaching plan: {e}")
            return self._get_default_coaching_plan()
    
    def generate_daily_coaching(self, recent_trades: List[Dict[str, Any]], current_mood: str = "neutral") -> Dict[str, Any]:
        """Generate daily coaching message and tips"""
        if not self.enabled:
            return self._get_default_daily_coaching()
        
        try:
            # Prepare recent performance context
            context = f"""
            Recent Trading Activity:
            - Number of recent trades: {len(recent_trades)}
            - Current mood/state: {current_mood}
            
            Recent Trades Summary:
            {json.dumps(recent_trades[-5:], indent=2) if recent_trades else "No recent trades"}
            """
            
            # Create daily coaching task
            task_description = f"""
            Provide daily coaching guidance for this trader:
            
            {context}
            
            Your daily coaching should include:
            1. Positive reinforcement for good behaviors
            2. Gentle guidance for improvements needed
            3. Today's focus areas (1-2 specific items)
            4. Motivational message
            5. Quick mental preparation tips
            6. Reminder of key trading principles
            
            Keep it concise, positive, and actionable for today's trading session.
            
            Provide daily coaching in JSON format.
            """
            
            task = Task(
                description=task_description,
                agent=self.agent,
                expected_output="Daily coaching guidance in JSON format with focus areas and motivation"
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
                        daily_coaching = json.loads(json_match.group())
                    else:
                        daily_coaching = self._structure_daily_response(result)
                else:
                    daily_coaching = result
                
                logger.info("Daily coaching generated")
                return daily_coaching
                
            except json.JSONDecodeError:
                return self._structure_daily_response(str(result))
            
        except Exception as e:
            logger.error(f"Error generating daily coaching: {e}")
            return self._get_default_daily_coaching()
    
    def generate_weekly_review(self, week_trades: List[Dict[str, Any]], week_psychology: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate weekly performance review and coaching"""
        if not self.enabled:
            return self._get_default_weekly_review()
        
        try:
            # Calculate weekly stats
            total_trades = len(week_trades)
            winning_trades = len([t for t in week_trades if t.get('pnl', 0) > 0])
            week_pnl = sum(t.get('pnl', 0) for t in week_trades)
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            context = f"""
            Weekly Performance Summary:
            - Total Trades: {total_trades}
            - Win Rate: {win_rate:.1f}%
            - Weekly P&L: ${week_pnl:.2f}
            - Psychology Notes: {len(week_psychology)} entries
            
            Week's Trading Details:
            {json.dumps(week_trades, indent=2)}
            
            Psychology Summary:
            {json.dumps(week_psychology, indent=2)}
            """
            
            # Create weekly review task
            task_description = f"""
            Conduct a comprehensive weekly review and provide coaching guidance:
            
            {context}
            
            Your weekly review should include:
            1. Performance Analysis: What went well, what didn't
            2. Progress Assessment: Movement toward goals
            3. Pattern Recognition: Emerging patterns this week
            4. Lessons Learned: Key takeaways from the week
            5. Next Week's Focus: Specific areas to improve
            6. Celebration: Acknowledge successes and progress
            7. Course Corrections: Adjustments needed
            
            Provide comprehensive weekly review in JSON format.
            """
            
            task = Task(
                description=task_description,
                agent=self.agent,
                expected_output="Weekly review and coaching in JSON format with analysis and guidance"
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
                        weekly_review = json.loads(json_match.group())
                    else:
                        weekly_review = self._structure_weekly_response(result, week_trades)
                else:
                    weekly_review = result
                
                logger.info("Weekly review generated")
                return weekly_review
                
            except json.JSONDecodeError:
                return self._structure_weekly_response(str(result), week_trades)
            
        except Exception as e:
            logger.error(f"Error generating weekly review: {e}")
            return self._get_default_weekly_review()
    
    def _structure_coaching_response(self, analysis_text: str, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Structure the coaching response when JSON parsing fails"""
        return {
            "overall_assessment": {
                "trading_level": "Intermediate",
                "strengths": ["Systematic approach", "Consistent execution"],
                "weaknesses": ["Setup selection", "Risk management"],
                "trajectory": "Positive with room for improvement"
            },
            "performance_coaching": {
                "technical_improvements": ["Focus on high-probability setups", "Improve target selection"],
                "risk_management": ["Maintain consistent position sizing", "Stick to stop losses"],
                "execution_tips": ["Follow your trading plan", "Avoid emotional decisions"]
            },
            "psychology_coaching": {
                "emotional_patterns": ["Work on patience", "Manage FOMO"],
                "mental_discipline": ["Daily meditation", "Pre-trade routine"],
                "confidence_building": ["Keep detailed records", "Celebrate small wins"]
            },
            "action_plan": {
                "immediate_actions": ["Review top 3 setups", "Implement pre-trade checklist"],
                "weekly_goals": ["Maintain trading discipline", "Complete daily reviews"],
                "monthly_objectives": ["Improve win rate by 5%", "Develop advanced skills"]
            },
            "motivational_message": "You're on the right track! Focus on consistency and the results will follow.",
            "agent_analysis": analysis_text[:500] + "..." if len(analysis_text) > 500 else analysis_text
        }
    
    def _structure_daily_response(self, analysis_text: str) -> Dict[str, Any]:
        """Structure the daily coaching response"""
        return {
            "daily_focus": ["Follow your trading plan", "Maintain emotional discipline"],
            "preparation_tips": ["Review market conditions", "Check your emotional state"],
            "motivational_message": "Stay focused on the process, not the outcome",
            "key_reminders": ["Risk management first", "Quality over quantity"],
            "agent_message": analysis_text[:300] + "..." if len(analysis_text) > 300 else analysis_text
        }
    
    def _structure_weekly_response(self, analysis_text: str, week_trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Structure the weekly review response"""
        total_trades = len(week_trades)
        week_pnl = sum(t.get('pnl', 0) for t in week_trades)
        
        return {
            "performance_summary": {
                "total_trades": total_trades,
                "weekly_pnl": week_pnl,
                "assessment": "Good progress" if week_pnl > 0 else "Learning week"
            },
            "lessons_learned": ["Stick to your plan", "Emotions affect decisions", "Patience pays off"],
            "next_week_focus": ["Improve setup selection", "Maintain discipline"],
            "celebration": "Good job maintaining consistency!",
            "course_corrections": ["Review losing trades", "Adjust position sizing"],
            "agent_analysis": analysis_text[:500] + "..." if len(analysis_text) > 500 else analysis_text
        }
    
    def _get_default_coaching_plan(self) -> Dict[str, Any]:
        """Default coaching plan when agent is disabled"""
        return {
            "overall_assessment": {
                "trading_level": "Assessment unavailable",
                "strengths": ["Enable AI for assessment"],
                "weaknesses": ["Enable AI for assessment"],
                "trajectory": "Enable AI for coaching guidance"
            },
            "performance_coaching": {
                "technical_improvements": ["Enable AI for personalized guidance"],
                "risk_management": ["Enable AI for risk analysis"],
                "execution_tips": ["Enable AI for execution coaching"]
            },
            "psychology_coaching": {
                "emotional_patterns": ["Enable AI for psychology coaching"],
                "mental_discipline": ["Enable AI for mental training"],
                "confidence_building": ["Enable AI for confidence strategies"]
            },
            "action_plan": {
                "immediate_actions": ["Enable AI features"],
                "weekly_goals": ["Enable AI for goal setting"],
                "monthly_objectives": ["Enable AI for long-term planning"]
            },
            "motivational_message": "Enable AI features to receive personalized coaching and mentorship!"
        }
    
    def _get_default_daily_coaching(self) -> Dict[str, Any]:
        """Default daily coaching when agent is disabled"""
        return {
            "daily_focus": ["Follow your trading plan", "Maintain discipline"],
            "preparation_tips": ["Review your strategy", "Check market conditions"],
            "motivational_message": "Stay consistent and focused on your goals",
            "key_reminders": ["Risk management first", "Quality over quantity"]
        }
    
    def _get_default_weekly_review(self) -> Dict[str, Any]:
        """Default weekly review when agent is disabled"""
        return {
            "performance_summary": {
                "assessment": "Enable AI for detailed weekly analysis"
            },
            "lessons_learned": ["Enable AI for personalized insights"],
            "next_week_focus": ["Enable AI for focused guidance"],
            "celebration": "Great job trading this week!",
            "course_corrections": ["Enable AI for improvement suggestions"]
        }

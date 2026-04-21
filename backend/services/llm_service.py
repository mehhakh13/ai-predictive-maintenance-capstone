"""
LLM Service - Claude API Integration with Function Calling (Phase 2)
"""
import json
from typing import List, Dict, Any, Optional
import anthropic
import config
from tools.cost_tools import COST_TOOLS
from tools.risk_tools import RISK_TOOLS
from tools.building_tools import BUILDING_TOOLS
from tools.trend_tools import TREND_TOOLS


class LLMService:
    """Service for interacting with Claude API and managing function calling"""

    def __init__(self):
        if not config.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not set in environment")

        self.client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        self.model = config.CLAUDE_MODEL

        # Combine all tool definitions
        self.tools = self._prepare_tools()
        self.tool_functions = self._prepare_tool_functions()

        print(f"✓ LLM Service initialized with {len(self.tools)} tools")

    def _prepare_tools(self) -> List[Dict[str, Any]]:
        """Prepare tools in Claude API format"""
        all_tools = COST_TOOLS + RISK_TOOLS + BUILDING_TOOLS + TREND_TOOLS

        claude_tools = []
        for tool in all_tools:
            claude_tools.append({
                "name": tool["name"],
                "description": tool["description"],
                "input_schema": tool["parameters"]
            })

        return claude_tools

    def _prepare_tool_functions(self) -> Dict[str, callable]:
        """Create a mapping of tool names to their functions"""
        all_tools = COST_TOOLS + RISK_TOOLS + BUILDING_TOOLS + TREND_TOOLS
        return {tool["name"]: tool["function"] for tool in all_tools}

    def _execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool function and return the result"""
        if tool_name not in self.tool_functions:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found"
            }

        try:
            func = self.tool_functions[tool_name]
            result = func(**tool_input)
            return result
        except Exception as e:
            return {
                "success": False,
                "error": f"Error executing {tool_name}: {str(e)}"
            }

    def chat(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Send a message to Claude and handle function calling

        Args:
            user_message: The user's question
            conversation_history: Previous messages in the conversation

        Returns:
            Dictionary with response, suggestions, and any data/charts
        """
        if conversation_history is None:
            conversation_history = []

        # Build messages array
        messages = []

        # Add conversation history (convert from our format to Claude format)
        for msg in conversation_history[-config.MAX_CONVERSATION_HISTORY:]:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        # Add current user message
        messages.append({
            "role": "user",
            "content": user_message
        })

        # System prompt
        system_prompt = """You are an expert Predictive Maintenance AI Assistant for university facilities.

Your role:
- Answer questions about maintenance costs, risks, defects, buildings, and trends
- Use the provided tools to query real data from the FMUCD (Facilities Management University Campus Dataset)
- Provide clear, actionable insights with specific numbers
- Format responses in markdown with headers, bullets, and bold text
- Always cite specific data points (costs, counts, percentages)

Guidelines:
- Use tools to get accurate data - don't make up numbers
- For cost questions, use cost_tools
- For risk questions, use risk_tools
- For building questions, use building_tools
- For trend/time-based questions, use trend_tools
- Keep responses concise but informative
- Suggest relevant follow-up questions

Available subsystems include: HVAC, Plumbing, Electrical, Lighting, Elevators, Roofing, etc.
"""

        # Make initial API call
        response = self.client.messages.create(
            model=self.model,
            max_tokens=config.MAX_TOKENS,
            temperature=config.DEFAULT_TEMPERATURE,
            system=system_prompt,
            messages=messages,
            tools=self.tools
        )

        # Handle function calling loop
        tool_results = []
        function_calls = []

        while response.stop_reason == "tool_use":
            # Execute all tool calls
            new_messages = []

            for block in response.content:
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_input = block.input

                    print(f"[LLM] Calling tool: {tool_name} with {tool_input}")
                    function_calls.append(tool_name)

                    # Execute the tool
                    result = self._execute_tool(tool_name, tool_input)
                    tool_results.append(result)

                    # Add tool result to messages
                    new_messages.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result)
                    })

            # Continue conversation with tool results
            messages.append({
                "role": "assistant",
                "content": response.content
            })
            messages.append({
                "role": "user",
                "content": new_messages
            })

            # Get next response
            response = self.client.messages.create(
                model=self.model,
                max_tokens=config.MAX_TOKENS,
                temperature=config.DEFAULT_TEMPERATURE,
                system=system_prompt,
                messages=messages,
                tools=self.tools
            )

        # Extract final text response
        final_text = ""
        for block in response.content:
            if hasattr(block, "text"):
                final_text += block.text

        # Generate suggestions based on context
        suggestions = self._generate_suggestions(user_message, function_calls)

        # Extract chart data if available from tool results
        chart_data = None
        chart_type = None
        for result in tool_results:
            if result.get("success") and result.get("chart_data"):
                chart_data = {"chart_data": result["chart_data"]}
                chart_type = "cost_bar"  # Default to bar chart
                break

        return {
            "response": final_text,
            "suggestions": suggestions,
            "data": chart_data,
            "chart_type": chart_type,
            "function_calls": function_calls
        }

    def _generate_suggestions(self, user_message: str, function_calls: List[str]) -> List[str]:
        """Generate smart follow-up suggestions based on context"""
        msg_lower = user_message.lower()

        # If they asked about costs
        if any(word in msg_lower for word in ['cost', 'expensive', 'money', 'budget']):
            return [
                "Which buildings have the highest costs?",
                "Show me cost trends over time",
                "What's the risk level for expensive systems?"
            ]

        # If they asked about risks
        if any(word in msg_lower for word in ['risk', 'failure', 'probability']):
            return [
                "What are the costs for high-risk systems?",
                "Show me buildings with highest risk",
                "What trends do you see in risky systems?"
            ]

        # If they asked about buildings
        if any(word in msg_lower for word in ['building', 'facility', 'location']):
            return [
                "What systems fail most in these buildings?",
                "Show me cost breakdown by building",
                "Compare risk levels across buildings"
            ]

        # If they asked about trends
        if any(word in msg_lower for word in ['trend', 'over time', 'monthly', 'history']):
            return [
                "What's driving these trends?",
                "Show me building-level trends",
                "Compare this to last year"
            ]

        # Default suggestions
        return [
            "What are the most expensive systems?",
            "Show me high-risk systems",
            "Which buildings need attention?"
        ]


# Singleton instance
_llm_service = None

def get_llm_service() -> LLMService:
    """Get or create the LLM service singleton"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service

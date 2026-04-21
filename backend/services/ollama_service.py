"""
Ollama LLM Service - Local AI Integration (FREE)
Replaces Claude API with Ollama for cost-free operation
"""
import json
import requests
from typing import List, Dict, Any, Optional
import config
from tools.cost_tools import COST_TOOLS
from tools.risk_tools import RISK_TOOLS
from tools.building_tools import BUILDING_TOOLS
from tools.trend_tools import TREND_TOOLS


class OllamaService:
    """Service for interacting with local Ollama models"""

    def __init__(self):
        self.base_url = config.OLLAMA_BASE_URL
        self.model = config.OLLAMA_MODEL
        self.timeout = config.OLLAMA_TIMEOUT

        # Combine all tool definitions
        self.tools = self._prepare_tools()
        self.tool_functions = self._prepare_tool_functions()

        # Verify Ollama is running
        self._check_ollama_connection()

        print(f"✓ Ollama Service initialized with {len(self.tools)} tools")
        print(f"  Model: {self.model}")
        print(f"  Base URL: {self.base_url}")

    def _check_ollama_connection(self):
        """Check if Ollama is running and accessible"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]

                if not any(self.model in name for name in model_names):
                    print(f"\n⚠️  Warning: Model '{self.model}' not found!")
                    print(f"   Available models: {', '.join(model_names)}")
                    print(f"   Run: ollama pull {self.model}")

        except requests.exceptions.ConnectionError:
            print(f"\n⚠️  Warning: Cannot connect to Ollama at {self.base_url}")
            print("   Make sure Ollama is running: ollama serve")

    def _prepare_tools(self) -> List[Dict[str, Any]]:
        """Prepare tools in a simple format for Ollama"""
        all_tools = COST_TOOLS + RISK_TOOLS + BUILDING_TOOLS + TREND_TOOLS

        tools_description = []
        for tool in all_tools:
            tool_desc = {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["parameters"]
            }
            tools_description.append(tool_desc)

        return tools_description

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

    def _build_system_prompt(self) -> str:
        """Build system prompt with tool descriptions"""

        tools_text = "\n\n".join([
            f"**{tool['name']}**\n"
            f"Description: {tool['description']}\n"
            f"Parameters: {json.dumps(tool['parameters'], indent=2)}"
            for tool in self.tools
        ])

        return f"""You are an expert Predictive Maintenance AI Assistant for university facilities.

Your role:
- Answer questions about maintenance costs, risks, defects, buildings, and trends
- Use the provided tools to query real data from the FMUCD dataset
- Provide clear, actionable insights with specific numbers
- Keep responses concise but informative

Available Tools:
{tools_text}

When you need data, respond ONLY with a JSON tool call in this exact format:
{{
  "tool": "tool_name",
  "parameters": {{"param": "value"}}
}}

After receiving tool results, provide a natural language response to the user.

Guidelines:
- Use tools to get accurate data - don't make up numbers
- For cost questions, use cost_tools (get_most_expensive_systems, etc.)
- For risk questions, use risk_tools
- For building questions, use building_tools
- For trend/time questions, use trend_tools
- Keep responses under 200 words
- Use bullet points and bold text for clarity
"""

    def _format_conversation_history(self, history: List[Dict[str, str]]) -> str:
        """Format conversation history for Ollama"""
        if not history:
            return ""

        formatted = "\n\nPrevious conversation:\n"
        for msg in history[-6:]:  # Last 6 messages for context
            role = msg["role"].capitalize()
            content = msg["content"][:200]  # Truncate long messages
            formatted += f"{role}: {content}\n"

        return formatted

    def _parse_tool_call(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Try to extract a tool call from the response"""
        # Look for JSON in the response
        import re

        # Try to find JSON blocks
        json_pattern = r'\{[^{}]*"tool"[^{}]*\}'
        matches = re.findall(json_pattern, response_text)

        for match in matches:
            try:
                tool_call = json.loads(match)
                if "tool" in tool_call:
                    return tool_call
            except json.JSONDecodeError:
                continue

        # Check if response mentions a tool name
        for tool in self.tools:
            tool_name = tool["name"]
            if tool_name in response_text.lower():
                # Try to extract parameters
                return {
                    "tool": tool_name,
                    "parameters": {}
                }

        return None

    def chat(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Send a message to Ollama and handle tool calling

        Args:
            user_message: The user's question
            conversation_history: Previous messages in the conversation

        Returns:
            Dictionary with response, suggestions, and any data/charts
        """
        if conversation_history is None:
            conversation_history = []

        system_prompt = self._build_system_prompt()
        history_text = self._format_conversation_history(conversation_history)

        # Build the full prompt
        full_prompt = f"{system_prompt}\n{history_text}\n\nUser: {user_message}\n\nAssistant:"

        # Call Ollama API
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": config.DEFAULT_TEMPERATURE,
                        "num_predict": 500  # Limit response length
                    }
                },
                timeout=self.timeout
            )

            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code}")

            response_data = response.json()
            response_text = response_data.get("response", "")

        except Exception as e:
            print(f"Error calling Ollama: {e}")
            return {
                "response": "I'm having trouble connecting to the AI service. Please make sure Ollama is running.",
                "suggestions": [
                    "Check if Ollama is installed: ollama --version",
                    "Start Ollama: ollama serve",
                    f"Pull model: ollama pull {self.model}"
                ],
                "data": None,
                "chart_type": None,
                "function_calls": []
            }

        # Check if response contains a tool call
        tool_call = self._parse_tool_call(response_text)
        function_calls = []
        tool_results = []

        if tool_call:
            tool_name = tool_call.get("tool")
            tool_params = tool_call.get("parameters", {})

            print(f"[Ollama] Calling tool: {tool_name} with {tool_params}")
            function_calls.append(tool_name)

            # Execute the tool
            result = self._execute_tool(tool_name, tool_params)
            tool_results.append(result)

            # Make second call with tool results
            tool_result_text = json.dumps(result, indent=2)
            follow_up_prompt = f"{full_prompt}\n\n{response_text}\n\nTool Result:\n{tool_result_text}\n\nNow provide a natural language response to the user based on this data:"

            try:
                follow_up_response = requests.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": follow_up_prompt,
                        "stream": False,
                        "options": {
                            "temperature": config.DEFAULT_TEMPERATURE,
                            "num_predict": 500
                        }
                    },
                    timeout=self.timeout
                )

                if follow_up_response.status_code == 200:
                    response_text = follow_up_response.json().get("response", response_text)

            except Exception as e:
                print(f"Error in follow-up call: {e}")

        # Generate suggestions
        suggestions = self._generate_suggestions(user_message, function_calls)

        # Extract chart data if available
        chart_data = None
        chart_type = None
        for result in tool_results:
            if result.get("success") and result.get("chart_data"):
                chart_data = {"chart_data": result["chart_data"]}
                chart_type = "cost_bar"
                break

        return {
            "response": response_text.strip(),
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
_ollama_service = None

def get_ollama_service() -> OllamaService:
    """Get or create the Ollama service singleton"""
    global _ollama_service
    if _ollama_service is None:
        _ollama_service = OllamaService()
    return _ollama_service

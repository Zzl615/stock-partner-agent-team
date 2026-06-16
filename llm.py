import os
import sys
import json
import config
import tools

# Define python functions to be used as tools by Gemini
def query_westock_data(command: str) -> str:
    """
    Query stock quotes, financials, or macro data using westock-data.
    Args:
        command: The command string to pass to westock-data, e.g. 'quote sh600519'
    """
    return tools.query_westock_data(command)

def query_westock_tool(command: str) -> str:
    """
    Query stock filtering or screening results using westock-tool.
    Args:
        command: The command string to pass to westock-tool, e.g. 'strategy macd_golden'
    """
    return tools.query_westock_tool(command)

# Mapping of function names to callable python functions
TOOL_MAP = {
    "query_westock_data": query_westock_data,
    "query_westock_tool": query_westock_tool
}

def get_openai_tools_schema():
    return [
        {
            "type": "function",
            "function": {
                "name": "query_westock_data",
                "description": "Query stock quotes, financials, or A-share/H-share/US-share market data.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The command string, e.g., 'quote sh600519' or 'finance sh600519 --num 4'"
                        }
                    },
                    "required": ["command"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "query_westock_tool",
                "description": "Filter A-share/H-share/US-share stocks based on quantitative strategies or filters.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The command string, e.g., 'strategy macd_golden' or 'filter --preset LowPE'"
                        }
                    },
                    "required": ["command"]
                }
            }
        }
    ]

def call_gemini(system_prompt, user_query, max_turns=5):
    """
    Call Gemini using the native google-generativeai SDK.
    """
    try:
        import google.generativeai as genai
    except ImportError:
        print("Error: google-generativeai package not installed.", file=sys.stderr)
        return None

    if not config.GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY is not set.", file=sys.stderr)
        return None

    genai.configure(api_key=config.GEMINI_API_KEY)
    
    # We pass the functions directly to Gemini model
    model = genai.GenerativeModel(
        model_name=config.GEMINI_MODEL,
        tools=[query_westock_data, query_westock_tool],
        system_instruction=system_prompt
    )
    
    chat = model.start_chat(enable_automatic_function_calling=True)
    response = chat.send_message(user_query)
    return response.text

def call_openai(system_prompt, user_query, max_turns=5):
    """
    Call OpenAI using the openai SDK with tool calling.
    """
    try:
        import openai
    except ImportError:
        print("Error: openai package not installed.", file=sys.stderr)
        return None

    # Determine base url and api key based on provider
    if config.LLM_PROVIDER == "gemini":
        api_key = config.GEMINI_API_KEY
        base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
        model_name = config.GEMINI_MODEL
    else:
        api_key = config.OPENAI_API_KEY
        base_url = None
        model_name = config.OPENAI_MODEL

    if not api_key:
        print(f"Error: API key for provider '{config.LLM_PROVIDER}' is not set.", file=sys.stderr)
        return None

    client = openai.OpenAI(api_key=api_key, base_url=base_url)
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query}
    ]
    
    for turn in range(max_turns):
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                tools=get_openai_tools_schema(),
                tool_choice="auto"
            )
            
            response_msg = response.choices[0].message
            messages.append(response_msg)
            
            # If no tool calls, this is the final answer
            if not response_msg.tool_calls:
                return response_msg.content
                
            # Execute tool calls
            for tool_call in response_msg.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)
                command = func_args.get("command", "")
                
                func = TOOL_MAP.get(func_name)
                if func:
                    result = func(command)
                else:
                    result = f"Error: Tool '{func_name}' not found."
                    
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": func_name,
                    "content": result
                })
        except Exception as e:
            print(f"Error in OpenAI ReAct loop turn {turn}: {e}", file=sys.stderr)
            return f"**Error executing LLM loop:** {e}"
            
    return "Error: ReAct loop exceeded maximum turns."

def run_agent(agent_name: str, system_prompt: str, user_query: str) -> str:
    """
    Runs an agent with its system prompt and user query.
    Chooses the appropriate backend based on config.
    """
    print(f"\n[Running Agent] {agent_name}...")
    
    # Try using OpenAI interface first as it handles tool-calling ReAct loop uniformly
    # (Gemini's OpenAI compatibility endpoint works perfectly for this).
    result = call_openai(system_prompt, user_query)
    if result:
        return result
        
    # Fallback to native Gemini SDK if openai library fails
    print(f"[LLM] Falling back to native Gemini SDK for {agent_name}...")
    result = call_gemini(system_prompt, user_query)
    if result:
        return result
        
    return f"Error: Failed to execute agent {agent_name} with provider {config.LLM_PROVIDER}."

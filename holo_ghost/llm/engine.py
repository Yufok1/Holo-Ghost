"""
HOLO-GHOST LLM Engine

Interface to LLM backends for intelligence.
Supports vLLM, local models, and OpenAI API.

"I think, therefore I observe."
"""

import asyncio
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


# System prompt for the Ghost's intelligence
GHOST_SYSTEM_PROMPT = """You are HOLO-GHOST, a digital observer that watches human-computer interaction.

You see:
- Mouse movements (position, velocity, acceleration)
- Keyboard inputs (keys, timing, patterns)
- Game context (active game, window focus)

Your role:
- Analyze input patterns for anomalies (inhuman behavior)
- Identify skill patterns and player tendencies
- Generate insights about gameplay
- Flag suspicious activity with confidence levels

You speak with:
- Technical precision when analyzing data
- Subtle wit when commenting on gameplay
- Neutrality when flagging (no accusations, just observations)

When analyzing inputs, consider:
- Human reaction time is typically 150-300ms
- Human aim has micro-corrections, not perfect lines
- Inhuman: >10,000 degrees/second rotation, instant direction changes
- Suspicious: Perfect recoil control, identical movement patterns

Format flags as:
{
    "type": "flag_type",
    "confidence": 0.0-1.0,
    "description": "brief explanation"
}

Keep responses concise. Data speaks for itself."""


@dataclass
class LLMResponse:
    """Response from LLM engine."""
    text: str
    flags: List[Dict[str, Any]] = None
    insight: Optional[str] = None
    tokens_used: int = 0


class LLMEngine:
    """
    LLM engine for Ghost intelligence.
    
    Supports multiple backends:
    - vLLM (local GPU serving)
    - OpenAI API
    - Local llama.cpp (future)
    """
    
    def __init__(
        self,
        engine_type: str = "vllm",
        model: str = "mistralai/Mistral-Nemo-Instruct-2407",
        url: str = "http://localhost:8000/v1",
        api_key: Optional[str] = None,
        light_mode: bool = False,
    ):
        """
        Initialize LLM engine.
        
        Args:
            engine_type: "vllm", "openai", or "local"
            model: Model identifier
            url: API URL (for vLLM or custom endpoint)
            api_key: API key (for OpenAI)
            light_mode: Whether to optimize for low-end hardware
        """
        self.engine_type = engine_type
        self.model = model
        self.url = url
        self.api_key = api_key or "not-needed"
        self.light_mode = light_mode
        
        self._client: Optional[AsyncOpenAI] = None
        self._connected = False

    async def connect(self) -> bool:
        """Connect to LLM backend."""
        # If engine is 'local' and light_mode is enabled, we could initialize llama-cpp here.
        # For now, we'll continue using the AsyncOpenAI interface as it's common for many local runners (LM Studio, Ollama).
        if self.engine_type == "local" and self.light_mode:
             print(f"[LLM] Entering Light Mode (Potato-friendly). Optimizing for {self.model}")

        if not OPENAI_AVAILABLE:
            print("[LLM] openai package not installed")
            return False
        
        try:
            self._client = AsyncOpenAI(
                base_url=self.url,
                api_key=self.api_key,
            )
            
            # Test connection
            if self.engine_type == "vllm":
                await self._client.models.list()
            
            self._connected = True
            print(f"[LLM] Connected to {self.engine_type} at {self.url}")
            return True
            
        except Exception as e:
            print(f"[LLM] Connection failed: {e}")
            return False
    
    async def analyze_inputs(
        self,
        inputs: List[Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze input sequence for patterns and anomalies.
        
        Args:
            inputs: List of InputSnapshot objects or dicts
            context: Additional context (game, player, etc.)
            
        Returns:
            Analysis result with flags and insights
        """
        if not self._connected:
            return {"flags": [], "insight": None}
        
        # Build analysis prompt
        input_summary = self._summarize_inputs(inputs)
        
        prompt = f"""Analyze this input sequence:

{input_summary}

Context: {context or 'No additional context'}

Look for:
1. Inhuman patterns (impossible speeds, perfect lines)
2. Macro/automation signatures
3. Notable skill patterns
4. Anything unusual

Respond with JSON containing "flags" array and optional "insight" string."""

        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": GHOST_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3,  # More deterministic for analysis
            )
            
            text = response.choices[0].message.content
            
            # Try to parse JSON response
            return self._parse_analysis(text)
            
        except Exception as e:
            print(f"[LLM] Analysis failed: {e}")
            return {"flags": [], "insight": None}
    
    async def ask(
        self,
        question: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Ask the Ghost a question.
        
        Args:
            question: Natural language question
            context: Current context
            
        Returns:
            Ghost's response
        """
        if not self._connected:
            return "LLM not connected"
        
        context_str = f"\n\nCurrent context:\n{self._format_context(context)}" if context else ""
        
        prompt = f"{question}{context_str}"
        
        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": GHOST_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.7,
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error: {e}"
    
    async def summarize_session(
        self,
        session_data: Dict[str, Any]
    ) -> str:
        """Generate natural language session summary."""
        if not self._connected:
            return "LLM not connected"
        
        prompt = f"""Summarize this gaming session:

Duration: {session_data.get('duration', 0):.0f} seconds
Game: {session_data.get('game', 'Unknown')}
Total inputs: {session_data.get('total_inputs', 0)}
Flags raised: {session_data.get('total_flags', 0)}
Recent flags: {session_data.get('recent_flags', [])}

Generate a brief, engaging summary of the session."""

        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": GHOST_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.8,
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error generating summary: {e}"
    
    def _summarize_inputs(self, inputs: List[Any]) -> str:
        """Create summary of input sequence for LLM."""
        lines = []
        
        for i, inp in enumerate(inputs[-20:]):  # Last 20 inputs
            if hasattr(inp, 'to_dict'):
                d = inp.to_dict()
            else:
                d = inp
            
            mouse = d.get('mouse', {})
            kb = d.get('keyboard', {})
            
            line = f"[{i}] dx:{mouse.get('dx', 0):+4d} dy:{mouse.get('dy', 0):+4d} vel:{mouse.get('velocity', 0):>7.1f} acc:{mouse.get('acceleration', 0):>8.1f}"
            
            if mouse.get('buttons', {}).get('left'):
                line += " CLICK"
            if kb.get('pressed'):
                line += f" keys:{kb['pressed']}"
            
            lines.append(line)
        
        return "\n".join(lines)
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context for prompt."""
        if not context:
            return "No context"
        
        lines = []
        for k, v in context.items():
            if isinstance(v, list):
                v = f"[{len(v)} items]"
            lines.append(f"- {k}: {v}")
        
        return "\n".join(lines)
    
    def _parse_analysis(self, text: str) -> Dict[str, Any]:
        """Parse LLM analysis response."""
        import json
        import re
        
        # Try to find JSON in response
        json_match = re.search(r'\{[\s\S]*\}', text)
        
        if json_match:
            try:
                result = json.loads(json_match.group())
                return {
                    "flags": result.get("flags", []),
                    "insight": result.get("insight")
                }
            except json.JSONDecodeError:
                pass
        
        # Fallback: extract any mentioned flags
        flags = []
        
        if "inhuman" in text.lower() or "suspicious" in text.lower():
            flags.append({
                "type": "llm_detected",
                "confidence": 0.7,
                "description": text[:200]
            })
        
        return {"flags": flags, "insight": text if len(text) < 500 else None}

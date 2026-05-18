"""
agents/dynamic_research_agent.py
Expert research agent — searches the web 3x and writes a structured report.
"""
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

load_dotenv()

def _create_tools():
    try:
        from langchain_tavily import TavilySearch
        return [TavilySearch(max_results=5)]
    except Exception as e:
        print(f"⚠️  Tavily unavailable: {e}. Running without web search.")
        return []

_tools = _create_tools()
_llm   = ChatGroq(model="meta-llama/llama-4-scout-17b-16e-instruct", temperature=0.4, max_tokens=4096)
_agent = create_react_agent(model=_llm, tools=_tools)

_SYSTEM_PROMPT = """You are an expert research analyst, similar to Perplexity AI.

SEARCH STRATEGY — always search 3 times with different angles:
1. First  → broad overview
2. Second → recent news, statistics, latest developments
3. Third  → specific details, examples, expert opinions

STRUCTURE — pick subheadings that fit the topic:
- Person:      Early Life | Rise to Prominence | Achievements | Controversies | Legacy
- Technology:  What It Is | How It Works | Who Uses It | Limitations | Future Outlook
- Concept:     Core Idea | History | How It Works | Applications | Open Questions
- Event:       Background | What Happened | Key Players | Impact | Long-Term Effects
- Comparison:  At a Glance | Option A | Option B | Head-to-Head | Verdict
- Other:       use your best judgment

WRITING RULES:
- Full paragraphs under each heading (no bullet dumps)
- Use ## for subheadings
- Include real facts, numbers, names, dates
- Minimum 450 words
- End with ## Bottom Line — one paragraph summary

BANNED headings: Overview | Key Findings | Detailed Analysis | Conclusion
"""

def run_research_agent(topic: str) -> str:
    result = _agent.invoke({
        "messages": [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=f"Research this topic and write the full report: {topic}"),
        ]
    })
    return result["messages"][-1].content

if __name__ == "__main__":
    topic = input("Enter a research topic: ").strip()
    print(run_research_agent(topic))

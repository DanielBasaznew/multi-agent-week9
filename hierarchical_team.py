import os
from dotenv import load_dotenv
from crewai import Agent, Crew, Process, Task, LLM
from crewai.tools import tool
from duckduckgo_search import DDGS

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

# 1. Models: Split Tiers
# Higher reasoning model for delegation & coordination
llm_manager = LLM(
    model="gemini/gemini-3.5-flash-lite",
    api_key=api_key,
    temperature=0.1,
)

# Cost-effective, fast model for individual worker agents
llm_worker = LLM(
    model="gemini/gemini-3.1-flash-lite",
    api_key=api_key,
    temperature=0.2,
)

# 2. Web Search Tool
@tool("web_search")
def web_search(query: str) -> str:
    """Search DuckDuckGo for recent information on a given query."""
    try:
        results = DDGS().text(query, max_results=4)
        if not results:
            return f"No results found for query: {query}"
        formatted = []
        for r in results:
            title = r.get("title", "No Title")
            snippet = r.get("body", "No Snippet")
            formatted.append(f"- {title}: {snippet}")
        return "\n".join(formatted)
    except Exception as e:
        return f"Search failed with error: {str(e)}"

# 3. Specialized Agents (powered by llm_worker)
researcher = Agent(
    role="Senior Research Analyst",
    goal="Gather verified facts, statistics, and 3 key trends on emerging tech topics.",
    backstory="You are a dedicated researcher. Your job is ONLY to gather and summarize factual findings. You do not write articles or perform editorial reviews.",
    tools=[web_search],
    llm=llm_worker,
    verbose=True,
    max_iter=5,
)

writer = Agent(
    role="Tech Content Strategist",
    goal="Synthesize research briefings into engaging, 3-paragraph executive summaries for leadership.",
    backstory="You are a professional writer. You take factual notes from researchers and turn them into clear, polished 3-paragraph summaries.",
    llm=llm_worker,
    verbose=True,
    max_iter=5,
)

reviewer = Agent(
    role="Editorial Quality Assurance Specialist",
    goal="Audit drafts against research briefings for accuracy and structure, issuing APPROVED or REVISION NEEDED.",
    backstory="You are an editor. You review drafts written by the writer, checking them against the research notes for accuracy and tone.",
    llm=llm_worker,
    verbose=True,
    max_iter=5,
)

# 4. Modular Tasks
topic = "The Impact of Generative AI and Autonomous Agents on Software Engineering Jobs 2025 2026"

research_task = Task(
    description=f"Conduct research on '{topic}'. Identify 3 key trends or shifts in software engineering roles with verified facts.",
    expected_output="A structured bullet-point research briefing highlighting 3 distinct industry trends.",
    agent=researcher,
)

writing_task = Task(
    description="Using the researcher's briefing, compose a concise, 3-paragraph executive summary for engineering leadership.",
    expected_output="A 3-paragraph executive summary based strictly on the research briefing.",
    agent=writer,
)

review_task = Task(
    description="Review the writer's 3-paragraph summary against the researcher's findings. Check for factual fidelity and structure. End with APPROVED or REVISION NEEDED.",
    expected_output="An editorial critique followed by an explicit verdict header (APPROVED or REVISION NEEDED).",
    agent=reviewer,
)

# 5. Hierarchical Crew (with manager_llm)
crew = Crew(
    agents=[researcher, writer, reviewer],
    tasks=[research_task, writing_task, review_task],
    process=Process.hierarchical,
    manager_llm=llm_manager,
    verbose=True,
)

if __name__ == "__main__":
    print(f"--- Starting Hierarchical Research Team on Topic: {topic} ---\n")
    result = crew.kickoff()
    print("\n--- Final Output ---\n")
    print(result)
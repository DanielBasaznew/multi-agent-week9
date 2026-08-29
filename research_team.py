import os
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool
from dotenv import load_dotenv
from duckduckgo_search import DDGS

load_dotenv()

# Ensure both environment variables are set for the native Google provider
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if api_key:
    os.environ["GEMINI_API_KEY"] = api_key
    os.environ["GOOGLE_API_KEY"] = api_key

# 1. Configure the Gemini LLM
gemini_llm = LLM(
    model="gemini/gemini-3.1-flash-lite",
    api_key=api_key,
    temperature=0.7,
)

# 2. Define Custom Search Tool
@tool("web_search")
def web_search(query: str) -> str:
    """Search the web for recent information, breakthroughs, and verified data.
    Useful when you need up-to-date facts on technical topics.
    """
    try:
        results = DDGS().text(query, max_results=4)
        if not results:
            return f"No results found for query: {query}"
        
        formatted = []
        for r in results:
            title = r.get("title", "No Title")
            snippet = r.get("body", "")
            formatted.append(f"- {title}: {snippet}")
        return "\n".join(formatted)
    except Exception as e:
        return f"Search failed with error: {str(e)}"

# 3. Define the Three Specialized Agents
researcher = Agent(
    role="Senior Research Analyst",
    goal="Uncover cutting-edge developments, facts, and breakthrough concepts in {topic}",
    backstory="""You are a rigorous technical research analyst at a premier think tank.
    You gather accurate, factual information using real-time web search and summarize
    concrete data without speculation.""",
    tools=[web_search],
    max_iter=5,
    llm=gemini_llm,
    verbose=True,
)

writer = Agent(
    role="Tech Content Strategist",
    goal="Craft compelling, accessible explanations based strictly on technical research",
    backstory="""You are an expert communicator who translates dense engineering
    and scientific briefings into engaging, clear articles for business and technical leaders.""",
    llm=gemini_llm,
    verbose=True,
)

reviewer = Agent(
    role="Editorial Quality Assurance Specialist",
    goal="Verify that the drafted overview strictly reflects the research findings and meets high clarity standards",
    backstory="""You are a meticulous technical editor. You review articles against
    the source briefing to check for factual consistency, missing nuances, and clarity.
    You deliver honest, highly specific critiques.""",
    llm=gemini_llm,
    verbose=True,
)

# 4. Define Tasks for the Sequential Pipeline
research_task = Task(
    description="""Search the web and analyze recent developments and core pillars of {topic}.
    Provide a structured summary highlighting 3 key breakthroughs or concepts, why they matter,
    and their practical implications. Include verified facts or names discovered.""",
    expected_output="A structured factual briefing with 3 key pillars and supporting details.",
    agent=researcher,
)

write_task = Task(
    description="""Using the research analyst's briefing, compose a concise, engaging
    3-paragraph executive overview on {topic}. Maintain technical fidelity while making it
    accessible.""",
    expected_output="A 3-paragraph executive article synthesized directly from the research briefing.",
    agent=writer,
)

review_task = Task(
    description="""Evaluate the writer's article against the research briefing provided.
    Check for:
    1. Factual fidelity (did the writer omit critical pillars or introduce hallucinations?).
    2. Clarity and accessibility for leadership.
    3. Structural adherence (is it cleanly organized in 3 paragraphs?).
    
    You must end your response with exactly one of these two verdict headers:
    APPROVED: [State clearly why the draft is ready for publication]
    or
    REVISION NEEDED: [Provide an itemized list of exact missing details or corrections needed]""",
    expected_output="A detailed critique followed strictly by either APPROVED: ... or REVISION NEEDED: ...",
    agent=reviewer,
)

# 5. Assemble the Crew
crew = Crew(
    agents=[researcher, writer, reviewer],
    tasks=[research_task, write_task, review_task],
    process=Process.sequential,
    verbose=True,
)

if __name__ == "__main__":
    test_topic = "Direct Air Carbon Capture Solid Sorbents vs Liquid Solvents"
    print(f"--- Starting Research Team Crew on Topic: {test_topic} ---\n")
    result = crew.kickoff(inputs={"topic": test_topic})
    print("\n--- Final Output ---\n")
    print(result)
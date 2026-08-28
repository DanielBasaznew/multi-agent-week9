import os
from crewai import Agent, Task, Crew, Process, LLM
from dotenv import load_dotenv

load_dotenv()

# 1. Configure the Gemini LLM
# CrewAI uses standard litellm formatting: "gemini/<model_name>"
gemini_llm = LLM(
    model="gemini/gemini-3.1-flash-lite",  # or gemini/gemini-3.1-flash
    api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.7,
)

# 2. Define Agents with distinct personas and bind the Gemini LLM
researcher = Agent(
    role="Senior Research Analyst",
    goal="Uncover cutting-edge developments and core concepts in {topic}",
    backstory="""You are an expert analyst at a leading tech think tank.
    Your strength is distilling complex technical breakthroughs into crisp,
    fact-based summaries without fluff.""",
    llm=gemini_llm,
    verbose=True,
)

writer = Agent(
    role="Tech Content Strategist",
    goal="Craft compelling, accessible explanations based on technical research",
    backstory="""You are a renowned tech communicator who translates dense
    engineering and research briefings into engaging, easy-to-understand articles
    for an executive audience.""",
    llm=gemini_llm,
    verbose=True,
)

# 3. Define Tasks bound to specific agents
research_task = Task(
    description="""Analyze recent developments and foundational concepts in {topic}.
    Highlight 3 key breakthroughs or fundamental pillars, why they matter,
    and their real-world implications.""",
    expected_output="A structured bullet-point briefing with 3 key points and analysis.",
    agent=researcher,
)

write_task = Task(
    description="""Using the research analyst's briefing, compose a short, 
    engaging 3-paragraph executive overview on {topic}. Make it insightful 
    and accessible while maintaining technical accuracy.""",
    expected_output="A 3-paragraph executive article synthesizing the research findings.",
    agent=writer,
)

# 4. Assemble the Crew with Sequential Orchestration
crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, write_task],
    process=Process.sequential,
    verbose=True,
)

if __name__ == "__main__":
    print("--- Starting Multi-Agent Execution ---\n")
    result = crew.kickoff(inputs={"topic": "Quantum Computing"})
    print("\n--- Final Output ---\n")
    print(result)
from crewai import Task
from typing import Dict, Any
from agents import *  # Import agent definitions

# Task Definitions
article_research_task = Task(
    description=(
        "Research current events in technology and create a summary that covers key innovations, trends, and impacts on society."
    ),
    expected_output=(
        "A detailed research summary that includes: "
        "- Overview of current technological innovations "
        "- Analysis of trends in technology "
        "- Discussion of impacts on society "
        "- Credible sources and references"
    ),
    agent=newspaper_writer
)

article_writing_task = Task(
    description=(
        "Write a comprehensive newspaper article on the latest advancements in AI technology. The article should: "
        "1. Introduce the topic clearly "
        "2. Highlight significant advancements "
        "3. Discuss implications for various industries "
        "4. Conclude with predictions or future trends"
    ),
    expected_output=(
        "A well-structured newspaper article that includes: "
        "- Clear introduction to AI advancements "
        "- In-depth discussion of significant advancements "
        "- Implications for various industries "
        "- Conclusion with future predictions "
        "- Proper citations and references"
    ),
    agent=newspaper_writer
)
import asyncio
from agent_framework.foundry import FoundryAgent
from azure.identity import AzureCliCredential

PROJECT_ENDPOINT = "https://has008-6910-resource.services.ai.azure.com/api/projects/has008-6910"

async def main():
    credential = AzureCliCredential()

    knowledge_agent = FoundryAgent(
        project_endpoint=PROJECT_ENDPOINT,
        agent_name="knowledge-search-agent",
        credential=credential,
    )
    job_agent = FoundryAgent(
        project_endpoint=PROJECT_ENDPOINT,
        agent_name="job-finder-agent",
        credential=credential,
    )

    print("Step 1: knowledge-search-agent decides what to search for (using its memory)...")
    plan = await knowledge_agent.run(
        "A user wants job recommendations. Based on their stored preference, "
        "write ONE short search query (just the query, no extra text) that "
        "job-finder-agent should search for."
    )
    query = plan.text.strip()
    print(f"Delegated query: {query}\n")

    print("Step 2: job-finder-agent actually searches...")
    job_result = await job_agent.run(query)
    print("--- job-finder-agent's answer ---")
    print(job_result.text)

if __name__ == "__main__":
    asyncio.run(main())
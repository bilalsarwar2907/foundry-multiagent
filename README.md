# Foundry Multi-Agent System

A multi-agent system built on Microsoft Foundry: a RAG-grounded orchestrator agent that delegates tasks to a specialist agent via the Microsoft Agent Framework — plus production-grade guardrails, automated evaluations, observability, and supervised fine-tuning layered on top.

Built portal-first (Levels 1–4, 6, 7, 8 required no code at all), dropping into Python only where Foundry has no native equivalent (Level 5, multi-agent orchestration).

## Architecture

```
Orchestrator (knowledge-search-agent)
  - RAG over an uploaded business document (Azure AI Search)
  - Memory (recalls user preferences across turns)
  - get_weather custom OpenAPI tool
  - Guardrails: jailbreak + indirect prompt-injection + content-harm blocking
    ↓ generates a short, specific delegated instruction
Specialist (job-finder-agent)
  - Web search only
  - Guardrails: same policy
    ↓ executes the delegated task independently
Returns result to orchestrator
```

## What's implemented

| Capability | How |
|---|---|
| RAG / Knowledge | Azure AI Search index over an uploaded document, chunking + embeddings (`text-embedding-3-large`), verified via grounded citations |
| Tools | Custom OpenAPI tool (weather lookup) |
| Memory | Cross-turn recall of stated user preferences |
| Multi-agent orchestration | Microsoft Agent Framework (`agent_framework.foundry.FoundryAgent`) — see `connect_agents.py` |
| Guardrails | Jailbreak + indirect prompt-injection + 4 content-harm categories, assigned directly to both agents (not just the underlying models) |
| Evaluations | Automated run against a 6-question ground-truth dataset (`eval_dataset.jsonl`) scored on Relevance / Groundedness / Coherence / Fluency — includes a deliberate hallucination-trap question |
| Observability | Application Insights connected via the project's Monitor tab — live per-request duration, token count, and cost |
| Fine-tuning | Supervised fine-tuning on an 11-example dataset (`finetune_dataset.jsonl`) to lock a strict `Answer: / Source:` output format into a custom model deployment |

## Key engineering findings

**Two incompatible agent architectures exist side by side in Foundry.** The "classic" Assistants-style API (`azure-ai-agents`, `ConnectedAgentTool`) and the current Prompt Agents architecture (`agent_framework.foundry.FoundryAgent`) look similar in the portal but use entirely different backing stores. `AgentsClient.list_agents()` against a Prompt Agents project returns an empty list with no error — it's silently talking to the wrong store. Confirmed by introspecting the installed package directly (`dir()`/`help()`) rather than trusting docs, which disagreed across sources for this preview feature.

**A guardrail applied to a model deployment doesn't protect every agent using that model.** An agent's own (default/empty) guardrail assignment silently overrides the model-level one. The fix is assigning the guardrail directly to the agent, not just the model — easy to miss since the "Select agents" list sits above the "Select models" list in the portal wizard.

**A plausible-sounding model refusal and a real guardrail block look almost identical in plain text.** The only reliable way to tell them apart is the response trace's Metadata tab: a real block shows `total_tokens: 0` and status `"incomplete"` (rejected before the model ever ran); a normal trained refusal shows a full token count and a completed response.

**A perfect evaluation score isn't proof by itself.** The dataset's one deliberate trap question — asking for a fact that doesn't exist in the source document — is what actually exercises the Groundedness metric. A 100% summary score only means something once you've opened that row and confirmed the agent said "not stated" instead of fabricating a plausible number.

**The Playground doesn't inherit a fine-tune's training system prompt**, and a live Web search tool left enabled can fully mask trained behavior. A fine-tuned model that looks completely untrained in testing is often a test-harness configuration problem (default placeholder instructions, a tool the training never used), not a failed fine-tune — check the harness before doubting the weights.

## Stack

Azure AI Foundry (Prompt Agents, Guardrails, Evaluations, Fine-tuning, Application Insights) · Microsoft Agent Framework · Azure AI Search · Python · `agent-framework` / `agent-framework-foundry` / `azure-identity`

## Setup

```bash
python3 -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
az login
python connect_agents.py
```

Requires an existing Foundry project with the two agents (`knowledge-search-agent`, `job-finder-agent`) already built in the portal, and `PROJECT_ENDPOINT` set to your own project's endpoint in `connect_agents.py`.

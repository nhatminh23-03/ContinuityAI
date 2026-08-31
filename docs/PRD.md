**ContinuityAI**

**Engineering Knowledge Resilience**

**Product Requirements Document (PRD)**

Hackathon Track: Wildcard Challenge - Build Intelligent Systems for the Future of Work

Version 1.0 \| August 11, 2026 \| MVP Scope Frozen

| **One-line product promise:** ContinuityAI turns fragmented engineering evidence into an evidence-backed knowledge graph so engineering managers can see which critical capabilities become exposed when expertise disappears - and prepare targeted knowledge-transfer work before the gap becomes an operational problem. |
|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

# Document Control

| **Field**                        | **Value**                                                                                               |
|----------------------------------|---------------------------------------------------------------------------------------------------------|
| **Product**                      | ContinuityAI                                                                                            |
| **Category**                     | Engineering Knowledge Resilience                                                                        |
| **Primary user**                 | Engineering Manager                                                                                     |
| **Challenge track**              | Wildcard Challenge - Build Intelligent Systems for the Future of Work                                   |
| **Primary technical innovation** | AI-generated, evidence-backed Engineering Knowledge Graph                                               |
| **Headline capability**          | Counterfactual expertise-unavailability simulation                                                      |
| **MVP architecture**             | Next.js/React frontend + FastAPI/Python backend + lightweight typed graph persistence                   |
| **Data strategy**                | Real public GitHub evidence + synthetic private enterprise artifacts generated from hidden ground truth |
| **Decision state**               | Core product scope frozen after structured challenge review                                             |
| **Source basis**                 | User-provided AI Builders Challenge with IBM Bob / BeMyApp PDF, especially pages 6-8                    |

# Contents

1\. Executive Summary

2\. Challenge Alignment

3\. Product Vision and Positioning

4\. Problem Definition

5\. Goals, Success Outcomes, and Non-Goals

6\. Primary Persona and Jobs-to-be-Done

7\. Product Principles

8\. Core Concepts and Terminology

9\. Primary User Scenarios

10\. MVP Scope and Information Architecture

11\. Detailed UX Requirements

12\. Functional Requirements

13\. Engineering Knowledge Graph Specification

14\. Data Strategy and Synthetic Organization Model

15\. AI Semantic Extraction Contract

16\. Evidence, Readiness, Freshness, and Confidence

17\. Continuity Risk Model

18\. Counterfactual Simulation Engine

19\. Backup Candidate Recommendation

20\. Knowledge-Transfer Plan Generation

21\. Human Challenge / Correct / Learn Workflow

22\. Responsible AI, Privacy, and Safety Boundaries

23\. System Architecture and Technical Stack

24\. API Contract Outline

25\. Evaluation and Validation Plan

26\. Acceptance Criteria and Definition of Done

27\. Three-Minute Hackathon Demo Script

28\. IBM Bob Development Plan

29\. Implementation Sequence

30\. Risks and Mitigations

31\. Post-MVP Roadmap

Appendix A. NovaPay Demo Model

Appendix B. Example Structured Objects

Appendix C. Final Scope Freeze Checklist

# 1. Executive Summary

Engineering organizations routinely eliminate infrastructure single points of failure while leaving a less visible failure mode untreated: critical technical knowledge concentrated in one person. A service may be redundant across regions, but the ability to recover it, deploy it, rotate credentials, diagnose a failure, or operate a legacy component may still depend on one engineer.

ContinuityAI is an Engineering Knowledge Resilience platform for engineering managers. It uses AI to interpret engineering artifacts such as pull requests, issues, incident records, runbooks, and technical documentation, and converts them into a typed, evidence-backed knowledge graph connecting systems, components, capabilities, engineers, and supporting evidence. Deterministic rules then classify demonstrated readiness, evaluate knowledge redundancy, calculate continuity exposure, and run counterfactual simulations.

The MVP is centered on one decision loop: an engineering manager identifies a risky system, simulates an engineer becoming unavailable, sees exactly which technical capabilities lose adequate coverage, inspects the evidence behind the conclusion, compares technically suitable backup candidates, and generates a targeted knowledge-transfer plan that the manager can review and approve.

The product does not claim to know what is inside an employee's head. It measures demonstrated capability from available work evidence. It does not produce employee-worth, productivity, bonus, promotion, or layoff scores. Systems and capabilities carry continuity risk; people appear as evidence-backed coverage relationships.

| **Core thesis:** Engineering tools record work. ContinuityAI reconstructs demonstrated technical capability and asks a different question: can the organization still operate a critical system when key expertise becomes unavailable? |
|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

# 2. Challenge Alignment

The user-provided challenge brief defines the Wildcard Challenge as “Build Intelligent Systems for the Future of Work” and calls for AI that helps individuals, teams, and organizations plan, coordinate, decide, and execute work more effectively. It lists workflow automation, AI co-workers, project planning assistants, decision intelligence, operations/productivity, and business-process orchestration as example directions. The brief also requires a working prototype or proof of concept using IBM Bob as the primary development tool, a public GitHub repository with the problem/solution/AI architecture/theme/Bob usage documented, and a public demo video no longer than three minutes. Judging criteria are Technical Execution, Innovation, Feasibility, Challenge Fit, and Real-World Impact.

| **Challenge requirement / criterion** | **ContinuityAI response**                                                                 |
|---------------------------------------|-------------------------------------------------------------------------------------------|
| Future-of-work decision support       | Turns fragmented engineering evidence into actionable knowledge-continuity decisions.     |
| Planning                              | Generates targeted knowledge-transfer plans for specific capability gaps.                 |
| Coordination                          | Identifies primary/backup coverage and prepares proposed work for manager approval.       |
| Decision-making                       | Counterfactual simulator shows capability loss when expertise becomes unavailable.        |
| Execution                             | Produces structured mitigation tasks; manager approves before execution.                  |
| Technical execution                   | AI extraction + typed knowledge graph + deterministic readiness/risk engine + simulation. |
| Innovation                            | Evidence-backed engineering knowledge graph, not contribution counting.                   |
| Feasibility                           | Small reusable MVP; no live enterprise integrations required.                             |
| Real-world impact                     | Targets operational disruption caused by hidden single-expert dependencies.               |
| IBM Bob                               | Used across planning, implementation, testing, debugging, and documentation.              |

# 3. Product Vision and Positioning

## 3.1 Vision

Make the knowledge required to operate critical software systems visible, inspectable, and resilient before absence, departure, team change, or incident exposes hidden dependencies.

## 3.2 Category

Engineering Knowledge Resilience. The observability analogy may be used in the pitch (“observability for the knowledge behind critical systems”), but the product is not positioned as employee observability or surveillance.

## 3.3 Primary value proposition

| **Headline:** ContinuityAI shows engineering managers which critical technical capabilities become exposed when key expertise becomes unavailable - and what they can do before that exposure becomes an operational problem. |
|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

## 3.4 Differentiation

| **Existing tool**     | **What it knows**                              | **What ContinuityAI adds**                                                                 |
|-----------------------|------------------------------------------------|--------------------------------------------------------------------------------------------|
| GitHub                | Commits, PRs, reviews, repository contributors | Semantic interpretation of what capabilities the work demonstrates.                        |
| CODEOWNERS            | Declared code ownership                        | Comparison of declared ownership vs demonstrated operational expertise.                    |
| Jira / issue tracker  | Task ownership and completion                  | Capability evidence and cross-source triangulation.                                        |
| Incident platform     | Who participated in incidents                  | Independent vs assisted recovery evidence; readiness implications.                         |
| Confluence / runbooks | Documented procedures and authors              | Documentation coverage and evidence of knowledge transfer.                                 |
| Traditional BI        | Counts and trends                              | Counterfactual continuity reasoning: what loses adequate coverage if expertise disappears? |

# 4. Problem Definition

## 4.1 Root problem

Engineering managers lack an evidence-based, continuously maintainable way to identify critical technical knowledge that is concentrated in too few people before an absence, departure, transfer, or production incident exposes the gap.

## 4.2 Why current approaches fail

- Static ownership is not the same as demonstrated operational capability.

- Activity volume is not the same as expertise; 200 trivial commits can be less meaningful than two independent P1 recoveries.

- Knowledge evidence is fragmented across repositories, tickets, incidents, and documentation.

- Managers rely heavily on memory and informal reputation, which becomes unreliable as teams and systems change.

- Documentation can exist but be incomplete, stale, or insufficient to establish that another engineer can independently perform the work.

- Knowledge resilience drifts as people move teams, architecture changes, and evidence becomes stale.

## 4.3 Failure modes the product addresses

| **Trigger**                         | **Hidden condition exposed**                          | **ContinuityAI role**                                        |
|-------------------------------------|-------------------------------------------------------|--------------------------------------------------------------|
| Unexpected resignation / retirement | Critical capabilities had only one demonstrated owner | Identify impacted capability coverage and candidate backups. |
| Vacation / illness during incident  | Team cannot independently recover a critical service  | Expose weak recovery readiness before the event.             |
| Team reassignment / reorganization  | A transfer creates new single-expert dependencies     | Simulate impact before making the change.                    |
| Architecture change                 | Previously current expertise becomes stale            | Knowledge Drift highlights degraded freshness/coverage.      |
| Incorrect declared ownership        | CODEOWNERS does not match operational reality         | Surface declared-vs-demonstrated mismatch.                   |

# 5. Goals, Success Outcomes, and Non-Goals

## 5.1 MVP goals

- Construct a typed engineering knowledge graph from multiple engineering artifact types.

- Map evidence to System → Component → Capability → Engineer relationships with source provenance.

- Derive readiness using deterministic rules over evidence strength, diversity, repetition, and freshness.

- Show a platform hierarchy with system-level Continuity Risk Index, critical coverage gaps, and Knowledge Drift indicators.

- Run an engineer-unavailability simulation that identifies exact capability coverage lost, degraded, or preserved.

- Provide provenance-first explanations for every important conclusion.

- Compare 2-3 technical backup candidates using evidence-backed capability overlap.

- Generate a candidate-specific knowledge-transfer plan and allow manager review/approval.

- Demonstrate correction of an assessment through linked evidence, attestation, or capability reclassification.

- Validate the prototype against a hidden-ground-truth synthetic organization model.

## 5.2 Success outcomes

| **Outcome**                                | **MVP success signal**                                                                         |
|--------------------------------------------|------------------------------------------------------------------------------------------------|
| Manager understands platform risk quickly | Dashboard makes highest-risk platform/system and critical-gap count obvious within 10 seconds. |
| AI conclusions are trustworthy             | Every user-visible expertise/readiness claim can open supporting evidence.                     |
| Simulation is specific                     | Result lists affected capabilities, not vague “Alex is important” statements.                  |
| Recommendation is decision support         | Top candidates show strengths, gaps, evidence, and limitations; manager chooses.               |
| Demo proves system logic                   | NovaPay scenario can be reproduced from seeded data and hidden-ground-truth evaluation.        |

## 5.3 Non-goals

- Employee productivity scoring, worth scoring, bonus calculation, promotion recommendations, or layoff recommendations.

- Prediction that a system outage will occur or a probabilistic “chance of failure.”

- Live Jira, Confluence, Slack, or enterprise SSO integration in the MVP.

- Autonomous staffing or task assignment without manager approval.

- Continuous background monitoring in the hackathon MVP.

- Production-grade graph database deployment; the MVP uses a typed graph abstraction over lightweight persistence.

- Perfect representation of tacit knowledge that has no available evidence.

- Full performance-review workflow; contribution insights remain secondary and evidence-only.

# 6. Primary Persona and Jobs-to-be-Done

## 6.1 Primary persona - Sarah, Engineering Manager

| **Attribute**          | **Definition**                                                                                                      |
|------------------------|---------------------------------------------------------------------------------------------------------------------|
| **Role**               | Engineering Manager, Payments Platform                                                                              |
| **Team**               | 8 engineers                                                                                                         |
| **Systems**            | Payment Gateway, Refund Engine, Billing Integration                                                                 |
| **Responsibilities**   | Reliability, delivery, incident readiness, team development, technical ownership                                    |
| **Current tools**      | GitHub, issue tracker, incident system, runbooks/docs, service ownership metadata                                   |
| **Current pain**       | Knows who is senior/visible, but cannot prove which specific operational capabilities depend uniquely on one person |
| **Trigger scenarios**  | Upcoming leave, resignation, team transfer, incident review, quarterly resilience review                            |
| **Decision authority** | Can prioritize cross-training and approve proposed mitigation work                                                  |

## 6.2 Jobs-to-be-done

- When I look across my platform, show me which systems and capabilities have dangerous knowledge concentration so I know where to investigate first.

- When a key engineer may become unavailable, show me exactly which capabilities lose adequate coverage rather than telling me the person is “important.”

- When you claim a capability is exposed, show me the evidence and what evidence is missing so I can trust or challenge the assessment.

- When a gap exists, show me the strongest technical backup candidates and the trade-offs rather than making a staffing decision for me.

- When I choose a backup candidate, turn the gap into a specific knowledge-transfer plan I can approve.

- When the organization changes, show me what knowledge resilience changed and which critical gaps are new, resolved, or becoming stale.

# 7. Product Principles

| **Principle**                                   | **Requirement**                                                                                                |
|-------------------------------------------------|----------------------------------------------------------------------------------------------------------------|
| **System-first, not employee-first**            | Risk belongs to systems/capabilities. People are coverage relationships, not scored assets.                    |
| **Evidence-backed AI**                          | Every expertise claim is traceable to source artifacts; unsupported certainty is prohibited.                   |
| **Artifact, not activity**                      | Interpret what work demonstrates; do not equate activity volume with expertise.                                |
| **AI extracts; deterministic logic scores**     | LLM performs semantic extraction and explanation; readiness/risk/simulation are rule-based.                    |
| **Risk is not confidence**                      | Continuity Risk Index communicates exposure; Evidence Confidence communicates strength of available evidence.  |
| **Uncertainty is valid**                        | Insufficient Evidence and Human Review Recommended are legitimate outputs.                                     |
| **Human-in-the-loop**                           | Managers confirm business criticality, can challenge assessments, choose backup candidates, and approve plans. |
| **Replace capability coverage, not people**     | Mitigation targets the few exposed capabilities, not cloning one engineer.                                     |
| **Privacy by boundary**                         | No private DMs, working hours, keystrokes, location, personality, or sentiment analysis.                       |
| **Decision support, not employment automation** | No autonomous promotion, bonus, layoff, or staffing decisions.                                                 |

# 8. Core Concepts and Terminology

| **Term**                       | **Definition**                                                                                                         |
|--------------------------------|------------------------------------------------------------------------------------------------------------------------|
| **Platform**                   | Top-level grouping of systems, e.g., Payments Platform. Formerly also called Portfolio; Platform is the single term.                                                                |
| **System / Service**           | Continuously operated technical product/service, e.g., Payment Gateway.                                                |
| **Component**                  | Logical subsystem within a system, e.g., Gateway Integration.                                                          |
| **Capability**                 | Operational or technical ability required to build/operate a component, e.g., Incident Recovery.                       |
| **Evidence**                   | Source artifact supporting a capability claim, e.g., incident, PR, runbook.                                            |
| **Readiness**                  | Evidence-derived classification: NONE, EXPOSED, ASSISTED, PRACTICED, VALIDATED.                                        |
| **Evidence Strength**          | Weak / Moderate / Strong based on what the artifact demonstrates.                                                      |
| **Evidence Freshness**         | Fresh / Aging / Stale using age + component change.                                                         |
| **Critical Coverage Gap**      | A business/operationally critical capability without adequate practiced/validated backup coverage.                     |
| **Continuity Risk Index**      | 0-100 severity index derived from transparent rules; not a failure probability.                                        |
| **Evidence Confidence**        | High/Medium/Low indication of how much trustworthy evidence supports the assessment.                                   |
| **Knowledge Drift**            | Change in knowledge resilience over time: new risk, resolved risk, or staleness.                                       |
| **Declared Ownership**         | Formal ownership source such as CODEOWNERS or service catalog.                                                         |
| **Demonstrated Coverage**      | Capability relationship inferred from evidence and readiness rules.                                                    |
| **Technical Backup Candidate** | Engineer with adjacent demonstrated capabilities who may be suitable for cross-training; not an autonomous assignment. |

# 9. Primary User Scenarios

| **Scenario**                             | **Expected product behavior**                                                                    |
|------------------------------------------|--------------------------------------------------------------------------------------------------|
| S1 - Proactive discovery                 | Sarah opens Dashboard and sees Payment Gateway carries two capabilities with no resilient backup. |
| S2 - Planned unavailability              | Alex will be unavailable; Sarah runs the counterfactual simulator.                               |
| S3 - Incident readiness                  | Sarah checks whether Payment Incident Recovery remains covered without Alex.                     |
| S4 - Team change                         | Sarah simulates a reassignment before moving an engineer.                                        |
| S5 - Evidence challenge                  | Sarah disagrees that Jordan is only EXPOSED and links missing incident evidence.                 |
| S6 - Mitigation planning                 | Sarah selects Maria as the preferred technical backup and generates a tailored plan.             |
| S7 - Knowledge drift                     | A platform shows a new critical gap after a simulated team change or stale evidence event.       |
| S8 - Contribution visibility (secondary) | Clicking a person shows evidence-backed technical contributions, not a performance score.        |

# 10. MVP Scope and Information Architecture

| **Scope freeze:** Build a small but reusable MVP platform across 2-3 platforms and 5-7 systems. The full workflow must genuinely work for multiple engineers/systems, not only a scripted Alex scenario. |
|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

## 10.1 Primary navigation

```text
ContinuityAI

├── Dashboard

├── Systems

├── Knowledge Graph

├── Simulations

├── Plans

└── People (lightweight)
```

## 10.2 Required end-to-end journey

```text
Portfolio Dashboard

↓

System Detail

↓

Contextual Knowledge Graph + Evidence

↓

Simulate Engineer Unavailability

↓

Capability Loss Analysis + Risk Recalculation

↓

Compare Technical Backup Candidates

↓

Generate Personalized Knowledge-Transfer Plan

↓

Manager Reviews / Approves
```

## 10.3 MVP vs deferred

| **Area**   | **MVP**                                          | **Deferred**                                         |
|------------|--------------------------------------------------|------------------------------------------------------|
| Data       | Public GitHub + synthetic incidents/tickets/docs | Live Jira/Confluence/Slack/ServiceNow integrations   |
| Graph      | Typed contextual graph                           | Enterprise-scale graph explorer / dedicated graph DB |
| Monitoring | Seeded Knowledge Drift indicators                | Continuous scheduled monitoring                      |
| People     | Evidence-only profile drawer                     | Performance review and recognition workflow          |
| Actions    | Prepared plan/tasks + manager approval           | Autonomous task assignment / calendar scheduling     |
| Validation | Hidden-ground-truth synthetic evaluation         | Real enterprise pilot / longitudinal validation      |

# 11. Detailed UX Requirements

## 11.1 Dashboard - Platform Risk Overview

“Portfolio Dashboard” may remain as a screen title; `Platform` is the domain term and the identifier prefix.

Purpose: within 10 seconds, Sarah must understand which platform/system deserves attention, how many critical coverage gaps exist, and whether risk is drifting.

| **Element**      | **Requirement**                                                                                           |
|------------------|-----------------------------------------------------------------------------------------------------------|
| Top summary      | Total critical coverage gaps and a knowledge-drift indicator per platform. No single “employee health” score. |
| Platform rows    | Platform name, highest system Continuity Risk Index, critical systems, critical gaps, drift indicator. No aggregated platform risk score is calculated. |
| System rows      | System name, business criticality, Continuity Risk Index, critical gap count, Evidence Confidence, drift. |
| Sort/filter      | Default sort by risk descending; filter by platform and risk class.                                      |
| Primary action   | Click system to open System Detail.                                                                       |
| Secondary action | Simulate unavailability from any system row or detail page.                                               |

| **Platform / System** | **Criticality** | **Risk** | **Critical Gaps** | **Drift**   |
|-----------------------|-----------------|----------|-------------------|-------------|
| Payments Platform     | \-              | Highest system 74 | 1        | +1 new risk |
| Payment Gateway       | CRITICAL        | 74 / 100 HIGH     | 0        | New risk    |
| Refund Engine         | HIGH            | 72 / 100 | 1                 | Stable      |
| Billing Integration   | HIGH            | 51 / 100 | 0                 | Improving   |
| Identity Platform     | \-              | Highest system 68 | 1        | Stable      |
| Authentication        | CRITICAL        | 68 / 100 | 1                 | Stable      |

## 11.2 System Detail

- Show business criticality and whether it was human-confirmed or AI-suggested.

- Show Continuity Risk Index, risk class, Evidence Confidence, and “Why?” link.

- List components and capabilities with coverage state: Covered, Degraded, Critical Gap, Insufficient Evidence.

- Show declared owner(s) and highlighted mismatch if demonstrated operational expertise differs.

- Offer “Simulate Engineer Unavailability.”

## 11.3 Contextual Knowledge Graph

The MVP graph is contextual, not an enterprise-wide hairball. Default view shows only the selected system/component/capability neighborhood and relevant engineers/evidence.

```text
PAYMENT GATEWAY

↓ HAS_COMPONENT

GATEWAY INTEGRATION

↓ REQUIRES_CAPABILITY

INCIDENT RECOVERY

├── DEMONSTRATED_BY → Alex (VALIDATED)

├── DEMONSTRATED_BY → Maria (ASSISTED)

└── DEMONSTRATED_BY → Jordan (EXPOSED)



Alex → SUPPORTED_BY → INC-184 / INC-221 / DOC-17
```

- Node click opens detail drawer.

- Capability node shows all engineers and readiness.

- Engineer-capability edge shows Evidence Confidence and freshness.

- Evidence node opens provenance card with source, date, excerpt/summary, and evidence role.

- Simulation visually dims/removes the selected engineer coverage and highlights gaps.

## 11.4 Provenance / Why Drawer

| **Section**                  | **Content**                                                           |
|------------------------------|-----------------------------------------------------------------------|
| Claim                        | Example: “Incident Recovery becomes a Critical Gap without Alex.”     |
| Coverage                     | Alex VALIDATED; Maria ASSISTED; Jordan EXPOSED.                       |
| Supporting evidence          | Strong/moderate/weak evidence cards with source ID and artifact type. |
| Missing evidence             | Example: “No qualifying independent P1 recovery found for Jordan.”    |
| Counter/conflicting evidence | Any evidence that weakens or contradicts the conclusion.              |
| Freshness                    | Latest qualifying evidence and freshness state.                       |
| Declared vs demonstrated     | Show CODEOWNERS/service owner alongside demonstrated coverage.        |
| Confidence                   | High/Medium/Low with explanation; never a fake “94% certainty.”       |
| Action                       | Challenge Assessment.                                                 |

## 11.5 Simulation Screen

- Engineer selector defaults to AI-suggested high-impact scenarios but allows any engineer in scope.

- MVP scenario is “Unavailable” and means the selected engineer’s demonstrated capability coverage is temporarily excluded from continuity coverage calculations.

- Output groups capabilities into Critical Gap, Degraded, Preserved, and Insufficient Evidence.

- Show before/after system Continuity Risk Index and exact rule changes.

- Explicit disclaimer: simulation identifies coverage loss; it does not predict an outage.

## 11.6 Candidate Comparison

- Show up to 3 technical candidates.

- Use High/Medium/Low technical overlap, not percentage match.

- For each candidate show relevant demonstrated strengths, missing capability evidence, freshness, and evidence sources.

- Show “Not considered: workload, career goals, leave, team priorities, staffing constraints.”

- Manager selects a candidate or chooses another engineer; AI does not autonomously assign.

## 11.7 Mitigation Plan

- Generate a capability-specific knowledge-transfer plan for the selected candidate.

- Plan contains 3-5 structured actions, owner suggestion, mentor suggestion, acceptance criteria, and linked source material.

- Actions should progress from Understand → Observe/Assist → Practice → Recovery Exercise → Documentation Update when applicable.

- Manager can edit the plan before approval.

- Approval stores the plan as Approved in the MVP; no live Jira write is required.

# 12. Functional Requirements

| **ID** | **Feature**              | **Requirement**                                                                                                                                  |
|--------|--------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------|
| FR-001 | Platform hierarchy       | System shall represent Platform → System → Component → Capability.                                                                              |
| FR-002 | Dashboard risk list      | System shall list all seeded platforms/systems with risk index/class, critical gaps, evidence confidence, and drift.                            |
| FR-003 | Artifact ingestion       | System shall ingest normalized GitHub/public evidence and synthetic incident/ticket/document records.                                            |
| FR-004 | Semantic extraction      | AI shall convert each artifact into structured evidence records using the schema in Section 15.                                                  |
| FR-005 | Taxonomy discovery       | AI shall propose components/capabilities using existing metadata first and flag low-confidence concepts for review.                              |
| FR-006 | Evidence provenance      | Every extracted evidence record shall retain source ID, artifact type, source date, source URI/reference if available, and extraction rationale. |
| FR-007 | Readiness                | Deterministic engine shall classify engineer-capability readiness as NONE / EXPOSED / ASSISTED / PRACTICED / VALIDATED.                          |
| FR-008 | Freshness                | System shall classify evidence freshness using artifact age and component-change signal.                                                         |
| FR-009 | Confidence               | System shall classify Evidence Confidence High/Medium/Low separately from continuity risk.                                                       |
| FR-010 | Business criticality     | AI may suggest system criticality; a human-confirmed value is authoritative.                                                                     |
| FR-011 | Operational criticality  | System shall derive or seed capability-level operational criticality and show supporting rationale.                                              |
| FR-012 | Risk rules               | Rule engine shall determine Low/Moderate/High/Critical continuity exposure.                                                                      |
| FR-013 | Risk index               | System shall map rule outcome to a transparent 0-100 Continuity Risk Index and display contributing rule factors.                                |
| FR-014 | Simulation               | System shall simulate engineer unavailability by excluding that engineer’s capability coverage and recomputing exposure.                         |
| FR-015 | Impact detail            | Simulation shall list capabilities that become Critical Gap, Degraded, or remain Covered.                                                        |
| FR-016 | Candidate search         | System shall identify up to 3 technically adjacent candidate backups using graph evidence.                                                       |
| FR-017 | Candidate explanation    | AI shall explain why each candidate is suitable/unsuitable using only evidence-backed graph facts.                                               |
| FR-018 | Plan generation          | AI shall create a candidate-specific mitigation plan with 3-5 actions and acceptance criteria.                                                   |
| FR-019 | Human approval           | Manager shall be able to edit and approve a generated mitigation plan. Edits are submitted with the approval request.                                                                      |
| FR-020 | Challenge assessment     | Manager shall be able to link evidence, add manager attestation, or correct capability mapping and trigger recomputation.                        |
| FR-021 | Declared-vs-demonstrated | System shall flag when declared ownership materially differs from demonstrated operational coverage.                                             |
| FR-022 | People insight drawer    | Clicking a person shall show evidence-backed capabilities/contributions without an employee value/performance score.                             |
| FR-023 | Knowledge Drift          | Dashboard shall show seeded/new/resolved/stale continuity changes for demo data.                                                                 |
| FR-024 | Auditability             | All user-visible risk/readiness/recommendation claims shall be traceable to rule output and source evidence.                                     |
| FR-025 | Uncertainty              | System shall support Insufficient Evidence and Conflicting Evidence states instead of forcing a classification.                                  |

# 13. Engineering Knowledge Graph Specification

## 13.1 Node types

| **Node type** | **Required properties**                                       | **Example**         |
|---------------|---------------------------------------------------------------|---------------------|
| Platform      | id, name                                                      | platform_payments   |
| System        | id, name, business_criticality, criticality_source            | system_payment_gateway |
| Component     | id, system_id, name                                           | component_gateway_integration |
| Capability    | id, component_id, name, operational_criticality               | cap_incident_recovery |
| Engineer      | id, display_name, role, team                                  | eng_alex_chen        |
| Evidence      | id, artifact_type, source_id, date, strength, role, freshness | evidence_inc_184     |

## 13.2 Edge types

| **Edge**            | **From → To**                               | **Properties**                                          |
|---------------------|---------------------------------------------|---------------------------------------------------------|
| HAS_SYSTEM          | Platform → System                           | none                                                    |
| HAS_COMPONENT       | System → Component                          | none                                                    |
| REQUIRES_CAPABILITY | Component → Capability                      | operational_criticality                                 |
| DEMONSTRATES        | Engineer → Capability                       | readiness, confidence, freshness, first_seen, last_seen |
| SUPPORTED_BY        | Engineer-Capability relationship → Evidence | evidence_role, extraction_confidence                    |
| DECLARED_OWNER      | Engineer → System                           | source, last_updated                                    |

## 13.3 Persistence

The MVP shall use a typed graph abstraction independent of the underlying database. Lightweight persistence may use normalized relational tables (nodes, edges, evidence, artifacts) or equivalent SQLite structures. The graph semantics must exist in code so simulation/traversal do not depend on a specific graph database product.

## 13.4 Graph invariants

- Every Capability belongs to exactly one Component in the MVP.

- Every Component belongs to exactly one System in the MVP.

- Every Evidence record must link to an original artifact/source reference.

- No DEMONSTRATES edge may exist without at least one supporting Evidence record or explicit Manager Attestation.

- Readiness is recomputed from evidence; users cannot directly edit readiness values.

- Risk belongs to Capability/System/Platform nodes, never to Engineer nodes.

# 14. Data Strategy and Synthetic Organization Model

## 14.1 Hybrid prototype data

| **Source**                   | **MVP data**                                                                                                             | **Purpose**                                                                  |
|------------------------------|--------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| Public GitHub                | Real commits, PRs/issues/contributor activity from a selected open-source repository or locally normalized public export | Realistic engineering activity patterns and source ingestion credibility.    |
| Incident records             | Synthetic                                                                                                                | Private operational evidence unavailable publicly; tests recovery expertise. |
| Jira-style tickets           | Synthetic                                                                                                                | Task/component ownership and assisted/independent work context.              |
| Runbooks/docs                | Synthetic Markdown/JSON                                                                                                  | Documentation coverage and authorship.                                       |
| Employees/team/org           | Synthetic NovaPay model                                                                                                  | Controlled persona/system relationships.                                     |
| CODEOWNERS/service ownership | Synthetic or adapted metadata                                                                                            | Declared-vs-demonstrated comparison.                                         |

## 14.2 Hidden-ground-truth generator

A hidden model defines the true simulated expertise distribution. ContinuityAI never receives readiness labels from this model. A generator emits artifacts probabilistically based on the hidden state, including occasional noise, incidental exposure, and non-expert activity. Evaluation compares the inferred graph against the hidden model.

```text
HIDDEN (not provided to application)

Payment Gateway → Incident Recovery

Alex = VALIDATED

Maria = ASSISTED

Jordan = EXPOSED



GENERATOR OUTPUT

INC-184: Alex independently restores routing

INC-221: Alex independently restores authentication

PR-442: Alex implements recovery logic

INC-230: Maria assists recovery

PR-391: Jordan reviews failover logic
```

## 14.3 NovaPay target scale

| **Entity**              | **Target count**             |
|-------------------------|------------------------------|
| Platforms               | 2-3                          |
| Systems                 | 5-7                          |
| Components              | 12-20                        |
| Capabilities            | 25-40                        |
| Engineers               | 8-12                         |
| Artifacts               | 500-2,000 normalized records |
| Critical demo incidents | 10-20                        |
| Documents/runbooks      | 15-30                        |

# 15. AI Semantic Extraction Contract

## 15.1 Boundary

| **Critical architecture rule:** AI interprets what an artifact demonstrates. AI does NOT directly assign final engineer readiness, Continuity Risk Index, or employee importance. |
|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

## 15.2 Input object

```text
ArtifactInput {

artifact_id: string

artifact_type: "pull_request" | "issue" | "incident" | "document" | "code_review" | "approved_collaboration"

title: string

body: string

participants: [{ engineer_id, role_in_artifact }]

created_at: datetime

updated_at: datetime

repository?: string

file_paths?: string[]

declared_system?: string

metadata?: object

}
```

## 15.3 Required extraction output

```text
EvidenceExtraction {

artifact_id: string

system: { name, source: "explicit" | "metadata" | "inferred" }

component: { name, confidence_band: "high" | "medium" | "low" }

capabilities: [{

name: string,

engineer_id: string,

evidence_role: "EXPOSURE" | "CONTRIBUTION" | "ASSISTED_EXECUTION" | "INDEPENDENT_EXECUTION" | "KNOWLEDGE_CAPTURE",

evidence_strength: "WEAK" | "MODERATE" | "STRONG",

rationale: string,

source_excerpt_or_summary: string

}]

possible_taxonomy_duplicates?: string[]

ambiguity?: string[]

}
```

## 15.4 Forbidden AI outputs

- “Alex is a validated expert” from a single artifact.

- “Jordan cannot recover Payments” when evidence is absent.

- Risk probability such as “93% chance of outage.”

- Employee productivity, worth, promotion, bonus, or layoff recommendation.

- Uncited capability claims without artifact provenance.

- Invented systems/capabilities when evidence is insufficient; low-confidence/unknown is required.

## 15.5 Taxonomy discovery order of trust

1\. Explicit company/service metadata and repository structure.

2\. CODEOWNERS/service catalog/architecture documentation.

3\. Repeated cross-artifact semantic evidence.

4\. AI inference with confidence band.

5\. Human confirmation for ambiguous or low-confidence concepts.

# 16. Evidence, Readiness, Freshness, and Confidence

## 16.1 Evidence strength

| **Strength** | **Examples**                                                                                                                 | **Interpretation**                                        |
|--------------|------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------|
| WEAK         | Reviewed PR, commented on issue, participated in discussion, read doc                                                        | Exposure; does not establish independent execution.       |
| MODERATE     | Modified related code, completed related ticket, co-authored doc, assisted incident                                          | Hands-on participation with some dependency/support.      |
| STRONG       | Independent production recovery, implemented capability, led deployment, designed architecture, authored operational runbook | Direct evidence of execution/ownership of the capability. |

## 16.2 Readiness states - prototype heuristics

| **State** | **Minimum evidence pattern (MVP heuristic)**                                                                               | **Meaning**                                                                     |
|-----------|----------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| NONE      | No qualifying evidence                                                                                                     | No evidence-based coverage claim.                                               |
| EXPOSED   | At least 1 relevant weak/moderate item OR 2 weak items                                                                     | Aware / interacted; no evidence of meaningful independent work.                 |
| ASSISTED  | At least 1 moderate/strong assisted item + 1 supporting item                                                               | Participated meaningfully but evidence suggests guidance/shared execution.      |
| PRACTICED | At least 1 recent strong item performed without significant support + 1 supporting item | Performed hands-on without significant support, but limited to controlled or lower-risk contexts, or lacking the repetition, diversity, or recency required for VALIDATED. |
| VALIDATED | At least 2 strong independent items across 2+ artifact types, with at least 1 FRESH; no unresolved major conflict | Repeated independent demonstration in multiple contexts.                        |

These thresholds are prototype heuristics for transparent demo logic, not scientifically validated competency standards. Production use would require customer calibration and empirical validation.

## 16.3 Evidence freshness

| **Freshness** | **Default rule**                                                                 |
|---------------|----------------------------------------------------------------------------------|
| FRESH         | Evidence ≤18 months old, OR ≤12 months with low component change (\<40%).        |
| AGING         | 18-36 months old OR substantial component change (40-70%).                       |
| STALE         | \>36 months old OR component change \>70% OR known major architecture migration. |

Component-change percentage is a simple prototype signal derived from normalized code/change events after the evidence date. It is not intended as a universal software-change metric.

## 16.4 Evidence Confidence

| **Confidence** | **Heuristic**                                                                                                            |
|----------------|--------------------------------------------------------------------------------------------------------------------------|
| HIGH           | 3+ qualifying evidence items, 2+ artifact types, at least one FRESH strong item, no unresolved major conflicts. |
| MEDIUM         | 2+ items or one strong item with limited diversity/freshness; no severe contradiction.                                   |
| LOW            | Sparse, stale, single-source, or materially conflicting evidence.                                                        |

## 16.5 Special assessment states

- INSUFFICIENT EVIDENCE - data cannot support a responsible readiness decision.

- CONFLICTING EVIDENCE - different sources materially disagree; human review recommended.

- MANAGER ATTESTED - human-provided evidence is stored distinctly from artifact-backed evidence.

# 17. Continuity Risk Model

## 17.1 Source of truth: rule engine

The risk class is determined by explicit resilience rules. A numeric index is derived for comparison/UI but never interpreted as failure probability.

| **Rule ID** | **Condition**                                                                                    | **Exposure**                                           |
|-------------|--------------------------------------------------------------------------------------------------|--------------------------------------------------------|
| R1          | CRITICAL/HIGH capability + **no** PRACTICED/VALIDATED engineer remaining (no adequate coverage) | `CRITICAL_GAP` exposure; CRITICAL class                 |
| R1b         | CRITICAL/HIGH capability + exactly one PRACTICED/VALIDATED engineer + no PRACTICED/VALIDATED backup (coverage without resilience) | `DEGRADED` exposure; HIGH class |
| R2          | CRITICAL/HIGH capability + one primary + best backup ASSISTED + incomplete/missing runbook       | HIGH                                                   |
| R3          | CRITICAL/HIGH capability + 2 PRACTICED/VALIDATED engineers                                       | LOW to MODERATE                                        |
| R4          | MEDIUM/LOW capability + single expert + good documentation                                       | MODERATE                                               |
| R5          | Evidence confidence LOW / conflicting                                                            | UNKNOWN/REVIEW rather than forced high-confidence risk |
| R6          | Validated backup exists but evidence STALE after major component change                          | HIGH or MODERATE depending on criticality              |

## 17.2 Numeric Continuity Risk Index

For MVP, map the rule class to a band, then apply small, inspectable modifiers. The class remains authoritative.

| **Class** | **Band** | **Anchor** |
|-----------|----------|------------|
| LOW       | 0-39     | 20         |
| MODERATE  | 40-59    | 50         |
| HIGH      | 60-79    | 70         |
| CRITICAL  | 80-100   | 90         |

| **Modifier**                                                                             | **Index adjustment (MVP)** |
|------------------------------------------------------------------------------------------|----------------------------|
| Missing critical runbook                                                                 | +5                         |
| Incomplete/outdated runbook                                                              | +3                         |
| High operational dependency (e.g., majority of recent P1 recovery evidence concentrated) | +3 — **not implemented**    |
| Best backup only EXPOSED                                                                 | +3                         |
| Best backup ASSISTED                                                                     | +1                         |
| Current complete runbook                                                                 | -3                         |
| Second PRACTICED engineer                                                                | -5                         |
| Second VALIDATED engineer                                                                | -8                         |

Clamp to the band corresponding to the authoritative risk class so modifiers cannot silently change the classification. Example: CRITICAL anchor 90 + missing runbook 5 + high dependency 3 = 98; display “98 / 100 CRITICAL.”

**Annotation, added during implementation (`RECOMMENDATIONS.md` R-08).** *High operational dependency* is
deliberately not implemented. It is true of nearly every sole-expert capability in the seeded data, so it
would add a constant to exactly the capabilities the sole-expert modifier already penalises — double-counting
one signal under two names and making the index harder to explain rather than more accurate. If it is wanted
later it should be redefined to capture something the sole-expert modifier does not, such as concentration
across a *component* rather than a capability. `app/continuity/reason_codes.py` is the implemented list, and
one modifier not in this table — `SOLE_ADEQUATE_ENGINEER`, +1 — was added there for the reason recorded in
`docs/DECISIONS.md`.

## 17.3 Platform/system aggregation

- System risk is driven by the highest-severity critical capabilities plus count of critical/high gaps; do not average severe gaps away.

- Platform risk is not calculated as an independent score. A platform communicates its highest system Continuity Risk Index, its total critical gaps, and its knowledge-drift status.

- Dashboard must allow drill-down from aggregate score to exact capability rule triggers.

# 18. Counterfactual Simulation Engine

## 18.1 Definition

The MVP “Engineer Unavailable” simulation temporarily excludes the selected engineer’s DEMONSTRATES edges from coverage calculations, recomputes best remaining readiness for each capability, applies risk rules, and aggregates changed exposure upward.

## 18.2 Algorithm

1\. Select engineer E and simulation scope (system; SYSTEM is the only scope implemented in MVP).

2\. Identify all capabilities C where E has readiness ≥ EXPOSED.

3\. For each C, ignore E when computing remaining coverage.

4\. Find best remaining engineer readiness and Evidence Confidence.

5\. Re-evaluate capability risk rules and index.

6\. Mark capability impact as Critical Gap, Degraded, Preserved, or Insufficient Evidence.

7\. Aggregate impacted capability states to components and the system in scope.

8\. Generate evidence-grounded explanation using deterministic result + graph facts.

## 18.3 Required output

| **Field**        | **Example**                                      |
|------------------|--------------------------------------------------|
| Engineer         | Alex Chen                                        |
| System affected  | Payment Gateway (scope is a single system in MVP) |
| Critical gaps    | Incident Recovery, Certificate Recovery          |
| Degraded         | Provider Failover                                |
| Preserved        | Retry Logic, Monitoring                          |
| Risk before      | 74 / 100 HIGH according to seeded rules          |
| Risk after       | 93 / 100 CRITICAL                                |
| Disclaimer       | Coverage simulation; not an outage prediction.   |

# 19. Backup Candidate Recommendation

## 19.1 Objective

Identify technically adjacent people who may be reasonable cross-training candidates. The product shall never claim to know the best staffing choice because workload, career goals, leave, team priorities, and organizational constraints are outside the MVP evidence model.

## 19.2 Candidate features

- Existing readiness for the exposed capability.

- Demonstrated adjacent capabilities (e.g., TLS, secrets, deployment for certificate recovery).

- Familiarity with the same system/component.

- Evidence freshness and diversity.

- Operational evidence (incident/deployment) vs only development exposure.

- Knowledge gaps that would need to be closed.

## 19.3 Output policy

| **Allowed**                                                                                                                     | **Not allowed**                                     |
|---------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------|
| “Maria has HIGH technical overlap based on recent deployment, infrastructure-recovery, and assisted payment-incident evidence.” | “Maria is objectively the best employee to assign.” |
| Top 2-3 candidate comparison                                                                                                    | Percentage “87% employee match” fake precision      |
| Explain why not Jordan using missing evidence                                                                                   | Assume absence of evidence proves inability         |
| Manager selects candidate                                                                                                       | Autonomous assignment                               |

# 20. Knowledge-Transfer Plan Generation

## 20.1 Plan objective

Convert an exposed capability and chosen candidate into specific, reviewable work. Do not generate generic “train someone” advice.

## 20.2 Plan structure

| **Field**            | **Requirement**                                                  |
|----------------------|------------------------------------------------------------------|
| Capability target    | Exact capability causing exposure.                               |
| Candidate            | Manager-selected engineer.                                       |
| Mentor/source expert | Suggested from graph; editable.                                  |
| Current readiness    | Evidence-derived current state.                                  |
| Target readiness     | Suggested PRACTICED or VALIDATED; label as target, not achieved. |
| Actions              | 3-5 ordered actions.                                             |
| Acceptance criteria  | Observable evidence of completion for each action.               |
| Linked material      | Relevant incidents, PRs, runbooks, architecture docs.            |
| Status               | Draft → Approved (MVP only).                                     |

## 20.3 Demo plan example - Maria / Incident Recovery

1\. Review Payment Gateway recovery architecture and incidents INC-184 / INC-221. Acceptance: record unanswered questions and confirm recovery sequence.

2\. Shadow an incident-recovery exercise with Alex. Acceptance: complete runbook walkthrough and identify decision points.

3\. Execute provider failover in staging. Acceptance: restore transaction routing and document steps without step-by-step prompting.

4\. Run a simulated gateway recovery drill. Acceptance: independently follow recovery path and verify success checks.

5\. Update Payment Recovery runbook. Acceptance: add missing failover/rollback steps found during the exercise.

# 21. Human Challenge / Correct / Learn Workflow

Managers must be able to challenge an assessment without directly editing readiness/risk numbers. The graph changes only when evidence or mappings change.

| **Challenge action**       | **Behavior**                                                                                                                                       |
|----------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------|
| Link Evidence              | Manager selects existing artifact the AI missed/misclassified; artifact is reprocessed.                                                            |
| Add Manager Attestation    | Create provenance-labeled attestation with date, capability, claim, author; lower evidentiary weight than strong artifact-backed proof by default. |
| Correct Capability Mapping | Move evidence from wrong capability/system to correct one; recompute related readiness.                                                            |
| Recompute                  | Affected DEMONSTRATES edges, readiness, confidence, risk, and simulations update.                                                                  |
| Audit trail                | Store previous assessment, challenge reason, added/corrected evidence, and new result.                                                             |

| **Rule:** Scores change because evidence changes - not because a manager manually overwrote a score. |
|------------------------------------------------------------------------------------------------------|

# 22. Responsible AI, Privacy, and Safety Boundaries

## 22.1 Allowed data

- GitHub commits/PRs/reviews/issues.

- Engineering tickets and incident records.

- Runbooks, architecture docs, approved technical documentation.

- Optional future organization-approved technical collaboration channels.

- Declared service ownership/team metadata.

## 22.2 Explicitly prohibited product behavior

- Analyze private DMs or personal email.

- Track working hours, online time, keyboard/mouse activity, location, or browser behavior.

- Infer personality, sentiment, loyalty, engagement, or protected/sensitive personal attributes.

- Produce employee productivity/value scores.

- Recommend firing, layoff ordering, promotion, bonus amount, or compensation.

- Use Continuity Risk as a proxy for employee worth.

- Autonomously assign staffing or training without manager approval.

## 22.3 Language policy

| **Avoid**                         | **Use instead**                                                         |
|-----------------------------------|-------------------------------------------------------------------------|
| “Alex is a 93 risk.”              | “Payment Gateway has a 93/100 Continuity Risk Index.”                   |
| “Jordan cannot recover Payments.” | “No qualifying independent recovery evidence was found for Jordan.”     |
| “Maria is the best employee.”     | “Maria has the strongest technical overlap among evaluated candidates.” |
| “92% chance of failure.”          | “Continuity Risk Index 92/100; not a failure probability.”              |

# 23. System Architecture and Technical Stack

## 23.1 Stack

| **Layer**     | **MVP choice**                                                      | **Reason**                                                                |
|---------------|---------------------------------------------------------------------|---------------------------------------------------------------------------|
| Frontend      | Next.js + React + TypeScript                                        | Polished hackathon UX and interactive graph/simulation.                   |
| Backend       | FastAPI + Python                                                    | Natural for data generation, AI processing, graph/risk logic, evaluation. |
| Persistence   | SQLite / lightweight relational store behind typed graph repository | Fast, deterministic, no graph-DB setup risk.                              |
| Graph model   | Python typed nodes/edges + repository/traversal layer               | Preserves graph semantics independent of storage.                         |
| AI adapter    | Provider-neutral service interface                                  | Centralized structured extraction and plan generation.                    |
| Visualization | React graph library or lightweight SVG/DOM graph                    | Contextual graph only; avoid enterprise-scale graph complexity.           |
| Testing       | pytest + frontend component/e2e tests                               | Deterministic rules and simulation must be testable.                      |

## 23.2 Modular monolith

```text
frontend/ (Next.js)

dashboard/

systems/

graph/

simulations/

plans/



backend/ (FastAPI)

ingestion/

ai/

graph/

evidence/

continuity/

recommendations/

plans/

evaluation/

api/
```

## 23.3 Processing flow

```text
Artifacts

↓ normalize

AI Evidence Extractor

↓ structured evidence

Taxonomy Normalizer

↓

Typed Knowledge Graph

↓

Readiness / Freshness / Confidence Engine

↓

Continuity Rule Engine

↓

Dashboard + Simulation

↓

Candidate Reasoning + Mitigation Generator

↓

Human Review / Approval
```

## 23.4 AI provider abstraction

```text
AIProvider

extract_evidence(artifact) -> EvidenceExtraction

normalize_taxonomy(candidates, context) -> NormalizedTaxonomy

explain_assessment(graph_facts, rule_facts) -> GroundedExplanation

compare_candidates(graph_facts) -> CandidateNarratives

generate_plan(selected_candidate, capability_gap, evidence) -> PlanDraft
```

Runtime LLM vendor is intentionally not hard-coded in the PRD. The challenge source establishes IBM Bob as the primary development tool, not a mandatory runtime inference API. Runtime provider choice must remain swappable.

# 24. API Contract Outline

> **Superseded.** This outline predates the frozen contract. `API_CONTRACT.md` is authoritative
> for endpoints, paths, and payloads — it freezes 10 endpoints under `/api/v1`. The table below
> is retained as design history. Endpoints listed here but absent from the frozen 10 are tracked
> in `DECISIONS.md` (CI-12, CI-13).

| **Method** | **Endpoint**                                 | **Purpose**                                                             |
|------------|----------------------------------------------|-------------------------------------------------------------------------|
| GET        | /api/portfolios                              | Dashboard portfolio hierarchy and aggregate risk.                       |
| GET        | /api/systems/{system_id}                     | System detail, components, capabilities, risk.                          |
| GET        | /api/capabilities/{capability_id}            | Capability coverage/readiness summary.                                  |
| GET        | /api/capabilities/{capability_id}/evidence   | Provenance cards and missing/conflicting evidence.                      |
| GET        | /api/graph/context                           | Contextual graph around portfolio/system/component/capability/engineer. |
| POST       | /api/simulations/unavailability              | Run engineer-unavailability simulation.                                 |
| GET        | /api/simulations/{id}                        | Retrieve simulation result.                                             |
| GET        | /api/capabilities/{capability_id}/candidates | Technical backup candidate comparison.                                  |
| POST       | /api/plans                                   | Generate mitigation plan for selected candidate.                        |
| PATCH      | /api/plans/{id}                              | Edit plan.                                                              |
| POST       | /api/plans/{id}/approve                      | Approve plan in MVP.                                                    |
| POST       | /api/assessments/{id}/challenge              | Link evidence / add attestation / correct mapping.                      |
| POST       | /api/ingest/synthetic                        | Load seeded NovaPay data.                                               |
| POST       | /api/ingest/github                           | Load normalized public GitHub export/API data.                          |

## 24.1 Simulation request example

```json
{

"engineer_id": "eng_alex_chen",

"scope_type": "system",

"scope_id": "system_payment_gateway"

}
```

## 24.2 Simulation response example

```json
{

"risk_before": 74,

"risk_after": 93,

"risk_class_after": "CRITICAL",

"critical_gaps": ["cap_incident_recovery", "cap_certificate_management"],

"degraded": ["cap_provider_failover"],

"preserved": ["cap_retry_logic", "cap_monitoring"],

"disclaimer": "Coverage simulation; not an outage prediction."

}
```

# 25. Evaluation and Validation Plan

## 25.1 Controlled prototype validation

Because real employee/incident knowledge data is sensitive and unavailable, the MVP uses a hidden-ground-truth NovaPay simulator. The application receives only generated/public artifacts. Evaluation compares inferred structure and decisions against the hidden model. This is prototype validation, not production accuracy evidence.

## 25.2 Metrics

| **Evaluation layer**      | **Metric / question**                                                                                                      |
|---------------------------|----------------------------------------------------------------------------------------------------------------------------|
| Knowledge reconstruction  | Did inferred engineer-capability readiness match hidden ground truth within accepted bucket tolerance?                     |
| Critical gap detection    | Did the rule engine identify hidden single-expert dependencies and avoid flagging healthy redundancy?                      |
| Counterfactual simulation | When engineer E is removed, did affected capability states match hidden expected coverage?                                 |
| Candidate recommendation  | Did top candidates align with hidden adjacent capability model?                                                            |
| Evidence grounding        | Do 100% of user-visible expertise/readiness claims expose at least one supporting source artifact or explicit attestation? |
| Uncertainty handling      | Does sparse evidence return Insufficient Evidence instead of a fabricated classification?                                  |

## 25.3 Reporting policy

- Report actual measured results only after tests run.

- Do not claim real-enterprise accuracy from synthetic evaluation.

- Document test dataset size, seed/version, and rule version.

- Keep hidden ground-truth file separate from app ingestion path.

# 26. Acceptance Criteria and Definition of Done

| **ID** | **Area**             | **Acceptance criterion**                                                                                                                                               |
|--------|----------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| AC-01  | Dashboard            | Loads 2-3 platforms and 5-7 systems; highest-risk system and critical-gap count are visible without drill-down.                                                       |
| AC-02  | System detail        | Clicking Payment Gateway shows components/capabilities, declared owner, risk index/class, and Evidence Confidence.                                                     |
| AC-03  | Graph                | Contextual graph renders System → Component → Capability → Engineer → Evidence relationships for selected scenario.                                                    |
| AC-04  | Provenance           | Every displayed readiness claim opens evidence cards with source ID/type/date/role/strength.                                                                           |
| AC-05  | Readiness            | Seeded hidden-ground-truth scenario yields Alex VALIDATED, Maria ASSISTED, Jordan EXPOSED for Payment Incident Recovery, or documented equivalent generated test case. |
| AC-06  | Simulation           | Simulating Alex unavailable changes Incident Recovery to Critical Gap while preserving at least one other capability (e.g., Retry Logic).                              |
| AC-07  | Risk                 | Before/after risk is deterministically reproducible from rules and “Why?” shows rule triggers.                                                                         |
| AC-08  | Candidate comparison | At least two candidates display strengths, gaps, evidence, and non-considered staffing factors.                                                                        |
| AC-09  | Human choice         | Manager can choose a non-top candidate and still generate a candidate-specific plan.                                                                                   |
| AC-10  | Plan                 | Generated plan contains 3-5 actions, acceptance criteria, linked evidence/material, and can be edited/approved.                                                        |
| AC-11  | Challenge            | Manager can link missed evidence or correct mapping and see readiness/risk recomputed.                                                                                 |
| AC-12  | Uncertainty          | A seeded sparse-data capability produces Insufficient Evidence.                                                                                                        |
| AC-13  | Privacy              | No employee productivity/value/layoff/bonus score exists anywhere in UI/API.                                                                                           |
| AC-14  | Performance          | Deterministic simulation returns in \<2 seconds on seeded dataset; normal read APIs target \<800ms local p95; AI plan/explanation operations target \<12 seconds.      |
| AC-15  | Demo reproducibility | Fresh clone + documented setup loads seeded dataset and reproduces hero scenario.                                                                                      |
| AC-16  | Challenge submission | README includes problem statement, solution, AI approach/architecture, challenge theme, and how IBM Bob was used; public video \<=3 minutes.                           |

## 26.1 Definition of Done

- All AC-01 through AC-16 pass or any exception is explicitly documented before submission.

- No demo-critical path depends on an unreliable live external API.

- All synthetic seeds required for the demo are versioned in the repository.

- AI prompts/output schemas are versioned and validated.

- No user-visible claim lacks evidence/provenance.

- Demo can be completed from a clean browser session in under 2 minutes 40 seconds, leaving buffer for intro/outro.

# 27. Three-Minute Hackathon Demo Script

Hero scenario: NovaPay Payment Gateway outage recovery. The first 20 seconds are incident-first for drama; the product itself still uses a Dashboard landing page.

| **Time**  | **Visual**                                                   | **Narration / objective**                                                                                                                                 |
|-----------|--------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------|
| 0:00-0:08 | P1 Payment Gateway outage card; Alex unavailable             | “NovaPay has redundant infrastructure, but during a payment outage the engineer who repeatedly restores service is unavailable.”                          |
| 0:08-0:18 | Declared owner Jordan vs demonstrated recovery evidence Alex | “Jordan officially owns the service. But the team’s work history tells a different story. The outage wasn’t predictable. The knowledge gap was.”          |
| 0:18-0:30 | ContinuityAI Dashboard; Payment Gateway 74 / 100 HIGH, 0 critical gaps, 2 capabilities without resilient backup | Introduce Engineering Knowledge Resilience and show platform visibility.                                                                                 |
| 0:30-0:50 | System Detail / Knowledge Graph                              | Show Payment Gateway → Gateway Integration → Incident Recovery → Alex/Maria/Jordan with evidence.                                                         |
| 0:50-1:08 | Click Why; provenance cards                                  | Show Alex independent P1 recoveries and Jordan missing independent recovery evidence.                                                                     |
| 1:08-1:28 | Simulate Alex Unavailable                                    | Incident Recovery → Critical Gap; Provider Failover degraded; Retry Logic preserved; risk 74 → 93, HIGH → CRITICAL. State clearly this is coverage, not outage prediction. |
| 1:28-1:50 | Candidate comparison                                         | Maria High overlap, Jordan Medium; show strengths/gaps and that manager chooses.                                                                          |
| 1:50-2:15 | Select Maria; Generate Plan                                  | Show 4 targeted actions with acceptance criteria.                                                                                                         |
| 2:15-2:30 | Approve Plan                                                 | Demonstrate AI prepares work; human approves.                                                                                                             |
| 2:30-2:45 | Architecture graphic                                         | Artifacts → AI extraction → evidence-backed graph → deterministic rules/simulation → grounded AI reasoning.                                               |
| 2:45-3:00 | Closing screen                                               | “Engineering tools tell you who worked on a system. ContinuityAI tells you whether the organization can still operate it when key expertise disappears.”  |

## 27.1 Mandatory demo claims

- Use “demonstrated evidence” language, not absolute knowledge claims.

- Say “Continuity Risk Index,” not probability.

- Say “coverage gap,” not “the system will fail.”

- Explicitly show evidence provenance once.

- Explicitly show human choice/approval once.

- Mention Bob’s role in building the prototype in final architecture/build note or README; do not force Bob into runtime architecture without evidence.

# 28. IBM Bob Development Plan

The challenge source requires IBM Bob as the primary development tool and describes Bob as assisting planning, coding, testing, and problem-solving. ContinuityAI will use Bob across the full build lifecycle and document that usage in the repository.

| **Phase**     | **Bob usage**                                                                     | **Evidence to retain**                         |
|---------------|-----------------------------------------------------------------------------------|------------------------------------------------|
| Planning      | Break PRD into small implementation tasks; identify dependencies and stop points. | Task prompts / planning notes.                 |
| Coding        | Generate/review backend models, APIs, rules, simulator, frontend components.      | Commits / notes attributing Bob-assisted work. |
| Testing       | Generate unit tests from readiness/risk/simulation acceptance criteria.           | Test files and results.                        |
| Debugging     | Analyze expected-vs-actual mismatches in hidden-ground-truth scenarios.           | Issue notes / fixes.                           |
| Documentation | Help maintain README, architecture, setup, evaluation results, demo notes.        | BUILD_WITH_BOB.md + README section.            |

## 28.1 BUILD_WITH_BOB.md outline

```text
# How IBM Bob Was Used

1. PRD decomposition

2. Knowledge graph schema implementation

3. Evidence extraction contract

4. Readiness/risk rule engine

5. Counterfactual simulation

6. Frontend workflow

7. Hidden-ground-truth tests

8. Debugging / validation

9. README and submission preparation
```

# 29. Implementation Sequence

Implement as a vertical slice with deterministic foundations before AI polish. Each milestone must have a testable stop point.

| **Milestone** | **Scope**                       | **Implementation**                                                                      | **Exit criterion**                                            |
|---------------|---------------------------------|-----------------------------------------------------------------------------------------|---------------------------------------------------------------|
| M1            | Repo + skeleton                 | Next.js app, FastAPI app, shared configuration, health endpoint, seeded DB loader.      | App boots; dashboard placeholder can call backend.            |
| M2            | Domain model                    | Platform/System/Component/Capability/Engineer/Evidence typed models; graph repository. | Seed graph can be traversed in tests.                         |
| M3            | Hidden-ground-truth generator   | NovaPay hidden model + artifact generator.                                              | Artifacts generated without exposing readiness labels to app. |
| M4            | Deterministic evidence engine   | Evidence strength/freshness/confidence/readiness rules.                                 | Unit tests pass for NONE→VALIDATED scenarios.                 |
| M5            | Risk engine                     | Criticality + coverage rules + numeric index bands/modifiers.                           | Why-risk output deterministic.                                |
| M6            | Counterfactual simulator        | Exclude engineer coverage; recompute capability/system risk.                            | Alex scenario produces targeted gap changes.                  |
| M7            | Dashboard + system detail       | Platform hierarchy, risk list, drill-down.                                             | AC-01/02 pass.                                                |
| M8            | Knowledge graph + provenance UI | Contextual graph, evidence drawer.                                                      | AC-03/04 pass.                                                |
| M9            | AI evidence extractor           | Structured schema + provider abstraction + validation.                                  | Sample artifacts map to correct capabilities/evidence roles.  |
| M10           | Candidate comparison            | Graph-based candidate search + grounded narratives.                                     | Top 2-3 candidate view works.                                 |
| M11           | Plan generation                 | Candidate-specific plan + edit/approve.                                                 | AC-10 pass.                                                   |
| M12           | Challenge workflow              | Link evidence / attestation / mapping correction + recompute.                           | AC-11 pass.                                                   |
| M13           | Evaluation                      | Run hidden-ground-truth comparison and record metrics.                                  | Evaluation report generated.                                  |
| M14           | Demo hardening                  | Seed lock, error handling, demo mode, README, BUILD_WITH_BOB, 3-min script.             | Clean-clone rehearsal succeeds.                               |

# 30. Risks and Mitigations

| **Risk**                                   | **Severity** | **Mitigation**                                                                                                                    |
|--------------------------------------------|--------------|-----------------------------------------------------------------------------------------------------------------------------------|
| Expertise inference is wrong               | High         | Provenance-first UI, evidence triangulation, uncertainty states, human challenge workflow.                                        |
| Synthetic data looks rigged                | High         | Hidden-ground-truth generator; app never sees true readiness labels; clearly label validation as controlled prototype.            |
| Scope creep                                | High         | Scope freeze; no live enterprise integrations, no autonomous execution, no full HR module.                                        |
| Graph visualization consumes too much time | Medium       | Contextual graph only; use simple stable visualization; data model matters more than animation.                                   |
| Risk score appears arbitrary               | High         | Rule class is source of truth; numeric index is banded/inspectable; Why view exposes triggers.                                    |
| Looks like surveillance                    | High         | System-first risk; strict prohibited-data list; no productivity/employee-worth decisions.                                         |
| LLM hallucination                          | High         | Structured schema validation, provenance requirement, deterministic scoring, unknown/low-confidence outputs.                      |
| Runtime AI API instability                 | Medium       | Provider abstraction + cache/precompute demo outputs where appropriate; deterministic path remains functional.                    |
| Real GitHub mapping to NovaPay is awkward  | Medium       | Normalize/anonymize public evidence; use real GitHub for activity credibility and synthetic private context for controlled story. |
| Demo exceeds 3 minutes                     | Medium       | Rehearse 2:40-2:50 cut; incident-first hook; one hero journey only.                                                               |

# 31. Post-MVP Roadmap

| **Horizon**                               | **Capabilities**                                                                                              |
|-------------------------------------------|---------------------------------------------------------------------------------------------------------------|
| Phase 2 - Integration                     | Live GitHub App, Jira, Confluence, ServiceNow/PagerDuty; SSO/RBAC; audit log.                                 |
| Phase 3 - Knowledge Drift                 | Scheduled graph refresh; new/resolved/stale risk alerts; historical trend views.                              |
| Phase 4 - Closed-loop mitigation          | Track plan completion; observe new evidence; update readiness only when qualifying evidence appears.          |
| Phase 5 - Enterprise graph                | Dedicated graph database, larger topology, multi-team dependencies, service catalog integration.              |
| Phase 6 - Approved collaboration evidence | Opt-in technical Slack/Teams channels under strict privacy controls; no private DMs.                          |
| Phase 7 - Contribution visibility         | Evidence-based review summaries that surface invisible technical/knowledge-sharing work without worth scores. |
| Phase 8 - Org-change simulation           | Evaluate proposed team moves/reorgs for capability coverage impact; remain human decision support.            |

# Appendix A. NovaPay Demo Model

## A.1 Platforms and systems

| **Platform**      | **System**          | **Business Criticality** |
|-------------------|---------------------|--------------------------|
| Payments Platform | Payment Gateway     | CRITICAL                 |
| Payments Platform | Refund Engine       | HIGH                     |
| Payments Platform | Billing Integration | HIGH                     |
| Identity Platform | Authentication      | CRITICAL                 |
| Identity Platform | Authorization       | HIGH                     |
| Data Platform     | Analytics Pipeline  | MEDIUM                   |

## A.2 Hero capability truth (hidden from app)

| **System**      | **Component**         | **Capability**         | **Alex**  | **Maria** | **Jordan** |
|-----------------|-----------------------|------------------------|-----------|-----------|------------|
| Payment Gateway | Gateway Integration   | Incident Recovery      | VALIDATED | ASSISTED  | EXPOSED    |
| Payment Gateway | Gateway Integration   | Provider Failover      | PRACTICED | PRACTICED | EXPOSED    |
| Payment Gateway | Transaction Processor | Retry Logic            | VALIDATED | EXPOSED   | VALIDATED  |
| Payment Gateway | Gateway Integration   | Certificate Management | VALIDATED | EXPOSED   | NONE       |
| Payment Gateway | Operations            | Monitoring             | PRACTICED | VALIDATED | ASSISTED   |

## A.3 Declared-vs-demonstrated demo mismatch

| **Fact**                                        | **Value**                                                                                                                       |
|-------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------|
| Declared Payment Gateway owner                  | Jordan Lee                                                                                                                      |
| Highest demonstrated Incident Recovery coverage | Alex Chen                                                                                                                       |
| Why mismatch matters                            | Ownership metadata alone would imply Jordan; incident/runbook evidence reveals Alex as the repeated independent recovery actor. |

# Appendix B. Example Structured Objects

## B.1 Evidence record

```json
{

"evidence_id": "evidence_inc_184",

"artifact_id": "INC-184",

"artifact_type": "incident",

"engineer_id": "eng_alex_chen",

"system_id": "system_payment_gateway",

"component_id": "component_gateway_integration",

"capability_id": "cap_incident_recovery",

"evidence_role": "INDEPENDENT_EXECUTION",

"strength": "STRONG",

"date": "2026-05-14",

"freshness": "FRESH",

"rationale": "Engineer diagnosed provider failover and restored transaction routing.",

"source_ref": "INC-184"

}
```

## B.2 Engineer-capability relationship

```json
{

"engineer_id": "eng_alex_chen",

"capability_id": "cap_incident_recovery",

"readiness": "VALIDATED",

"evidence_confidence": "HIGH",

"freshness": "FRESH",

"supporting_evidence_ids": ["evidence_inc_184", "evidence_inc_221", "evidence_doc_17"]

}
```

## B.3 Candidate comparison

```json
{

"capability_id": "cap_incident_recovery",

"candidate": "eng_maria_gomez",

"technical_overlap": "HIGH",

"strengths": ["production-deployment", "infrastructure-recovery", "monitoring", "assisted-payment-recovery"],

"gaps": ["independent-gateway-recovery", "provider-failover-execution"],

"not_considered": ["workload", "career-goals", "upcoming-leave", "team-priorities"]

}
```

# Appendix C. Final Scope Freeze Checklist

- □ MVP uses Dashboard → System → Graph/Evidence → Simulation → Candidate Comparison → Plan → Approval.

- □ Platform hierarchy is supported; risk originates at capability level and rolls upward.

- □ Primary user is Engineering Manager.

- □ Primary technical innovation is AI-generated evidence-backed Engineering Knowledge Graph.

- □ Counterfactual simulation is the hero capability.

- □ Real public GitHub + synthetic private enterprise data.

- □ Hidden-ground-truth synthetic generator used for evaluation.

- □ AI performs structured semantic extraction; deterministic rules perform readiness/risk/simulation.

- □ Continuity Risk Index is not a probability.

- □ Evidence Confidence is separate from risk.

- □ Readiness uses strength + diversity + repetition + freshness.

- □ Systems/capabilities are scored; employees are not globally risk-scored.

- □ People insights are secondary, evidence-only, and contain no performance/bonus score.

- □ Candidate recommendation is technical decision support; manager chooses.

- □ Plan is prepared by AI; manager edits/approves.

- □ No live Jira/Confluence/Slack integration required for MVP.

- □ No continuous monitoring required for MVP; Knowledge Drift is represented using seeded data.

- □ No autonomous staffing, promotions, bonuses, layoffs, or employee-worth decisions.

- □ IBM Bob is used across planning, coding, testing, debugging, and documentation.

- □ Three-minute demo is incident-first but product landing page is Dashboard.

# Source Note

Challenge requirements and framing in this PRD are grounded in the user-provided PDF “AI Builders Challenge with IBM Bob \| BeMyApp,” especially pages 6-8. The PDF states the August Space challenge and Wildcard Challenge, describes the Wildcard as “Build Intelligent Systems for the Future of Work,” requires a working prototype/proof of concept using IBM Bob as the primary development tool, a public GitHub repository with specified README content, and a public video no longer than three minutes, and lists judging criteria of Technical Execution, Innovation, Feasibility, Challenge Fit, and Real-World Impact. Product-specific requirements in this PRD were developed from the structured design decisions made in this conversation and are not claims from the challenge source.

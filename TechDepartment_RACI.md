# RACI Matrix – DevOps, SRE, Platform Engineering, Software Development, QA, Technical Support

## Legend

| Symbol | Meaning |
|---------|----------|
| **R** | Responsible – Does the work to complete the task |
| **A** | Accountable – Ultimately answerable for the correct completion |
| **C** | Consulted – Provides input or expertise before or during the task |
| **I** | Informed – Kept updated on progress or outcomes |

---

## RACI Matrix

| Activity / Responsibility | DevOps | SRE | Platform Eng | Software Dev | QA | Technical Support |
|----------------------------|:------:|:---:|:--------------:|:--------------:|:--:|:-----------------:|
| CI/CD pipeline design & maintenance | R | C | A | C | I | I |
| Infrastructure as Code (IaC) | R | C | A | I | I | I |
| Environment provisioning (e.g., EKS, EC2, Cloud) | R | C | A | I | I | I |
| Application deployment automation | R | C | A | C | I | I |
| Monitoring & alerting setup | C | A | R | I | I | I |
| Incident response (P1/P2 issues) | C | A | R | I | I | R |
| Customer-reported issue triage | I | C | I | C | I | A/R |
| Reliability & SLI/SLO definition | C | A | R | C | I | I |
| Cost optimisation (cloud, infra) | C | A | R | I | I | I |
| Security compliance / DevSecOps practices | A | C | R | C | I | I |
| Release management | R | I | C | A | C | I |
| Application performance tuning | C | A | R | R | I | C |
| Code development & feature implementation | I | I | I | A/R | C | I |
| Unit testing | I | I | I | A/R | C | I |
| Integration & regression testing | I | I | I | C | A/R | I |
| Load & performance testing | I | A/R | C | C | C | I |
| Continuous improvement / feedback loops | A | A | A | C | C | C |
| Tooling (CI/CD, observability, internal platforms) | C | C | A/R | I | I | I |
| Change management & approvals | R | C | A | C | I | I |
| Documentation & runbooks | R | A | C | C | I | C |
| Root cause analysis (post-incident review) | C | A | R | C | I | C |
| User issue documentation & FAQ updates | I | I | I | C | C | A/R |
| Monitoring dashboard maintenance | C | A | R | I | I | I |
| Escalation management (tiered support) | I | A | C | C | I | R |

---

## Notes

- **Technical Support** – First line for customer and production issues, responsible for triage and escalation.  
- **SRE** – Owns reliability, SLIs/SLOs, observability, and incident management.  
- **Platform Engineering** – Builds and maintains internal platforms, shared tooling, and infrastructure as a product.  
- **DevOps** – Focuses on automation, CI/CD, and bridging development and operations.  
- **Software Development** – Accountable for application code, bug fixes, and feature delivery.  
- **QA** – Owns testing strategy, automation, and release quality.

---


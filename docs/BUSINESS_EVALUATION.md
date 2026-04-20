# AgriTech Plant Disease Detection — Business Evaluation & Quality Assessment

## 1. Project Business Context

**Domain:** Agriculture / AgriTech.
**Business Problem:** Early detection of plant diseases currently relies on expensive and slow consultations with agronomists. This delay often results in late interventions, significant crop loss, and reduced farm profitability.
**Proposed Solution:** A binary image classification model designed to automatically detect the presence or absence of disease in plants using field-captured photographs.
**Primary Stakeholders:** Farm owners, agricultural managers, and field operators.
**Practical Value:** Reducing the initial detection cycle to seconds, allowing for more rapid response thus minimizing potential economic impact.

### Formal Business Goal
"To automate the primary detection of crop diseases using an **offline-capable** computer vision model, thereby reducing expert consultation costs and minimizing crop loss while ensuring the system saves more in prevented loss than it costs in false alarms."

---

## 2. Defined Business Outcomes

Success is defined as the deployment of a model that accurately differentiates between diseased and healthy plants, providing actionable insights even in low-connectivity environments.

**Expected Results:**
- **Reduce** operational costs associated with recurring expert consultations by filtering out clearly healthy crops.
- **Minimize** crop loss through accelerated detection and targeted intervention.
- **Accelerate** the decision-making process for field management via **Edge Inference**.
- **Optimize** field monitoring density by enabling operators to cover more high-risk areas.

---

## 3. Key Business Criteria for Quality

The project success is measured against five primary business criteria, prioritized by their impact on farm survival:
1.  **Risk Mitigation (Primary):** Preventing total crop failure via high-recall detection.
2.  **Cost Efficiency (Break-even):** Ensuring "false alarms" do not exceed the cost of saved crops.
3.  **Operational Latency (Edge-first):** Ensuring the system works in rural, low-connectivity zones.
4.  **Targeted Intervention Efficiency:** Shifting from "blind scouting" to "targeted scouting."
5.  **Solution Scalability:** Technical capacity to handle peak seasonal demand.

---

## 4. Business Metrics System

| Business Criterion | Business Metric | Unit | Target Value | Data Source |
| :--- | :--- | :--- | :--- | :--- |
| Risk Mitigation | Attributable loss reduction (vs. Control Group) | % | > 10% | A/B Pilot Study |
| Cost Efficiency | Break-even Precision Threshold | % | > 70% | Model Performance / Finance |
| Operational Latency | On-device (Edge) Inference Time | seconds | < 3 sec | Device Logs (no network) |
| Intervention Efficiency | Targeted scouting density (interventions/km) | % increase | +50% | Field operator logs |
| Scalability | Peak Concurrent Request Handling | RPM | > 1000 RPM | Synthetic Load Testing |

---

## 5. Alignment: Business Criteria vs. ML Metrics

The critical balance in this project is the **Recall/Precision Trade-off**. A "perfect" recall model that flags everything as diseased is business-useless.

| Business Criterion | ML Metric | Relationship | Operational Constraint |
| :--- | :--- | :--- | :--- |
| **Risk Mitigation** | **Recall** (Diseased) | High Recall prevents the scenario of undetected spread. | **Target: >= 90%** |
| **Cost Efficiency** | **Precision** | Low Precision triggers False Positives wasting expert fees. | **Hard Guardrail: >= 70%** (Break-even point) |
| **Operational Latency** | **Model Size / FLOPS** | Smaller models enable execution on budget smartphones without cloud upload. | **Target: < 50MB model size** |

### The "Break-even" Logic
A false positive costs exactly one expert consultation fee ($C$). A false negative costs the value of the lost crop ($L$). The model is only business-viable if:
` (Precision * Value_Saved) > ((1 - Precision) * Consultation_Cost) `

---

## 6. Integral Quality Evaluation (Risk-Aware Weight Model)

Weights have been adjusted to prioritize farm survival (Risk) and profitability (Cost) over efficiency metrics.

| Criterion | Weight | Target | Actual (Hypothetical)* | Achievement | Final Contribution |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Risk Mitigation (Recall) | 45% | > 10% red. | 12% red. | 100% | 45.00% |
| Cost Efficiency (Precision) | 25% | > 70% Prec. | 68% Prec. | 97% | 24.25% |
| Operational Latency (Edge) | 15% | < 3s (Edge) | 2.8s (Edge) | 100% | 15.00% |
| Intervention Efficiency | 10% | +50% dens. | +30% dens. | 60% | 6.00% |
| Scalability | 5% | > 1000 RPM | 1500 RPM | 100% | 5.00% |
| **Total** | **100%** | | | | **Sum: 95.25%** |

*\*Note: Achievement is calculated as (Actual / Target). Values are for illustrative planning.*

**Quality Level:** 95.25% indicates a **Critical Success Level**, provided the Precision guardrail is strictly monitored.

---

## 7. Business Feasibility & Attribution Analysis

- **Feasibility:** The project is feasible only if **Edge Inference** is implemented. Rural 4G/5G latency makes cloud-based detection a secondary, unreliable option.
- **Attribution Strategy:** To avoid spurious correlations (e.g., claiming weather-driven health as ML success), we will use **Split-Field A/B Testing** during the pilot. One half of the farm will use the app-guided scouting, while the other uses traditional intervals.
- **Recommendation:** Proceed with deployment but implement a **"Confidence Threshold"** feature. If the model is < 85% certain, it should automatically recommend a human expert rather than providing a binary answer, further protecting the Precision/Recall balance.


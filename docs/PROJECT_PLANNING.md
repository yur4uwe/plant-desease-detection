# AgriTech Plant Disease Detection — Project Planning

## 1. Needs and Stakeholder Analysis

### Stakeholders
- Farm owners — end users whose crop losses represent the core problem the product addresses
- AgriTech firm management — internal project sponsor concerned with delivery timeline and commercial viability
- Agricultural domain experts and agronomists — consulted for data label validation and domain knowledge
- Data providers — owners of public datasets and educational resources whose terms of use govern data collection

### Problems
- Farm owners operating at scales where crop diseases have significant financial impact
- Crop diseases spread unnoticed until visible damage has already affected large areas
- Early detection currently requires either constant expert presence or careful manual inspection of large areas
- Both expert consultation and manual inspection are expensive and slow to scale
- Delayed detection increases losses due to damage spreading before any response is possible

---

## 2. Project Goals and Objectives

- **Specific:** Develop a binary classification model that detects the presence or absence of disease in plant photographs, trained on publicly available image datasets
- **Measurable:** Achieve a minimum classification accuracy of 90% on a held-out test set
- **Achievable:** Leverage existing public datasets and established CNN architectures to build and validate the model within the project timeframe
- **Relevant:** Early disease detection directly reduces crop losses by enabling faster response before disease spreads
- **Time-Bound:** Deliver a trained, evaluated and documented binary classification model with a complete data pipeline within 16 weeks

---

## 3. Project Implementation Stages

- **Initiation:** Market and domain research to identify commercially relevant crops and feasibility of available public datasets
- **Planning:** Define project scope, objectives, data strategy, toolchain, and timeline across 16 weeks
- **Execution:**
  - Data scraping and collection from public internet sources
  - Data verification and quality assessment of collected images and labels
  - Data pipeline development for preprocessing and augmentation
  - Model development using established CNN architectures
  - Model evaluation, iteration and performance enhancement
- **Monitoring & Control:** Continuous tracking of model performance metrics against the 90% accuracy target throughout execution
- **Closing:** Final model documentation, evaluation report, and API development as stretch goal

---

## 4. Data Resource Assessment

- Primary data consists of labeled photographs of both healthy and diseased plants
- Labels are binary — healthy or diseased — regardless of specific disease type
- Data will be sourced from publicly available datasets and educational resources scraped from the internet
- Dataset diversity across multiple sources is preferred to reduce bias from any single collection methodology
- Data quality assessment will be performed prior to pipeline development to filter unusable or mislabeled images
- Volume and class balance between healthy and diseased samples will be evaluated to prevent model bias toward either class

---

## 5. Potential Risk Assessment

### Project Risks
- Insufficient publicly available data for target crops and diseases
- Time constraints preventing full model iteration within 16 weeks
- Scope creep pulling focus from core binary classification deliverable toward full disease identification

### Data Risks
- Poor image quality from internet scraping
- Incorrect or inconsistent labeling in source datasets
- Class imbalance between healthy and diseased plant images
- Disease symptoms not fully visible in image at time of capture

### Model Risks
- Overfitting to dataset conditions not representative of real field photography
- Model performance degrading on crop varieties underrepresented in training data

### Product Risks
- False negatives — diseased plants classified as healthy, delaying response and spreading damage
- False positives — healthy plants flagged as diseased, causing unnecessary intervention costs
- On-field image capture remains a manual labor cost in real deployment, potentially offsetting savings from automated detection
- Over-reliance on model output without expert verification for treatment decisions

---

## 6. Business Benefits of Project Implementation

- Automated detection eliminates the need for costly agronomist consultations at the initial monitoring stage, reserving expert involvement for treatment decisions only
- Immediate classification from a photograph compresses disease response time from days to seconds, directly limiting spread before intervention
- A model-based solution can monitor far larger crop areas than manual inspection or periodic expert visits allow, making systematic monitoring economically viable
- Plant disease intervention is only financially justified when potential crop loss exceeds intervention cost — by dramatically reducing detection cost, the model makes precision intervention accessible to farm owners who previously could not afford the monitoring infrastructure to reach that decision point
- Earlier detection directly reduces crop losses and remediation costs by catching disease before it spreads to neighboring plants
- Agronomist expertise is redirected from routine monitoring toward higher-value treatment and containment decisions, improving overall resource efficiency on the farm

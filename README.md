Here’s a clean handoff summary you can paste into a new chat.

---

# Project Summary: Automated Resume Ranking via Skill Graph

I am building a **B2B resume-ranking and candidate-fit platform** for companies. The main business goal is:

> Help businesses identify which candidates are the best fit for a specific job role, even when resumes and job descriptions do not use the exact same keywords.

The core idea is to go beyond simple keyword matching by using:

```text
Skill extraction
+ Skill taxonomy
+ Skill graph
+ Vector similarity
+ Graph similarity
+ Dynamic job-domain weighting
+ Project/responsibility evidence
+ Candidate skill-gap analysis
```

There is also a user-facing goal:

> Help candidates understand what skills they are missing, follow a skill tree, and take tests/quizzes to improve their fit for target roles.

So the project has two sides:

```text
Business side:
Rank and compare candidates for jobs.

Candidate side:
Skill tree, missing skills, learning path, and tests.
```

---

# Dataset Used

I used two Kaggle datasets:

## 1. Resume Data for Ranking

This is the main dataset.

It contains:

```text
9544 resume-job pairs
35 columns
matched_score column
resume skills
job required skills
candidate experience/responsibilities
job position name
```

Important columns:

```text
skills
related_skils_in_job
job_position_name
skills_required
matched_score
career_objective
responsibilities
certification_skills
positions
professional_company_names
```

This dataset is used for:

```text
Resume-job matching
Ranking candidates
Comparing my ranking score against matched_score
```

## 2. Job Skill Set Dataset

This is the auxiliary dataset.

It contains:

```text
1167 job postings
5 categories
job_title
job_description
job_skill_set
```

Important columns:

```text
category
job_title
job_description
job_skill_set
```

It is used for:

```text
Building skill co-occurrence relationships
Strengthening the skill graph
Getting additional job-skill patterns
```

---

# Dataset Filtering

The original data had many non-tech roles like HR, finance, sales, civil engineering, mechanical engineering, trade marketing, etc.

For the first working version, I filtered to tech-related roles only.

Tech resume rows after filtering:

```text
4425
```

Tech job skill rows:

```text
240
```

Selected roles include:

```text
Senior Software Engineer
Machine Learning (ML) Engineer
AI Engineer
Database Administrator (DBA)
System Administrator
Network Support Engineer
Senior iOS Engineer
Executive/ Sr. Executive -IT
Intern (Generative AI Engineering - 2D/3D Image Generation)
DevOps Engineer
Data Engineer
Full Stack Developer (Python,React js)
Data Science Engineer
```

Reason for filtering:

```text
The original dataset had too many generic/non-tech terms like sales, accounting, customer service, communication, project management, etc.
These polluted the skill graph.
```

---

# Current Codebase

The codebase currently has these main files:

```text
data_loading.py
data_profile.py
preprocess_tech.py
skill_taxonomy.json
build_vectors_and_graph.py
analyze_graph.py
```

---

# File: data_loading.py

Purpose:

```text
Loads both CSV datasets and prints their columns.
```

This was used to inspect the raw structure of both datasets.

The resume dataset columns included:

```text
address
career_objective
skills
educational_institution_name
degree_names
passing_years
educational_results
result_types
major_field_of_studies
professional_company_names
company_urls
start_dates
end_dates
related_skils_in_job
positions
locations
responsibilities
certification_skills
job_position_name
educationaL_requirements
experiencere_requirement
responsibilities.1
skills_required
matched_score
```

The job skill dataset columns included:

```text
job_id
category
job_title
job_description
job_skill_set
```

---

# File: data_profile.py

Purpose:

```text
Profiles the raw datasets before cleaning.
```

It prints:

```text
shape
columns
data types
missing values
duplicate rows
sample rows
text column stats
top skills/items
matched_score distribution
job role/category distribution
```

Important findings:

```text
Resume dataset shape: 9544 x 35
Job skill dataset shape: 1167 x 5
Resume dataset has matched_score with no missing values
matched_score mean: around 0.66
matched_score max: 0.97
matched_score min: 0.0
```

The raw skill columns were noisy.

Examples of frequent raw skills:

```text
python
machine learning
sql
data analysis
deep learning
excel
java
c++
natural language processing
sales
documentation
accounting
project management
microsoft office
```

This showed that filtering and noise removal were necessary.

---

# File: preprocess_tech.py

Purpose:

```text
Filters the data to tech roles.
Cleans text.
Parses skill lists.
Normalizes skill aliases.
Removes noisy/generic terms.
Creates cleaned CSV files.
```

Main outputs:

```text
clean_tech_resume_dataset.csv
clean_tech_job_skill_dataset.csv
initial_skill_vocab.json
skill_frequency.json
```

Important preprocessing steps:

## 1. Tech role filtering

Only selected tech roles are kept.

## 2. Skill parsing

Some columns store skills like:

```python
['Python', 'SQL', 'Machine Learning']
```

or nested lists like:

```python
[['Data Analysis', 'Business Analysis']]
```

The parser handles these and converts them into clean lowercase skill lists.

## 3. Alias normalization

Examples:

```text
reactjs → react
react.js → react
react js → react
nodejs → node.js
sklearn → scikit-learn
natural language processing → nlp
ml → machine learning
ai → artificial intelligence
powerbi → power bi
mysql database → mysql
ms office → microsoft office
python programming → python
ios application development → ios development
asp.net mvc strong understanding of database design → asp.net
```

## 4. Noise removal

Generic/noisy terms are removed or reduced, such as:

```text
none
n/a
advanced
intermediate
sales
marketing
customer service
clients
budgeting
financial statements
accounting
microsoft office
word
powerpoint
outlook
communication
leadership
problem solving
project management
documentation
research
quality
scheduling
```

## 5. Combined text fields

The cleaned resume dataset has:

```text
resume_text
job_text
resume_skills
job_required_skills
related_job_skills
matched_score
```

The resume text should include:

```text
career_objective
skills
certification_skills
positions
responsibilities
professional_company_names
degree_names
major_field_of_studies
```

The job text includes:

```text
job_position_name
skills_required
related_skils_in_job
responsibilities.1
educationaL_requirements
experiencere_requirement
```

---

# File: skill_taxonomy.json

Purpose:

```text
Defines canonical technical skill domains.
Used to filter skills, create domain nodes, and build the skill graph.
```

Current domains:

```text
programming_languages
machine_learning_ai
ml_frameworks_libraries
data_engineering_big_data
frontend
backend
databases
cloud_devops
mobile_development
networking_security
analytics_bi
software_engineering
```

Example taxonomy:

```json
{
  "programming_languages": [
    "python",
    "java",
    "c",
    "c++",
    "javascript",
    "typescript",
    "r",
    "swift",
    "kotlin",
    "sql"
  ],
  "machine_learning_ai": [
    "machine learning",
    "artificial intelligence",
    "deep learning",
    "nlp",
    "computer vision",
    "neural networks",
    "predictive modeling",
    "model training",
    "model evaluation",
    "data mining",
    "generative ai",
    "large language models",
    "llm"
  ],
  "ml_frameworks_libraries": [
    "tensorflow",
    "pytorch",
    "scikit-learn",
    "keras",
    "opencv",
    "numpy",
    "pandas",
    "matplotlib"
  ]
}
```

The taxonomy intentionally excludes most soft skills from core ranking because they inflated scores.

---

# File: build_vectors_and_graph.py

Purpose:

```text
Builds vectors.
Builds the skill graph.
Prunes graph edges.
Computes resume ranking scores.
Exports graph and ranked results.
```

Main outputs:

```text
ranked_tech_resumes.csv
skill_vocab_final.json
skill_graph.json
```

## Graph construction

The graph has two types of edges:

### 1. Taxonomy edges

Example:

```text
tensorflow → ml_frameworks_libraries
python → programming_languages
docker → cloud_devops
```

### 2. Co-occurrence edges

If skills appear together often in resumes/JDs, they are connected.

Example:

```text
python ↔ machine learning
machine learning ↔ deep learning
mongodb ↔ nosql
cisco ↔ linux
```

## Graph pruning

Initially the graph was too dense:

```text
Nodes: 122
Edges: 2604
Density: 0.3528
```

This made almost everything close to everything.

Then weak edges were pruned using:

```python
min_weight = 50
```

After pruning:

```text
Nodes: 122
Edges: 508
Density: 0.0688
Connected components: 1
Largest component size: 122
```

This is a much healthier graph.

## Final ranking formula before latest planned upgrade

The shortlist score was:

```text
shortlist_score =
0.60 × weighted/direct skill coverage
+ 0.25 × cosine skill similarity
+ 0.15 × graph similarity
```

Then multiplied by:

```text
coverage_penalty
```

Coverage penalty prevents tiny matches like:

```text
[excel] → [excel]
```

from getting perfect scores.

---

# File: analyze_graph.py

Purpose:

```text
Analyzes graph quality.
```

It prints:

```text
number of nodes
number of edges
density
connected components
largest component size
top high-degree nodes
domain node counts
strongest edges
```

Current graph analysis:

```text
Nodes: 122
Edges: 508
Density: 0.0688
Connected components: 1
Largest component size: 122
```

Top high-degree nodes:

```text
machine learning: 66
python: 55
data analysis: 37
java: 35
sql: 35
deep learning: 33
nlp: 31
```

Strongest edges:

```text
machine learning -- python
data analysis -- machine learning
data analysis -- python
java -- python
data analysis -- sql
deep learning -- machine learning
python -- sql
machine learning -- nlp
python -- scikit-learn
python -- tensorflow
pytorch -- tensorflow
mongodb -- nosql
cisco -- linux
```

The graph is usable now, but high-degree hub skills like `machine learning`, `python`, `sql`, and `java` still need to be treated carefully.

---

# Current Ranking Status

Current final score stats after pruning:

```text
count: 4425
mean: 0.101
std: 0.157
min: 0.0
25%: 0.0
50%: 0.0
75%: 0.1896
max: 0.85
```

This is better than before because the model is less overconfident.

Per-role rankings are now printed instead of global top 10.

Current roles printed include:

```text
AI Engineer
Data Engineer
Data Science Engineer
Database Administrator
DevOps Engineer
Executive/ Sr. Executive -IT
Full Stack Developer
Intern Generative AI Engineer
Machine Learning Engineer
Network Support Engineer
Senior Software Engineer
Senior iOS Engineer
System Administrator
```

---

# Current Problem

The graph-based score works, but graph similarity can still be high because of hub skills.

Example hubs:

```text
machine learning
python
java
sql
data analysis
```

So the graph is good for semantic matching, but it should not be the final judge.

The project should use a multi-stage ranking approach:

```text
Stage 1:
Skill graph + vectors create candidate shortlist.

Stage 2:
Project/responsibility evidence checks whether the candidate actually used those skills.

Stage 3:
Role-domain alignment checks if the candidate’s skill distribution fits the job.
```

---

# Latest Planned Upgrade

The next upgrade is to replace static domain weights with **dynamic JD-based domain weighting**.

Reason:

Static weights are too rigid. They break for hybrid/custom job titles like:

```text
Forward Deployed Engineer
AI Platform Engineer
Data Infrastructure Engineer
ML Ops Engineer
```

Instead of hardcoding:

```python
machine_learning_ai = 1.5
cloud_devops = 1.3
```

the system should infer domain importance from the job description.

---

# Planned Updates by File

## Update: preprocess_tech.py

Add `professional_company_names` to `resume_text`.

Current or target resume text columns:

```python
[
    "career_objective",
    "skills",
    "certification_skills",
    "positions",
    "responsibilities",
    "professional_company_names",
    "degree_names",
    "major_field_of_studies"
]
```

Reason:

```text
Project/responsibility evidence scoring needs richer resume text.
```

---

## Update: build_vectors_and_graph.py

This is the main file to update.

### Add DOMAIN_HINTS

Purpose:

```text
Infer important domains from job description language.
```

Example:

```python
DOMAIN_HINTS = {
    "cloud_devops": [
        "deployment",
        "infrastructure",
        "production",
        "kubernetes",
        "docker",
        "terraform",
        "ci/cd",
        "server",
        "monitoring",
        "scaling",
        "cloud",
        "devops"
    ],
    "backend": [
        "api",
        "apis",
        "backend",
        "microservices",
        "distributed systems",
        "server-side",
        "integration",
        "scalable systems",
        "application development"
    ],
    "machine_learning_ai": [
        "machine learning",
        "artificial intelligence",
        "model training",
        "inference",
        "fine-tuning",
        "nlp",
        "computer vision",
        "neural networks",
        "generative ai"
    ],
    "data_engineering_big_data": [
        "etl",
        "data pipeline",
        "big data",
        "spark",
        "hadoop",
        "hive",
        "pyspark",
        "data warehouse"
    ],
    "frontend": [
        "frontend",
        "react",
        "javascript",
        "typescript",
        "html",
        "css",
        "ui",
        "web application"
    ],
    "databases": [
        "database",
        "sql",
        "mysql",
        "postgresql",
        "mongodb",
        "redis",
        "elasticsearch",
        "nosql"
    ],
    "mobile_development": [
        "ios",
        "android",
        "swift",
        "kotlin",
        "mobile app",
        "mobile application"
    ],
    "networking_security": [
        "network",
        "networking",
        "cisco",
        "ccna",
        "firewall",
        "security",
        "lan",
        "wan"
    ],
    "analytics_bi": [
        "analytics",
        "data analysis",
        "business analysis",
        "dashboard",
        "tableau",
        "power bi",
        "excel",
        "reporting"
    ],
    "software_engineering": [
        "software engineering",
        "testing",
        "debugging",
        "quality assurance",
        "algorithms",
        "data structures",
        "requirements"
    ]
}
```

---

### Add infer_dynamic_domain_weights()

Purpose:

```text
Generate job-specific domain weights from explicit job skills and semantic hints.
```

Formula:

```text
domain_weight = 1.0 + boost
boost = min(0.5, hits * 0.08)
```

Explicit skills count more than hints.

Pseudo-code:

```python
def infer_dynamic_domain_weights(job_text, job_skills, skill_to_domain):
    domain_hits = {domain: 0 for domain in set(skill_to_domain.values())}

    for skill in job_skills:
        domain = skill_to_domain.get(skill)
        if domain:
            domain_hits[domain] += 2

    job_text = str(job_text).lower()

    for domain, hints in DOMAIN_HINTS.items():
        for hint in hints:
            if hint in job_text:
                domain_hits[domain] += 1

    domain_weights = {}

    for domain, hits in domain_hits.items():
        boost = min(0.5, hits * 0.08)
        domain_weights[domain] = 1.0 + boost

    return domain_weights
```

---

### Replace static weighted score with dynamic coverage

New function:

```python
def dynamic_weighted_skill_coverage(resume_skills, job_skills, skill_to_domain, domain_weights):
    if not job_skills:
        return 0.0

    resume_set = set(resume_skills)
    job_set = set(job_skills)

    total_weight = 0.0
    matched_weight = 0.0

    for skill in job_set:
        domain = skill_to_domain.get(skill, "unknown")
        weight = domain_weights.get(domain, 1.0)

        total_weight += weight

        if skill in resume_set:
            matched_weight += weight

    if total_weight == 0:
        return 0.0

    return matched_weight / total_weight
```

---

### Add role_domain_alignment_score()

Purpose:

```text
Measures whether candidate skills belong to the dominant JD domains.
```

This helps avoid “smart but wrong-domain” candidates.

Example:

```text
DevOps JD
Candidate has mostly ML skills
→ lower alignment
```

Function:

```python
def role_domain_alignment_score(resume_skills, skill_to_domain, domain_weights):
    if not resume_skills:
        return 0.0

    top_domains = sorted(
        domain_weights.items(),
        key=lambda x: x[1],
        reverse=True
    )[:3]

    important_domains = {domain for domain, weight in top_domains if weight > 1.0}

    if not important_domains:
        return 0.0

    aligned_count = 0

    for skill in resume_skills:
        domain = skill_to_domain.get(skill)
        if domain in important_domains:
            aligned_count += 1

    return aligned_count / len(resume_skills)
```

---

### Add project_evidence_score()

Purpose:

```text
Checks if matched skills appear near action verbs in resume text.
```

This is based on the idea that skill lists alone are weak, but responsibilities/projects show proficiency.

Action verbs:

```python
ACTION_VERBS = [
    "built",
    "developed",
    "implemented",
    "designed",
    "trained",
    "optimized",
    "deployed",
    "created",
    "integrated",
    "automated",
    "maintained",
    "tested",
    "evaluated",
    "improved",
    "managed"
]
```

Function:

```python
def project_evidence_score(resume_text, matched_skills):
    if not matched_skills:
        return 0.0

    text = str(resume_text).lower()
    evidence_count = 0

    for skill in matched_skills:
        skill = skill.lower()

        if skill not in text:
            continue

        skill_pos = text.find(skill)

        window_start = max(0, skill_pos - 80)
        window_end = min(len(text), skill_pos + 80)
        context_window = text[window_start:window_end]

        if any(verb in context_window for verb in ACTION_VERBS):
            evidence_count += 1

    return evidence_count / len(matched_skills)
```

---

### Update scoring loop

New scoring design:

```text
shortlist_score =
0.60 × dynamic weighted skill coverage
+ 0.25 × cosine similarity
+ 0.15 × graph similarity
```

Then:

```text
final_fit_score =
0.65 × shortlist_score
+ 0.20 × role_domain_alignment
+ 0.15 × project_evidence_score
```

Columns to save:

```text
direct_match
cosine_skill
graph_similarity
coverage_penalty
shortlist_score
role_domain_alignment
project_evidence_score
final_fit_score
```

Sort by:

```text
final_fit_score
```

not old `final_ranking`.

---

## Update: analyze_graph.py

Optional small update:

```python
degrees = [degree for _, degree in G.degree()]
print("Average degree:", sum(degrees) / len(degrees))
```

No major change needed.

---

## No Change Needed

These files do not need changes right now:

```text
data_loading.py
data_profile.py
skill_taxonomy.json
```

---

# Recommended System Architecture

Final intended architecture:

```text
Resume Dataset
        ↓
Preprocessing + skill normalization
        ↓
Skill taxonomy mapping
        ↓
Skill vectors
        ↓
Skill graph construction
        ↓
Graph pruning
        ↓
Stage 1 ranking:
    dynamic weighted skill coverage
    cosine similarity
    graph similarity
        ↓
Shortlist candidates
        ↓
Stage 2 reranking:
    role-domain alignment
    project evidence score
        ↓
Final candidate fit score
        ↓
Business dashboard + candidate skill-gap view
```

---

# Product Vision

## B2B Business Dashboard

For companies/recruiters:

```text
Upload/select job description
Upload/select resumes
Rank candidates
Compare candidates side-by-side
See matched skills
See missing critical skills
See graph-inferred related skills
See evidence from projects/responsibilities
Get final fit score
```

Main business value:

```text
Companies can shortlist better candidates faster, even when resumes do not exactly match JD keywords.
```

## Candidate/User Dashboard

For job seekers:

```text
Choose target role
See current skill profile
See missing skills
View skill tree
Take skill tests/quizzes
Get improvement roadmap
Track readiness score
```

Example:

```text
Target role: ML Engineer

Already has:
Python, SQL, Pandas

Missing:
PyTorch, Docker, AWS, model evaluation

Recommended path:
Machine Learning basics
→ Deep Learning
→ PyTorch
→ Deployment with Docker
→ Cloud deployment
```

---

# Frontend Plan

Suggested frontend pages:

```text
/ranking
/graph
/compare
/skill-gap
/tests
/skill-tree
```

## /ranking

Shows candidate ranking table:

```text
Candidate ID
Job Role
Matched Score
Direct Match
Cosine Skill
Graph Similarity
Shortlist Score
Role Domain Alignment
Project Evidence Score
Final Fit Score
```

## /graph

Shows the skill graph using:

```text
Cytoscape.js
```

Reason:

```text
Cytoscape is better than React Flow for actual node-link graph visualization.
```

## /compare

Compare two candidates:

```text
Exact matched skills
Missing skills
Related graph skills
Project evidence
Final fit score
```

## /skill-gap

Shows:

```text
Candidate has
Candidate lacks
Recommended next skills
```

## /skill-tree

A visual tree of skills required for a target role.

Example:

```text
Machine Learning Engineer
├── Programming
│   ├── Python
│   └── SQL
├── ML Core
│   ├── Machine Learning
│   ├── Model Evaluation
│   └── Data Mining
├── Deep Learning
│   ├── Neural Networks
│   ├── TensorFlow
│   └── PyTorch
└── Deployment
    ├── Docker
    ├── AWS
    └── CI/CD
```

## /tests

For missing skills, generate tests/quizzes.

Example:

```text
Missing skill: SQL

Questions:
1. Difference between INNER JOIN and LEFT JOIN?
2. Write a query to find duplicate records.
3. Explain indexing.
```

Purpose:

```text
Do not just tell users what they lack.
Help them prove/improve those skills.
```

---

# Important Design Principle

The project should not claim that the graph alone determines the best candidate.

Better framing:

```text
The skill graph creates a semantic shortlist.
The evidence layer checks whether the candidate actually used those skills.
The final score combines skill match, role-domain alignment, and evidence of practical experience.
```

That is much more realistic.

---

# Current Best Next Step

In the new chat, continue from here:

```text
Update build_vectors_and_graph.py with:
1. DOMAIN_HINTS
2. infer_dynamic_domain_weights()
3. dynamic_weighted_skill_coverage()
4. role_domain_alignment_score()
5. project_evidence_score()
6. shortlist_score + final_fit_score scoring loop

Update preprocess_tech.py:
1. Add professional_company_names into resume_text

Then rerun:
python preprocess_tech.py
python build_vectors_and_graph.py
python analyze_graph.py
```

Then inspect:

```text
Shortlist score stats
Final fit score stats
Top 5 candidates per job role
Whether role-domain alignment improves bad matches
Whether project_evidence_score is non-zero and useful
```

Final goal:

```text
Build a clean B2B candidate ranking system plus a candidate-facing skill improvement/testing platform.
```

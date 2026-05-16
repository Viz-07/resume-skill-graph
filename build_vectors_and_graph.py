from networkx.algorithms.traversal import breadth_first_search
import pandas as pd
import json
import ast
import numpy as np
import networkx as nx
from itertools import combinations
from sklearn.metrics.pairwise import cosine_similarity
from networkx.readwrite import json_graph


RESUME_CSV = "clean_tech_resume_dataset.csv"
JOB_CSV = "clean_tech_job_skill_dataset.csv"
TAXONOMY_JSON = "skill_taxonomy.json"

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
    "ml_frameworks_libraries": [
        "tensorflow",
        "pytorch",
        "scikit-learn",
        "keras",
        "opencv",
        "numpy",
        "pandas"
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


DOMAIN_WEIGHTS = {
    "programming_languages": 1.3,
    "machine_learning_ai": 1.5,
    "ml_frameworks_libraries": 1.4,
    "data_engineering_big_data": 1.3,
    "frontend": 1.2,
    "backend": 1.2,
    "databases": 1.2,
    "cloud_devops": 1.3,
    "mobile_development": 1.2,
    "networking_security": 1.1,
    "analytics_bi": 1.0,
    "software_engineering": 1.1
}


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

        # Look around the skill mention
        window_start = max(0, skill_pos - 80)
        window_end = min(len(text), skill_pos + 80)
        context_window = text[window_start:window_end]

        if any(verb in context_window for verb in ACTION_VERBS):
            evidence_count += 1

    return evidence_count / len(matched_skills)


def infer_dynamic_domain_weights(job_text, job_skills, skill_to_domain):
    """
    Infers domain importance from the job description itself.
    Uses explicit required skills + semantic keywords from the JD.
    """
    domain_hits = {domain: 0 for domain in set(skill_to_domain.values())}

    # 1. Explicit skill-domain hits
    for skill in job_skills:
        domain = skill_to_domain.get(skill)
        if domain:
            domain_hits[domain] += 2

    # 2. Semantic JD hint hits
    job_text = str(job_text).lower()

    for domain, hints in DOMAIN_HINTS.items():
        for hint in hints:
            if hint in job_text:
                domain_hits[domain] = domain_hits.get(domain, 0) + 1

    # 3. Convert hit counts to weights
    domain_weights = {}

    for domain, hits in domain_hits.items():
        # Base weight = 1.0
        # Max boost = 0.5
        boost = min(0.5, hits * 0.08)
        domain_weights[domain] = 1.0 + boost

    return domain_weights


def safe_parse_list(value):
    if isinstance(value, list):
        return value

    if pd.isna(value):
        return []

    try:
        parsed = ast.literal_eval(value)
        if isinstance(parsed, list):
            return parsed
    except Exception:
        return []

    return []


def load_taxonomy():
    with open(TAXONOMY_JSON, "r", encoding="utf-8") as f:
        taxonomy = json.load(f)

    skill_to_domain = {}
    canonical_skills = []

    for domain, skills in taxonomy.items():
        for skill in skills:
            skill = skill.lower().strip()
            canonical_skills.append(skill)
            skill_to_domain[skill] = domain

    canonical_skills = sorted(set(canonical_skills))
    return taxonomy, canonical_skills, skill_to_domain


def filter_to_taxonomy(skills, canonical_skill_set):
    return sorted(set([
        skill.lower().strip()
        for skill in skills
        if skill.lower().strip() in canonical_skill_set
    ]))


def make_vector(skills, skill_index):
    vector = np.zeros(len(skill_index), dtype=np.float32)

    for skill in skills:
        if skill in skill_index:
            vector[skill_index[skill]] = 1.0

    return vector


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


def role_domain_alignment_score(resume_skills, skill_to_domain, domain_weights):
    if not resume_skills:
        return 0.0

    # Use top 3 JD-inferred domains as important domains
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


def coverage_penalty(resume_skills, job_skills):
    """
    Penalizes tiny matches.
    A candidate matching 1 out of 1 skill should not automatically get 1.0
    if the extracted job skill set is too small.
    """
    resume_count = len(set(resume_skills))
    job_count = len(set(job_skills))

    if resume_count == 0 or job_count == 0:
        return 0.0

    # Cap reaches 1.0 only when there are enough skills to judge properly.
    resume_factor = min(resume_count / 5, 1.0)
    job_factor = min(job_count / 5, 1.0)

    return resume_factor * job_factor


def cosine_skill_score(resume_vector, job_vector):
    if resume_vector.sum() == 0 or job_vector.sum() == 0:
        return 0.0

    return float(cosine_similarity([resume_vector], [job_vector])[0][0])


def add_cooccurrence_edges(G, skills, source):
    skills = sorted(set(skills))

    for s1, s2 in combinations(skills, 2):
        if G.has_edge(s1, s2):
            G[s1][s2]["weight"] += 1
            G[s1][s2]["sources"].add(source)
        else:
            G.add_edge(s1, s2, weight=1, relation="co_occurs", sources={source})


def build_graph(resume_df, job_df, taxonomy, canonical_skills, skill_to_domain):
    G = nx.Graph()

    # Skill nodes
    for skill in canonical_skills:
        G.add_node(
            skill,
            node_type="skill",
            domain=skill_to_domain.get(skill, "unknown"),
        )

    # Domain nodes + taxonomy edges
    for domain, skills in taxonomy.items():
        G.add_node(domain, node_type="domain")

        for skill in skills:
            skill = skill.lower().strip()
            if skill in G:
                G.add_edge(
                    domain,
                    skill,
                    weight=3,
                    relation="belongs_to_domain",
                    sources={"taxonomy"},
                )

    # Resume co-occurrence
    for skills in resume_df["resume_skills_filtered"]:
        add_cooccurrence_edges(G, skills, "resume")

    # Job-required co-occurrence
    for skills in resume_df["job_skills_filtered"]:
        add_cooccurrence_edges(G, skills, "resume_job")

    # Job skill set co-occurrence
    for skills in job_df["job_skill_list_filtered"]:
        add_cooccurrence_edges(G, skills, "job_skill_set")

    # Convert sets to lists so JSON export works
    for u, v, data in G.edges(data=True):
        if isinstance(data.get("sources"), set):
            data["sources"] = sorted(data["sources"])

    return G


def prune_graph_edges(G, min_weight=20):
    edges_to_remove = []

    for u, v, data in G.edges(data=True):
        relation = data.get("relation")
        weight = data.get("weight", 0)

        # Keep taxonomy/domain edges always
        if relation == "belongs_to_domain":
            continue

        # Remove weak co-occurrence edges
        if relation == "co_occurs" and weight < min_weight:
            edges_to_remove.append((u, v))

    G.remove_edges_from(edges_to_remove)

    return G


def graph_similarity_score(G, resume_skills, job_skills):
    if not resume_skills or not job_skills:
        return 0.0

    all_scores = []

    for job_skill in job_skills:
        best = 0.0

        for resume_skill in resume_skills:
            if job_skill == resume_skill:
                best = max(best, 1.0)
                continue

            try:
                distance = nx.shortest_path_length(G, job_skill, resume_skill)

                if distance == 1:
                    score = 0.7
                elif distance == 2:
                    score = 0.4
                elif distance == 3:
                    score = 0.2
                else:
                    score = 0.0

                best = max(best, score)

            except (nx.NetworkXNoPath, nx.NodeNotFound):
                pass

        all_scores.append(best)

    return sum(all_scores) / len(all_scores)


def explain_candidate_match(G, resume_skills, job_skills):
    resume_set = set(resume_skills)
    job_set = set(job_skills)

    exact_matches = sorted(resume_set & job_set)
    missing_skills = sorted(job_set - resume_set)

    inferred_matches = []

    for missing_skill in missing_skills:
        best_related = None
        best_distance = None

        for resume_skill in resume_set:
            try:
                distance = nx.shortest_path_length(G, missing_skill, resume_skill)

                if distance <= 2:
                    if best_distance is None or distance < best_distance:
                        best_distance = distance
                        best_related = resume_skill

            except (nx.NetworkXNoPath, nx.NodeNotFound):
                continue

        if best_related:
            inferred_matches.append({
                "required_skill": missing_skill,
                "resume_skill": best_related,
                "distance": best_distance
            })

    return {
        "exact_matches": exact_matches,
        "missing_skills": missing_skills,
        "inferred_matches": inferred_matches
    }


def get_skill_gap(resume_skills, job_skills):
    return sorted(set(job_skills) - set(resume_skills))


def main():
    resume_df = pd.read_csv(RESUME_CSV)
    job_df = pd.read_csv(JOB_CSV)

    taxonomy, canonical_skills, skill_to_domain = load_taxonomy()
    canonical_skill_set = set(canonical_skills)
    skill_index = {skill: idx for idx, skill in enumerate(canonical_skills)}

    resume_df["resume_skills"] = resume_df["resume_skills"].apply(safe_parse_list)
    resume_df["job_required_skills"] = resume_df["job_required_skills"].apply(safe_parse_list)
    resume_df["related_job_skills"] = resume_df["related_job_skills"].apply(safe_parse_list)

    job_df["job_skill_list"] = job_df["job_skill_list"].apply(safe_parse_list)

    resume_df["resume_skills_filtered"] = resume_df["resume_skills"].apply(
        lambda skills: filter_to_taxonomy(skills, canonical_skill_set)
    )

    # combine required + related job skills
    resume_df["job_skills_filtered"] = resume_df.apply(
        lambda row: filter_to_taxonomy(
            row["job_required_skills"] + row["related_job_skills"],
            canonical_skill_set,
        ),
        axis=1,
    )

    job_df["job_skill_list_filtered"] = job_df["job_skill_list"].apply(
        lambda skills: filter_to_taxonomy(skills, canonical_skill_set)
    )

    G = build_graph(
        resume_df,
        job_df,
        taxonomy,
        canonical_skills,
        skill_to_domain,
    )

    G = prune_graph_edges(G, min_weight=50)

    resume_vectors = []
    job_vectors = []

    direct_scores = []
    cosine_scores = []
    graph_scores = []
    coverage_scores = []
    final_scores = []
    shortlist_scores = []
    role_alignment_scores = []
    project_evidence_scores = []
    fit_scores = []


    MIN_JOB_SKILLS = 2
    MIN_RESUME_SKILLS = 2

    for _, row in resume_df.iterrows():
        resume_skills = row["resume_skills_filtered"]
        job_skills = row["job_skills_filtered"]

        rv = make_vector(resume_skills, skill_index)
        jv = make_vector(job_skills, skill_index)

        if len(job_skills) < MIN_JOB_SKILLS or len(resume_skills) < MIN_RESUME_SKILLS:
            direct = 0.0
            cosine = 0.0
            graph = 0.0
            coverage = 0.0
            role_alignment = 0.0
            evidence = 0.0
            shortlist = 0.0
            fit = 0.0
        else:
            domain_weights = infer_dynamic_domain_weights(
                row["job_text"],
                job_skills,
                skill_to_domain
            )

            direct = dynamic_weighted_skill_coverage(
                resume_skills,
                job_skills,
                skill_to_domain,
                domain_weights
            )

            cosine = cosine_skill_score(rv, jv)
            graph = graph_similarity_score(G, resume_skills, job_skills)
            coverage = coverage_penalty(resume_skills, job_skills)

            shortlist = (
                0.60 * direct
                + 0.25 * cosine
                + 0.15 * graph
            ) * coverage

            role_alignment = role_domain_alignment_score(
                resume_skills,
                skill_to_domain,
                domain_weights
            )

            matched_skills = sorted(set(resume_skills) & set(job_skills))

            evidence = project_evidence_score(
                row["resume_text"],
                matched_skills
            )

            fit = (
                0.65 * shortlist
                + 0.20 * role_alignment
                + 0.15 * evidence
            )

        direct_scores.append(direct)
        cosine_scores.append(cosine)
        graph_scores.append(graph)
        coverage_scores.append(coverage)
        shortlist_scores.append(shortlist)
        role_alignment_scores.append(role_alignment)
        project_evidence_scores.append(evidence)
        fit_scores.append(fit)

    resume_df["direct_match"] = direct_scores
    resume_df["cosine_skill"] = cosine_scores
    resume_df["graph_similarity"] = graph_scores
    resume_df["coverage_penalty"] = coverage_scores
    resume_df["shortlist_score"] = shortlist_scores
    resume_df["role_domain_alignment"] = role_alignment_scores
    resume_df["project_evidence_score"] = project_evidence_scores
    resume_df["final_fit_score"] = fit_scores

    ranked_df = resume_df.sort_values("final_fit_score", ascending=False)

    ranked_df.to_csv(
        "ranked_tech_resumes.csv",
        index=False,
        encoding="utf-8",
    )

    with open("skill_vocab_final.json", "w", encoding="utf-8") as f:
        json.dump(canonical_skills, f, indent=2)

    graph_data = json_graph.node_link_data(G)

    with open("skill_graph.json", "w", encoding="utf-8") as f:
        json.dump(graph_data, f, indent=2)

    print("Saved:")
    print("- ranked_tech_resumes.csv")
    print("- skill_vocab_final.json")
    print("- skill_graph.json")

    with open("graph_summary.txt", "w", encoding="utf-8") as f:
        f.write("Graph summary:\n")
        f.write(f"Nodes: {G.number_of_nodes()}\n")
        f.write(f"Edges: {G.number_of_edges()}\n")

        f.write("\nShortlist score stats:\n")
        f.write(ranked_df["shortlist_score"].describe().to_string())
        f.write("\n")

        f.write("\nRole domain alignment stats:\n")
        f.write(ranked_df["role_domain_alignment"].describe().to_string())
        f.write("\n")

        f.write("\nProject evidence score stats:\n")
        f.write(ranked_df["project_evidence_score"].describe().to_string())
        f.write("\n")

        f.write("\nFinal score stats:\n")
        f.write(ranked_df["final_fit_score"].describe().to_string())
        f.write("\n")

        f.write("\nTop 5 candidates per job role:\n")

        for role, role_df in ranked_df.groupby("job_position_name"):
            role_top = (
                role_df.sort_values("final_fit_score", ascending=False)
                .head(5)
            )

            f.write("\n\n")
            f.write(f"{role}\n")

            f.write(
                role_top[
                    [
                    "job_position_name",
                    "resume_skills_filtered",
                    "job_skills_filtered",
                    "matched_score",
                    "direct_match",
                    "cosine_skill",
                    "graph_similarity",
                    "coverage_penalty",
                    "shortlist_score",
                    "role_domain_alignment",
                    "project_evidence_score",
                    "final_fit_score",
                ]
                ].to_string()
            )

            f.write("\n")

if __name__ == "__main__":
    main()
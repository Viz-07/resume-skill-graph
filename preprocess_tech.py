import pandas as pd
import ast
import re
import json
from collections import Counter


RESUME_DATA_PATH = "resume_data_for_ranking.csv"
JOB_SKILL_DATA_PATH = "job_skill_set.csv"


TECH_ROLES = [
    "Senior Software Engineer",
    "Machine Learning (ML) Engineer",
    "AI Engineer",
    "Database Administrator (DBA)",
    "System Administrator (Operation & Maintenance of Server, Storage & Service Desk System)",
    "Network Support Engineer",
    "Senior iOS Engineer",
    "Executive/ Sr. Executive -IT",
    "Intern (Generative AI Engineering - 2D/3D Image Generation)",
    "DevOps Engineer",
    "Data Engineer",
    "Full Stack Developer (Python,React js)",
    "Data Science Engineer",
]


NOISE_SKILLS = {
    "none",
    "n/a",
    "na",
    "[]",
    "[none]",
    "advanced",
    "intermediate",
    "user",

    # generic business/admin terms
    "sales",
    "marketing",
    "customer service",
    "clients",
    "client",
    "budget",
    "budgeting",
    "inventory",
    "materials",
    "contracts",
    "policies",
    "financial",
    "financial statements",
    "general ledger",
    "accounting",
    "sap",
    "quickbooks",

    # generic office tools
    "microsoft office",
    "microsoft office suite",
    "ms office",
    "word",
    "powerpoint",
    "outlook",
    "access",
    "office",

    # generic soft skills
    "communication",
    "collaboration",
    "team collaboration",
    "leadership",
    "problem solving",
    "project management",
    "time management",
    "attention to detail",
    "adaptability",
    "organizational skills",
    "interpersonal skills",

    # generic vague words
    "documentation",
    "research",
    "quality",
    "processes",
    "scheduling",
    "reporting",
    "troubleshooting",
    "safety"
}


SKILL_ALIASES = {
    "js": "javascript",
    "java script": "javascript",

    "reactjs": "react",
    "react.js": "react",
    "react js": "react",

    "nodejs": "node.js",
    "node": "node.js",

    "py": "python",
    "python programming": "python",

    "r programming": "r",

    "powerbi": "power bi",
    "power-bi": "power bi",

    "ms excel": "excel",
    "microsoft excel": "excel",

    "ms office": "microsoft office",
    "microsoft office suite": "microsoft office",

    "mysql database": "mysql",
    "nosql database": "nosql",

    "postgres": "postgresql",

    "mongo db": "mongodb",

    "sklearn": "scikit-learn",
    "scikit learn": "scikit-learn",
    "scikit-learn.": "scikit-learn",

    "tensorflow.": "tensorflow",
    "pytorch.": "pytorch",

    "natural language processing": "nlp",
    "natural learning processing": "nlp",
    "ml/nlp": "nlp",

    "machine learning": "machine learning",
    "ml": "machine learning",

    "ai": "artificial intelligence",
    "artificial intelligence": "artificial intelligence",

    "deep learning": "deep learning",
    "computer vision": "computer vision",

    "data analytics": "data analysis",
    "data visualisation": "data visualization",

    "dbms": "database management",
    "rdbms": "relational database",

    "amazon redshift": "redshift",

    "microsoft azure": "azure",
    "google cloud": "gcp",

    "rest": "rest api",
    "restful api": "rest api",

    "ci cd": "ci/cd",
    "cicd": "ci/cd",

    "k8s": "kubernetes",

    "hdfs": "hadoop",
    "mapreduce": "hadoop",
    "yarn": "hadoop",

    "r or java": "java",

    "ios application development": "ios development",
    "ios app developer": "ios development",
    "mobile apps developer ios": "ios development",
    "native ios": "ios development",

    "swift ios": "swift",
    "swift ui": "swift ui",

    "asp.net mvc strong understanding of database design": "asp.net",

    "database administrator dba": "database administrator",
    "dba": "database administrator",

    "operation & maintenance of server": "system administration",

    "hardware & networking": "networking",

    "ccna cisco certified network associate": "ccna",

    "auto cad 2d 3d": "autocad"
}


def clean_text(value):
    if pd.isna(value):
        return ""

    value = str(value).lower()
    value = value.replace("\n", " ")
    value = value.replace("\t", " ")

    # keep useful programming symbols
    value = re.sub(r"[^a-z0-9+#./&\s-]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()

    return value


def normalize_skill(skill):
    skill = clean_text(skill)

    # remove bullets and extra punctuation
    skill = skill.replace("•", "")
    skill = skill.strip(" .,-:;")

    if skill in SKILL_ALIASES:
        skill = SKILL_ALIASES[skill]

    return skill


def parse_list_like(value):
    if pd.isna(value):
        return []

    value = str(value).strip()

    if not value:
        return []

    try:
        parsed = ast.literal_eval(value)

        # handles ['Python', 'SQL']
        if isinstance(parsed, list):
            flattened = []

            for item in parsed:
                if isinstance(item, list):
                    flattened.extend(item)
                else:
                    flattened.append(item)

            return [
                normalize_skill(x)
                for x in flattened
                if normalize_skill(x) and normalize_skill(x) not in NOISE_SKILLS
            ]

    except Exception:
        pass

    # fallback for plain multiline strings
    parts = re.split(r",|;|\||\n", value)

    return [
        normalize_skill(p)
        for p in parts
        if normalize_skill(p) and normalize_skill(p) not in NOISE_SKILLS
    ]


def combine_text_columns(df, columns):
    existing = [col for col in columns if col in df.columns]
    return df[existing].fillna("").astype(str).agg(" ".join, axis=1).apply(clean_text)


def build_initial_vocab(resume_df, job_df, min_freq=20):
    counter = Counter()

    for col in ["resume_skills", "job_required_skills", "related_job_skills"]:
        for skills in resume_df[col]:
            counter.update(skills)

    for skills in job_df["job_skill_list"]:
        counter.update(skills)

    vocab = sorted([
        skill
        for skill, count in counter.items()
        if count >= min_freq and skill not in NOISE_SKILLS and len(skill) > 1
    ])

    return vocab, counter


def main():
    resume_df = pd.read_csv(RESUME_DATA_PATH)
    job_df = pd.read_csv(JOB_SKILL_DATA_PATH)

    # 1. Filter resume dataset to tech-related roles
    tech_resume_df = resume_df[
        resume_df["job_position_name"].isin(TECH_ROLES)
    ].copy()

    # 2. Filter job-skill dataset to IT category
    tech_job_df = job_df[
        job_df["category"].str.upper().eq("INFORMATION-TECHNOLOGY")
    ].copy()

    # 3. Parse structured skill columns
    tech_resume_df["resume_skills"] = tech_resume_df["skills"].apply(parse_list_like)
    tech_resume_df["job_required_skills"] = tech_resume_df["skills_required"].apply(parse_list_like)
    tech_resume_df["related_job_skills"] = tech_resume_df["related_skils_in_job"].apply(parse_list_like)

    tech_job_df["job_skill_list"] = tech_job_df["job_skill_set"].apply(parse_list_like)

    # 4. Create combined text fields
    tech_resume_df["resume_text"] = combine_text_columns(
        tech_resume_df,
        [
            "career_objective",
            "skills",
            "certification_skills",
            "positions",
            "responsibilities",
            "professional_company_names",
            "degree_names",
            "major_field_of_studies"
        ],
    )

    tech_resume_df["job_text"] = combine_text_columns(
        tech_resume_df,
        [
            "job_position_name",
            "skills_required",
            "related_skils_in_job",
            "responsibilities.1",
            "educationaL_requirements",
            "experiencere_requirement",
        ],
    )

    tech_job_df["job_text"] = combine_text_columns(
        tech_job_df,
        [
            "category",
            "job_title",
            "job_description",
            "job_skill_set",
        ],
    )

    # 5. Numeric score
    tech_resume_df["matched_score"] = pd.to_numeric(
        tech_resume_df["matched_score"],
        errors="coerce",
    )

    # 6. Build preliminary vocabulary
    vocab, counter = build_initial_vocab(tech_resume_df, tech_job_df, min_freq=20)

    # 7. Save outputs
    output_resume_cols = [
        "job_position_name",
        "resume_text",
        "job_text",
        "resume_skills",
        "job_required_skills",
        "related_job_skills",
        "matched_score",
    ]

    output_job_cols = [
        "category",
        "job_title",
        "job_text",
        "job_skill_list",
    ]

    tech_resume_df[output_resume_cols].to_csv(
        "clean_tech_resume_dataset.csv",
        index=False,
        encoding="utf-8",
    )

    tech_job_df[output_job_cols].to_csv(
        "clean_tech_job_skill_dataset.csv",
        index=False,
        encoding="utf-8",
    )

    with open("initial_skill_vocab.json", "w", encoding="utf-8") as f:
        json.dump(vocab, f, indent=2)

    with open("skill_frequency.json", "w", encoding="utf-8") as f:
        json.dump(dict(counter.most_common()), f, indent=2)

    print("Saved:")
    print("- clean_tech_resume_dataset.csv")
    print("- clean_tech_job_skill_dataset.csv")
    print("- initial_skill_vocab.json")
    print("- skill_frequency.json")

    print("\nOriginal resume rows:", len(resume_df))
    print("Tech resume rows:", len(tech_resume_df))

    print("\nOriginal job skill rows:", len(job_df))
    print("Tech job skill rows:", len(tech_job_df))

    print("\nVocabulary size:", len(vocab))
    print("\nTop 50 skills:")
    for skill, count in counter.most_common(50):
        print(f"{skill}: {count}")


if __name__ == "__main__":
    main()
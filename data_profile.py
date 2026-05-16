import pandas as pd
import ast
import re
from collections import Counter

RESUME_DATA_PATH = "resume_data_for_ranking.csv"
JOB_SKILL_DATA_PATH = "job_skill_set.csv"


def load_data():
    resume_df = pd.read_csv(RESUME_DATA_PATH)
    job_df = pd.read_csv(JOB_SKILL_DATA_PATH)

    return resume_df, job_df


def basic_profile(df, name, file=None):
    print(f"DATASET: {name}", file=file)

    print("\nShape:", file=file)
    print(df.shape, file=file)

    print("\nColumns:", file=file)
    print(df.columns.tolist(), file=file)

    print("\nData types:", file=file)
    print(df.dtypes, file=file)

    print("\nMissing values:", file=file)
    missing = df.isnull().sum().sort_values(ascending=False)
    print(missing[missing > 0], file=file)

    print("\nDuplicate rows:", file=file)
    print(df.duplicated().sum(), file=file)

    print("\nSample rows:", file=file)
    print(df.head(3).to_string(), file=file)


def column_text_stats(df, columns, name, file=None):
    print(f"TEXT COLUMN STATS: {name}", file=file)

    for col in columns:
        if col not in df.columns:
            continue

        print(f"\nColumn: {col}", file=file)

        non_null = df[col].dropna()

        print("Non-null rows:", len(non_null), file=file)
        print("Unique values:", non_null.nunique(), file=file)

        lengths = non_null.astype(str).apply(len)

        print("Average text length:", round(lengths.mean(), 2), file=file)
        print("Median text length:", round(lengths.median(), 2), file=file)
        print("Max text length:", lengths.max(), file=file)

        print("Sample values:", file=file)

        for value in non_null.head(3):
            print(
                "-", 
                str(value)[:300].replace("\n", " "), 
                "...",
                file=file
            )


def parse_possible_list(value):
    """
    Some Kaggle columns store lists as strings:
    "['Python', 'SQL']"
    This function tries to convert them into Python lists.
    """
    if pd.isna(value):
        return []

    value = str(value).strip()

    if not value:
        return []

    try:
        parsed = ast.literal_eval(value)
        if isinstance(parsed, list):
            return [str(x).strip().lower() for x in parsed if str(x).strip()]
    except Exception:
        pass

    # fallback: split by common separators
    parts = re.split(r",|;|\||/|\n", value)
    return [p.strip().lower() for p in parts if p.strip()]


def skill_column_profile(df, columns, name, top_n=50, file=None):
    print(f"SKILL COLUMN PROFILE: {name}")

    for col in columns:
        if col not in df.columns:
            continue

        print(f"\nColumn: {col}", file=file)

        all_skills = []

        for value in df[col].dropna():
            skills = parse_possible_list(value)
            all_skills.extend(skills)

        counter = Counter(all_skills)

        print("Total extracted skill mentions:", len(all_skills), file=file)
        print("Unique extracted skills:", len(counter), file=file)

        print(f"\nTop {top_n} skills/items:", file=file)
        for skill, count in counter.most_common(top_n):
            print(f"{skill}: {count}", file=file)


def score_profile(df, file=None):
    print("MATCHED SCORE PROFILE", file=file)

    if "matched_score" not in df.columns:
        print("No matched_score column found.", file=file)
        return

    score = pd.to_numeric(df["matched_score"], errors="coerce")

    print(score.describe(), file=file)

    print("\nMissing matched_score:", score.isnull().sum(), file=file)

    print("\nScore value counts / buckets:", file=file)
    print(pd.cut(score, bins=10).value_counts().sort_index(), file=file)


def category_profile(df, columns, name, file=None):
    print(f"CATEGORY / ROLE PROFILE: {name}", file=file)

    for col in columns:
        if col not in df.columns:
            continue

        print(f"\nColumn: {col}", file=file)
        print(df[col].value_counts(dropna=False).head(30), file=file)


def save_clean_preview(resume_df, job_df):
    """
    Saves small preview files so we can inspect them easily.
    """
    resume_preview_cols = [
        "skills",
        "related_skils_in_job",
        "job_position_name",
        "skills_required",
        "matched_score",
        "career_objective",
        "responsibilities",
        "certification_skills",
        "positions",
    ]

    job_preview_cols = [
        "category",
        "job_title",
        "job_description",
        "job_skill_set",
    ]

    resume_existing = [c for c in resume_preview_cols if c in resume_df.columns]
    job_existing = [c for c in job_preview_cols if c in job_df.columns]

    resume_df[resume_existing].head(100).to_csv(
        "resume_dataset_preview.csv",
        index=False,
        encoding="utf-8"
    )

    job_df[job_existing].head(100).to_csv(
        "job_skill_dataset_preview.csv",
        index=False,
        encoding="utf-8"
    )

    print("\nSaved preview files:")
    print("- resume_dataset_preview.csv")
    print("- job_skill_dataset_preview.csv")


def main():
    resume_df, job_df = load_data()

    with open("dataset_analysis.txt", "w", encoding="utf-8") as f:

        basic_profile(
            resume_df,
            "Resume Ranking Dataset",
            file=f
        )

        basic_profile(
            job_df,
            "Job Skill Set Dataset",
            file=f
        )

        column_text_stats(
            resume_df,
            columns=[
                "skills",
                "related_skils_in_job",
                "skills_required",
                "career_objective",
                "responsibilities",
                "certification_skills",
                "positions",
                "job_position_name",
            ],
            name="Resume Ranking Dataset",
            file=f
        )

        column_text_stats(
            job_df,
            columns=[
                "category",
                "job_title",
                "job_description",
                "job_skill_set",
            ],
            name="Job Skill Set Dataset",
            file=f
        )

        skill_column_profile(
            resume_df,
            columns=[
                "skills",
                "related_skils_in_job",
                "skills_required",
                "certification_skills",
            ],
            name="Resume Ranking Dataset",
            file=f
        )

        skill_column_profile(
            job_df,
            columns=[
                "job_skill_set",
                "category",
            ],
            name="Job Skill Set Dataset",
            file=f
        )

        score_profile(
            resume_df,
            file=f
        )

        category_profile(
            resume_df,
            columns=[
                "job_position_name",
                "positions",
                "degree_names",
                "major_field_of_studies",
            ],
            name="Resume Ranking Dataset",
            file=f
        )

        category_profile(
            job_df,
            columns=[
                "category",
                "job_title",
            ],
            name="Job Skill Set Dataset",
            file=f
        )

    save_clean_preview(resume_df, job_df)


if __name__ == "__main__":
    main()
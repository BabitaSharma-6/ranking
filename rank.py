import streamlit as st
import pandas as pd
import spacy
import pdfplumber
import docx
import nltk
from nltk.tokenize import word_tokenize

# Load NLP model
nlp = spacy.load("en_core_web_sm")

# Function to extract text from resume
def extract_text(file):
    text = ""
    if file.name.endswith(".pdf"):
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                extracted_text = page.extract_text()
                if extracted_text:
                    text += extracted_text + " "
    elif file.name.endswith(".docx"):
        doc = docx.Document(file)
        for para in doc.paragraphs:
            text += para.text + " "
    return text.strip()

# Function to process text and extract relevant details
def extract_details(text):
    if not text:
        return 0, "Unknown", 0, "No skills found"

    doc = nlp(text)
    words = word_tokenize(text)

    # Extract experience (Years mentioned in text)
    experience = sum([int(word) for word in words if word.isdigit() and int(word) <= 50])

    # Extract skills (Nouns assumed as skills)
    skills = ", ".join(set([token.text.lower() for token in doc if token.pos_ == "NOUN"]))

    # Extract education (Finding common education keywords)
    education_keywords = ["bachelor", "master", "phd", "mba", "bsc", "msc", "engineering"]
    education = next((token.text for token in doc if token.text.lower() in education_keywords), "Unknown")

    # Extract passing year (Last 4-digit number in the text)
    years = [int(word) for word in words if word.isdigit() and len(word) == 4 and 1950 <= int(word) <= 2025]
    passing_year = max(years) if years else 0

    return experience, education, passing_year, skills if skills else "No skills found"

# Function to rank resumes based on filters
def rank_resumes(df, filters):
    scores = []

    for _, row in df.iterrows():
        score = 0

        # Ensure numeric values are not None
        experience = row["Experience"] if pd.notna(row["Experience"]) else 0
        salary = row["Salary"] if pd.notna(row["Salary"]) else 0
        passing_year = row["Passing Year"] if pd.notna(row["Passing Year"]) else 0

        # Apply ranking criteria
        if filters["experience"] <= experience:
            score += 1
        if filters["education"].lower() in row["Education"].lower():
            score += 1
        if filters["salary"] <= salary:
            score += 1
        if filters["passing_year"] <= passing_year:
            score += 1

        scores.append(score)

    df["Score"] = scores

    # Sorting based on filters
    if filters["sort_by"] == "Name":
        df = df.sort_values(by="Name", ascending=True)
    elif filters["sort_by"] == "Experience":
        df = df.sort_values(by="Experience", ascending=False)
    elif filters["sort_by"] == "Passing Year":
        df = df.sort_values(by="Passing Year", ascending=False)

    return df

# Streamlit UI
def main():
    st.set_page_config(page_title="Resume Genics")
    st.title("AI-Powered Resume Ranking System")

    uploaded_files = st.file_uploader("Upload Resumes (PDF/DOCX)", type=["pdf", "docx"], accept_multiple_files=True)

    if uploaded_files:
        data = []

        for file in uploaded_files:
            text = extract_text(file)
            experience, education, passing_year, skills = extract_details(text)
            
            # Salary is randomly assigned for now (you can extract it from the text later)
            salary = experience * 5000  # Approximate salary based on experience

            data.append({
                "Name": file.name,
                "Experience": experience,
                "Education": education,
                "Passing Year": passing_year,
                "Salary": salary,
                "Skills": skills
            })

        # Create DataFrame
        df = pd.DataFrame(data, columns=["Name", "Experience", "Education", "Passing Year", "Salary", "Skills"])

        # Filters for ranking
        st.subheader("Set Filters for Ranking")
        filters = {
            "experience": st.number_input("Minimum Experience (years)", 0, 50, 1),
            "education": st.text_input("Required Education (e.g., Bachelor, Master, PhD)", ""),
            "passing_year": st.number_input("Minimum Passing Year", 1950, 2025, 2015),
            "salary": st.number_input("Minimum Salary (per month)", 0, 100000, 50000),
            "sort_by": st.selectbox("Sort Resumes By", ["Score", "Name", "Experience", "Passing Year"])
        }

        if st.button("Rank Resumes"):
            ranked_resumes = rank_resumes(df, filters)
            st.subheader("Ranked Resumes")
            st.dataframe(ranked_resumes)

if __name__ == "__main__":
    main()

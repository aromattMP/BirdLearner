import streamlit as st
import pandas as pd
import os
import random

# === CONFIG ===
st.set_page_config(page_title="Bird Learner", layout="centered")

# === LOAD MASTER DATA ===
@st.cache_data
def load_master_birds():
    df = pd.read_csv("Victoria Falls Birding.csv")
    df.columns = df.columns.str.strip()
    return df

def load_or_create_user_progress(username, master_df):
    filename = f"progress_{username}.csv"
    if os.path.exists(filename):
        user_df = pd.read_csv(filename)
    else:
        user_df = master_df.copy()
        user_df["familiar"] = False
        user_df.to_csv(filename, index=False)
    return user_df

def save_user_progress(username, df):
    df.to_csv(f"progress_{username}.csv", index=False)

def get_image_path(bird_name):
    base_folder = "bird_images/Zipped"
    filename = f"{bird_name}.jpg"
    path = os.path.join(base_folder, filename)
    return path if os.path.exists(path) else None

# === USER LOGIN ===
st.title("🐦 Bird Learner")

username = st.text_input("Enter your name:", value="", placeholder="e.g. matt")
if not username:
    st.stop()

# === LOAD USER DATA ===
master_df = load_master_birds()
birds_df = load_or_create_user_progress(username, master_df)

# === SESSION STATE SETUP ===
if "shuffled_order" not in st.session_state:
    shuffled = list(range(len(birds_df)))
    random.shuffle(shuffled)
    st.session_state.shuffled_order = shuffled
    st.session_state.index = 0

if "quiz_state" not in st.session_state:
    st.session_state.quiz_state = {
        "question_bird": None,
        "options": [],
        "answer": None,
        "user_choice": None,
        "answered": False
    }

if "flashcard_bird" not in st.session_state:
    st.session_state.flashcard_bird = None
if "flashcard_reveal" not in st.session_state:
    st.session_state.flashcard_reveal = False

# === MODE SELECTOR ===
mode = st.selectbox("Choose mode", ["Normal", "One of Four", "Flashcard"])

# === NORMAL MODE ===
if mode == "Normal":
    shuffled_index = st.session_state.shuffled_order[st.session_state.index]
    bird = birds_df.iloc[shuffled_index]
    image_path = get_image_path(bird["English"])

    st.subheader(f"{bird['English']} / {bird['Afrikaans']}")

    if image_path:
        st.image(image_path, width=600)
    else:
        st.warning("No image found for this bird.")

    familiar_key = f"familiar_{shuffled_index}"
    familiar_state = st.checkbox("Mark as familiar", value=bird["familiar"], key=familiar_key)

    # Save familiar state
    birds_df.at[shuffled_index, "familiar"] = familiar_state
    save_user_progress(username, birds_df)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Previous"):
            st.session_state.index = (st.session_state.index - 1) % len(birds_df)
    with col2:
        if st.button("Next ➡️"):
            st.session_state.index = (st.session_state.index + 1) % len(birds_df)

    progress = birds_df["familiar"].sum()
    st.progress(progress / len(birds_df))
    st.caption(f"{progress} of {len(birds_df)} birds marked as familiar")

# === ONE OF FOUR MODE ===
elif mode == "One of Four":
    st.header("🧠 One of Four Quiz")

    quiz = st.session_state.quiz_state

    if quiz["question_bird"] is None or st.button("New Question"):
        question_bird = birds_df.sample(1).iloc[0]
        correct_name = question_bird["English"]
        other_choices = birds_df[birds_df["English"] != correct_name].sample(3)["English"].tolist()
        options = other_choices + [correct_name]
        random.shuffle(options)

        quiz.update({
            "question_bird": question_bird,
            "options": options,
            "answer": correct_name,
            "user_choice": None,
            "answered": False
        })

    image_path = get_image_path(quiz["answer"])
    if image_path:
        st.image(image_path, width=600)
    else:
        st.warning("No image found for this bird.")

    choice = st.radio("What bird is this?", quiz["options"], index=None, key="quiz_choice")

    if st.button("Check Answer"):
        if choice:
            quiz["user_choice"] = choice
            quiz["answered"] = True
            st.session_state.quiz_state = quiz
        else:
            st.warning("Please select an answer before checking.")

    if quiz["answered"]:
        if quiz["user_choice"] == quiz["answer"]:
            st.success("✅ Correct!")
        else:
            st.error(f"❌ Incorrect. The correct answer was: **{quiz['answer']}**")

# === FLASHCARD MODE ===
elif mode == "Flashcard":
    st.header("📸 Flashcard Mode")

    if st.session_state.flashcard_bird is None or st.button("Next Flashcard"):
        st.session_state.flashcard_bird = birds_df.sample(1).iloc[0]
        st.session_state.flashcard_reveal = False

    bird = st.session_state.flashcard_bird
    image_path = get_image_path(bird["English"])

    if image_path:
        st.image(image_path, width=600)
    else:
        st.warning("No image found for this bird.")

    if not st.session_state.flashcard_reveal:
        if st.button("Reveal Name"):
            st.session_state.flashcard_reveal = True

    if st.session_state.flashcard_reveal:
        st.markdown(f"**{bird['English']} / {bird['Afrikaans']}**")

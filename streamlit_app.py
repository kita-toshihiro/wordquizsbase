import streamlit as st
import pandas as pd
import sqlite3
import os
import random

# --- データベース設定 ---
def init_db():
    conn = sqlite3.connect('vocab_app.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS words 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, word TEXT, mean TEXT, level INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS records 
                 (word_id INTEGER, is_correct INTEGER, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    if os.path.exists('words.csv'):
        c.execute("SELECT count(*) FROM words")
        if c.fetchone()[0] == 0:
            df_csv = pd.read_csv('words.csv')
            df_csv.to_sql('words', conn, if_exists='append', index=False)
    conn.commit()
    return conn

conn = init_db()

def get_words(mode='all'):
    if mode == 'review':
        query = """
        SELECT DISTINCT w.id, w.word, w.mean 
        FROM words w 
        JOIN records r ON w.id = r.word_id 
        WHERE r.is_correct = 0
        """
    else:
        query = "SELECT id, word, mean FROM words"
    return pd.read_sql(query, conn)

def save_record(word_id, is_correct):
    c = conn.cursor()
    c.execute("INSERT INTO records (word_id, is_correct) VALUES (?, ?)", (int(word_id), is_correct))
    conn.commit()

# --- クイズ用補助関数 ---
def prepare_quiz(df):
    """問題と選択肢を準備する"""
    if df.empty:
        return None
    
    # 正解を1つ選ぶ
    correct_row = df.sample(n=1).iloc[0]
    
    # ハズレの選択肢を全単語リストから3つ選ぶ
    all_meanings = pd.read_sql("SELECT mean FROM words", conn)['mean'].tolist()
    all_meanings.remove(correct_row['mean'])
    distractors = random.sample(all_meanings, 3)
    
    # 選択肢をシャッフル
    options = distractors + [correct_row['mean']]
    random.shuffle(options)
    
    return {
        "id": correct_row['id'],
        "word": correct_row['word'],
        "answer": correct_row['mean'],
        "options": options
    }

# --- UI部分 ---
st.set_page_config(page_title="TOEIC 600点 4択クイズ", layout="centered")
st.title("🎓 TOEIC 600点 4択マスター")

menu = st.sidebar.radio("メニュー", ["クイズに挑戦", "復習モード", "学習記録"])

if menu in ["クイズに挑戦", "復習モード"]:
    df_pool = get_words(mode='all' if menu == "クイズに挑戦" else 'review')
    
    if df_pool.empty:
        st.warning("対象となる単語がありません。")
    else:
        # 新しい問題をセット
        if 'quiz_data' not in st.session_state:
            st.session_state.quiz_data = prepare_quiz(df_pool)
            st.session_state.answered = False
            st.session_state.feedback = None

        quiz = st.session_state.quiz_data

        st.info(f"現在のモード: {menu}")
        st.markdown(f"### Q: **{quiz['word']}**")
        st.write("意味を次の中から選んでください：")

        # 4択ボタンの作成
        for option in quiz['options']:
            if st.button(option, key=option, use_container_width=True, disabled=st.session_state.answered):
                st.session_state.answered = True
                if option == quiz['answer']:
                    st.session_state.feedback = ("correct", f"⭕️ 正解！: {quiz['answer']}")
                    save_record(quiz['id'], 1)
                else:
                    st.session_state.feedback = ("error", f"❌ 不正解... 正解は: {quiz['answer']}")
                    save_record(quiz['id'], 0)

        # フィードバック表示
        if st.session_state.answered:
            type, msg = st.session_state.feedback
            if type == "correct": st.success(msg)
            else: st.error(msg)
            
            if st.button("次の問題へ ➡️"):
                del st.session_state.quiz_data
                del st.session_state.answered
                del st.session_state.feedback
                st.rerun()

elif menu == "学習記録":
    st.subheader("📊 苦手な単語ランキング")
    query = """
    SELECT w.word, w.mean, 
           COUNT(*) as '間違い回数'
    FROM records r 
    JOIN words w ON r.word_id = w.id
    WHERE r.is_correct = 0
    GROUP BY w.id
    ORDER BY COUNT(*) DESC
    """
    history_df = pd.read_sql(query, conn)
    if history_df.empty:
        st.write("まだ記録がありません。クイズを解いてみましょう！")
    else:
        st.table(history_df.head(15))

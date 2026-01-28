import streamlit as st
import pandas as pd
from supabase import create_client, Client
import random
import os

# --- Supabase接続設定 ---
@st.cache_resource
def get_supabase_client():
    #url = st.secrets["SUPABASE_URL"]
    #key = st.secrets["SUPABASE_KEY"]
    
    import os
    # 環境変数から取得（設定されていない場合は None が返る）
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    return create_client(url, key)

supabase = get_supabase_client()

# --- データベース初期化（CSVインポート） ---
def init_supabase_data():
    # テーブルが空かどうか確認
    res = supabase.table("words").select("id", count="exact").limit(1).execute()
    
    # 既存データが0件かつCSVファイルが存在する場合に実行
    if (res.count == 0 or len(res.data) == 0) and os.path.exists('words.csv'):
        df_csv = pd.read_csv('words.csv')
        
        # Supabaseは一度に大量のデータを送ると制限に掛かることがあるため
        # 辞書形式のリストに変換して一括挿入
        data_to_insert = df_csv.to_dict(orient='records')
        
        with st.spinner('データベースに単語をインポート中...'):
            # 100件ずつ分割して挿入（安全策）
            chunk_size = 100
            for i in range(0, len(data_to_insert), chunk_size):
                chunk = data_to_insert[i:i + chunk_size]
                supabase.table("words").insert(chunk).execute()
        st.success(f"{len(data_to_insert)}件の単語をインポートしました！")

# アプリ起動時に実行
init_supabase_data()

# --- 以降、データ取得やUIの処理 ---
# (前回の回答と同じ get_words, save_record, prepare_quiz 関数...)

def get_words(mode='all'):
    if mode == 'review':
        # 不正解がある単語を結合して取得
        # 注意: Supabase(PostgREST)での複雑なJOINはRPCを使うか、全取得してpandasでフィルタリングが簡単です
        res = supabase.table("records").select("word_id, words(id, word, mean)").eq("is_correct", 0).execute()
        # 重複排除してDataFrame化
        data = [r['words'] for r in res.data if r.get('words')]
        df = pd.DataFrame(data).drop_duplicates()
    else:
        res = supabase.table("words").select("id, word, mean").execute()
        df = pd.DataFrame(res.data)
    return df

def save_record(word_id, is_correct):
    data = {"word_id": int(word_id), "is_correct": is_correct}
    supabase.table("records").insert(data).execute()

# --- クイズ用補助関数 ---
def prepare_quiz(df):
    if df.empty:
        return None
    
    correct_row = df.sample(n=1).iloc[0]
    
    # 全意味リストをSupabaseから取得して選択肢を作成
    all_res = supabase.table("words").select("mean").execute()
    all_meanings = [r['mean'] for r in all_res.data if r['mean'] != correct_row['mean']]
    
    distractors = random.sample(all_meanings, min(len(all_meanings), 3))
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
        if 'quiz_data' not in st.session_state:
            st.session_state.quiz_data = prepare_quiz(df_pool)
            st.session_state.answered = False
            st.session_state.feedback = None

        quiz = st.session_state.quiz_data

        st.info(f"現在のモード: {menu}")
        st.markdown(f"### Q: **{quiz['word']}**")
        
        for option in quiz['options']:
            if st.button(option, key=option, use_container_width=True, disabled=st.session_state.answered):
                st.session_state.answered = True
                if option == quiz['answer']:
                    st.session_state.feedback = ("success", f"⭕️ 正解！: {quiz['answer']}")
                    save_record(quiz['id'], 1)
                else:
                    st.session_state.feedback = ("error", f"❌ 不正解... 正解は: {quiz['answer']}")
                    save_record(quiz['id'], 0)

        if st.session_state.answered:
            ftype, msg = st.session_state.feedback
            if ftype == "success": st.success(msg)
            else: st.error(msg)
            
            if st.button("次の問題へ ➡️"):
                for key in ['quiz_data', 'answered', 'feedback']:
                    if key in st.session_state: del st.session_state[key]
                st.rerun()

elif menu == "学習記録":
    st.subheader("📊 苦手な単語ランキング")
    # Supabaseで集計クエリを実行（もしくは全件取得してpandasで集計）
    res = supabase.table("records").select("is_correct, words(word, mean)").eq("is_correct", 0).execute()
    
    if not res.data:
        st.write("まだ記録がありません。クイズを解いてみましょう！")
    else:
        # データのフラット化と集計
        flat_data = []
        for r in res.data:
            if r['words']:
                flat_data.append({"word": r['words']['word'], "mean": r['words']['mean']})
        
        history_df = pd.DataFrame(flat_data)
        if not history_df.empty:
            ranking = history_df.value_counts().reset_index(name='間違い回数')
            st.table(ranking.head(15))

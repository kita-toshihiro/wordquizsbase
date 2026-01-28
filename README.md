# 🎓 TOEIC 600点 4択マスター

Streamlit と Supabase を利用した、TOEIC 頻出単語の 4択クイズアプリです。
学習データはクラウド（Supabase）で管理されるため、進捗を永続的に記録し、苦手な単語を重点的に復習することが可能です。

## URL

https://wordquizsbase-z5jadxnmt4o.streamlit.app/

## 🚀 主な機能

* **自動データインポート**: `words.csv` が存在する場合、初回起動時に自動的に Supabase へ単語データを登録します。
* **4択クイズモード**: 全単語の中からランダムに出題。直感的なインターフェースで学習を進められます。
* **復習モード**: 過去に間違えたことがある単語のみを抽出して出題します。
* **学習記録（苦手ランキング）**: 間違えた回数が多い単語をランキング形式で表示し、自分の弱点を可視化します。

## 🛠 セットアップ

### 1. データベースの準備 (Supabase)

Supabase にプロジェクトを作成し、以下の 2 つのテーブルを作成してください。

**`words` テーブル**

* `id`: int8 (Primary Key, Auto Increment)
* `word`: text (単語名)
* `mean`: text (意味)

**`records` テーブル**

* `id`: int8 (Primary Key, Auto Increment)
* `word_id`: int8 (Foreign Key: `words.id`)
* `is_correct`: int8 (正解なら 1, 不正解なら 0)
* `created_at`: timestamptz (default: now())

### 2. 環境変数の設定

Streamlit のシークレット管理（`.streamlit/secrets.toml`）に以下の情報を設定します。

```toml
SUPABASE_URL = "あなたのSupabaseプロジェクトURL"
SUPABASE_KEY = "あなたのSupabase APIキー"

```

### 3. 単語データの用意

プロジェクトのルートディレクトリに `words.csv` を配置してください。
フォーマットは以下の通りです。

```csv
word,mean
apple,りんご
banana,バナナ
...

```

## 📦 インストールと実行

```bash
# ライブラリのインストール
pip install streamlit pandas supabase

# アプリの起動
streamlit run streamlit_app.py

```

## 📂 ファイル構成

* `streamlit_app.py`: アプリケーションのメインロジック
* `words.csv`: インポート用の単語データ（初回実行時のみ使用）
* `.streamlit/secrets.toml`: APIキーなどの機密情報

## 💡 技術スタック

* **Frontend/UI**: [Streamlit](https://streamlit.io/)
* **Database**: [Supabase](https://supabase.com/) (PostgreSQL)
* **Data Analysis**: Pandas

---

### 💡 今後のカスタマイズ案

* [ ] ユーザーログイン機能の実装（マルチユーザー対応）
* [ ] カテゴリ別（動詞、名詞、形容詞など）の出題機能
* [ ] 正解率のグラフ表示機能

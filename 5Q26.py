import streamlit as st
import pandas as pd
import random

# クイズデータを読み込む関数
def load_quizzes(file):
    df = pd.read_csv(file, encoding='utf-8')
    return df

# アプリケーションのタイトル
st.title('国家試験対策アプリ')

# セッション状態の初期化
if 'highlighted_questions' not in st.session_state:
    st.session_state.highlighted_questions = set()
if 'user_answers' not in st.session_state:
    st.session_state.user_answers = {}
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'total_questions' not in st.session_state:
    st.session_state.total_questions = 0
if 'percentage' not in st.session_state:
    st.session_state.percentage = 0
if 'shuffled_options' not in st.session_state:
    st.session_state.shuffled_options = {}

# ファイルアップロード
uploaded_file = st.file_uploader("クイズデータのCSVファイルをアップロードしてください", type="csv")

if uploaded_file is not None:
    # アップロードされたファイルを読み込む
    df = load_quizzes(uploaded_file)
    
    # 年と分類の選択肢を取得し、「すべて」を追加
    years = df['year'].unique().tolist()
    categories = df['category'].unique().tolist()
    
    # 「すべて」を含む選択肢を作成
    years = ['すべて'] + years
    categories = ['すべて'] + categories
    
    # ユーザーが「年」と「分類」を選択
    selected_years = st.multiselect('過去問を選択', years)
    selected_categories = st.multiselect('内容を選択', categories)

    # 年と分類の選択に応じてデータをフィルタリング
    if 'すべて' in selected_years and 'すべて' in selected_categories:
        filtered_df = df
    elif 'すべて' in selected_years:
        filtered_df = df[df['category'].isin(selected_categories)]
    elif 'すべて' in selected_categories:
        filtered_df = df[df['year'].isin(selected_years)]
    else:
        filtered_df = df[df['year'].isin(selected_years) & df['category'].isin(selected_categories)]
    
    # 内容カテゴリーで優先的に表示するためのソート
    if not filtered_df.empty:
        filtered_df = filtered_df.sort_values(by=['category'])
        quizzes = []
        for _, row in filtered_df.iterrows():
            options = [row[f"option{i}"] for i in range(1, 6) if pd.notna(row[f"option{i}"])]
            answers = [row[f"answer{i}"] for i in range(1, 6) if pd.notna(row[f"answer{i}"])]
            
            # シャッフルされた選択肢をセッション状態に保存
            if row["question"] not in st.session_state.shuffled_options:
                shuffled_options = options[:]
                random.shuffle(shuffled_options)
                st.session_state.shuffled_options[row["question"]] = shuffled_options

            quiz = {
                "question": row["question"],
                "type": row["type"],
                "options": st.session_state.shuffled_options[row["question"]],
                "answers": answers
            }
            quizzes.append(quiz)

        # クイズの表示とユーザー回答の収集
        for idx, quiz in enumerate(quizzes, start=1):
            # 問題番号のハイライト
            highlight = 'background-color: #fdd; padding: 10px;' if idx in st.session_state.highlighted_questions else ''
            st.markdown(f'<div style="{highlight}">問題{idx}</div>', unsafe_allow_html=True)

            # 問題文の表示
            st.markdown(f'<div>{quiz["question"]}</div>', unsafe_allow_html=True)

            # CSSで選択肢間隔を調整
            st.markdown(
                """
                <style>
                div[role='radiogroup'] {
                    margin-top: -20px;  /* 問題文と選択肢の間隔を完全に詰める */
                }
                div[role='radiogroup'] > label {
                    margin-bottom: 10px; /* 選択肢同士の間隔 */
                }
                </style>
                """,
                unsafe_allow_html=True
            )

            # 単一選択問題の処理
            if quiz["type"] == "single":
                user_selection = st.radio(
                    "",  # ラベルなし
                    quiz["options"],
                    key=f"{idx}_radio",
                    index=None  # 初期状態で何も選択されていない
                )
                st.session_state.user_answers[quiz["question"]] = user_selection  # 選択された答えをセッションに保存

            # 複数選択問題の処理
            elif quiz["type"] == "multiple":
                selected_options = st.session_state.user_answers.get(quiz["question"], [])
                for option in quiz["options"]:
                    checked = option in selected_options
                    if st.checkbox(option, key=f"{idx}_{option}", value=checked):
                        if option not in selected_options:
                            selected_options.append(option)
                    else:
                        if option in selected_options:
                            selected_options.remove(option)
                st.session_state.user_answers[quiz["question"]] = selected_options

            # 問題間のスペース
            st.markdown("<br>", unsafe_allow_html=True)

        # 回答ボタンを作成
        if st.button('回答'):
            correct_count = 0
            total_questions = len(quizzes)
            st.session_state.highlighted_questions.clear()  # ハイライトの初期化

            for idx, quiz in enumerate(quizzes, start=1):
                if quiz["type"] == "single":
                    user_answer = st.session_state.user_answers.get(quiz["question"])
                    is_correct = user_answer == quiz["answers"][0]
                    if is_correct:
                        correct_count += 1
                    else:
                        st.session_state.highlighted_questions.add(idx)  # 間違った問題番号をハイライト
                elif quiz["type"] == "multiple":
                    user_answers_options = set(st.session_state.user_answers.get(quiz["question"], []))
                    correct_answers = set(quiz["answers"])
                    is_correct = user_answers_options == correct_answers
                    if is_correct:
                        correct_count += 1
                    else:
                        st.session_state.highlighted_questions.add(idx)  # 間違った問題番号をハイライト

            # 成績の計算と表示
            st.session_state.score = correct_count
            st.session_state.total_questions = total_questions
            st.session_state.percentage = (correct_count / total_questions) * 100 if total_questions > 0 else 0
            
            st.write(f"成績: {st.session_state.score}/{st.session_state.total_questions} ({st.session_state.percentage:.2f}%)")

            # 不正解問題にハイライトボタンを表示
            if st.button('不正解問題にハイライト'):
                for idx in st.session_state.highlighted_questions:
                    st.markdown(f'<div style="background-color: #fdd; padding: 10px;">問題{idx}</div>', unsafe_allow_html=True)


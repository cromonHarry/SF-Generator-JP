# =======================================================
# 改良版SF生成器 - デモンストレーション特化版 (自動実行・高機能可視化版)
# =======================================================
import streamlit as st
import json
import re
import time
from openai import OpenAI
from tavily import TavilyClient
import concurrent.futures

# ========== Page Setup ==========
st.set_page_config(page_title="近未来SF生成器", layout="wide")

# ========== Client Initialization ==========
try:
    client = OpenAI(api_key=st.secrets["openai"]["api_key"])
    tavily_client = TavilyClient(api_key=st.secrets["tavily"]["api_key"])
except Exception:
    st.error("❌ APIキーが設定されていません。StreamlitのSecretsに `openai` と `tavily` のAPIキーを追加してください。")
    st.stop()


# ========== System Prompt & Constants (変更なし) ==========
SYSTEM_PROMPT = """君はサイエンスフィクションの専門家であり、「アーキオロジカル・プロトタイピング（Archaeological Prototyping, 以下AP）」モデルに基づいて社会を分析します。以下はこのモデルの紹介です。
APは、18の項目(6個の対象と12個射)によって構成される社会文化モデル(Sociocultural model)である。要するに、ある課題をテーマとして、社会や文化を18この要素に分割し、そのつながりを論理的に描写したモデルである。
このモデルは、有向グラフとしても考えることができます。6つの対象（前衛的社会問題、人々の価値観、社会問題、技術や資源、日常の空間とユーザー体験、制度）と12の射（メディア、コミュニティ化、文化芸術振興、標準化、コミュニケーション、組織化、意味付け、製品・サービス、習慣化、パラダイム、ビジネスエコシステム、アート（社会批評））で⼀世代の社会文化モデルを構成する。これらの対象と射のつながりは、以下の定義で示されます。

##対象
1. 前衛的社会問題: 技術や資源のパラダイムによって引き起こされる社会問題や日常生活が営まれる空間やそこでのユーザーの体験に対してアート(社会批評)を介して顕在化される社会問題。
2. 人々の価値観: 文化芸術振興を通して広められる前衛的社会問題や日常のコミュニケーションによって広められる制度で対応できない社会問題に共感する人々のありたい姿。この問題は誰もが認識しているのではなく、ある⼀部の先進的な/マイノリティの人々のみが認識する。具体的には、マクロの環境問題(気候・生態など)と人文環境問題(倫理・経済・衛生など)が含まれる。
3. 社会問題: 前衛的問題に取り組む先進的なコミュニティによって社会に認識される社会問題やメディアを介して暴露される制度で拘束された社会問題。社会において解決すべき対象として顕在化される。
4. 技術や資源: 日常生活のルーティンを円滑に機能させるために作られた制度のうち、標準化されて過去から制約を受ける技術や資源であり、社会問題を解決すべく組織化された組織(営利・非営利法人、法人格を持たない集団も含み、新規・既存を問わない)が持つ技術や資源。
5. 日常の空間とユーザー体験: 技術や資源を動員して開発された製品・サービスによって構成される物理的空間であり、その空間で製品・サービスに対してある価値観のもとでの意味づけを行い、それらを使用するユーザーの体験。価値観とユーザー体験の関係性は、例えば、 「AI エンジニアになりたい」という価値観を持った人々が、PC に対して「プログラミングを学習するためのもの」という意味づけを行い、 「プログラミング」という体験を行う、というようなものである。
6. 制度: ある価値観を持った人々が日常的に行う習慣をより円滑に行うために作られる制度や、日常の空間とユーザー体験を構成するビジネスを行う関係者(ビジネスエコシステム)がビジネスをより円滑に行うために作られる制度。具体的には、法律やガイドライン、業界標準、行政指導、モラルが挙げられる。

##射
1. メディア : 現代の制度的⽋陥を顕在化させるメディア。マスメディアやネットメディア等の主要なメディアに加え、情報発信を行う個人も含まれる。制度を社会問題に変換させる。(制度 -> 社会問題)
2. コミュニティ化: 前衛的な問題を認識する人々が集まってできるコミュニティ。公式か非公式かは問わない。前衛的社会問題を社会問題に変換させる。 (前衛的社会問題 -> 社会問題)
3. 文化芸術振興: アート(社会批評)が顕在化させた社会問題を作品として展⽰し、人々に伝える活動。前衛的社会問題を人々の価値観に変換させる。 (前衛的社会問題 -> 人々の価値観)
4. 標準化 : 制度の中でも、より広い関係者に影響を与えるために行われる制度の標準化。制度を新しい技術·資源に変換させる。 (制度 -> 技術·資源)
5. コミュニケーション: 社会問題をより多くの人々に伝えるためのコミュニケーション⼿段。例えば、近年は SNS を介して行われることが多い。社会問題を人々の価値観に変換させる。 (社会問題 -> 人々の価値観)
6. 組織化 : 社会問題を解決するために形成される組織。法人格の有無や新旧の組織かは問わず 、新しく生まれた社会問題に取り組む全ての組織。社会問題を新しい技術·資源に変換させる。 (社会問題 -> 技術·資源)
7. 意味付け : 人々が価値観に基づいて製品やサービスを使用する理由。人々の価値観を新しい日常の空間とユーザー体験に変換させる。 (人々の価値観 -> 日常の空間とユーザー体験)
8. 製品・サービス: 組織が保有する技術や資源を利用して創造する製品やサービス。技術·資源を日常の空間とユーザー体験に変換させる。 (技術·資源 -> 日常の空間とユーザー体験)
9. 習慣化 : 人々が価値観に基づいて行う習慣。人々の価値観を制度に変換させる。 (人々の価値観 -> 制度)
10. パラダイム : その時代の⽀配的な技術や資源として、次世代にも影響をもたらすもの。技術·資源を前衛的社会問題に変換させる。 (技術·資源 -> 前衛的社会問題)
11. ビジネスエコシステム: 日常の空間やユーザー体験を維持するために、構成する製品・サービスに関わる関係者が形成するネットワーク 。日常の空間とユーザー体験を制度に変換させる。 (日常の空間とユーザー体験 -> 制度)
12. アート(社会批評): 人々が気づかない問題を、主観的/内発的な視点で⾒る人の信念。日常の空間とユーザー体験に違和感を持ち、問題を提⽰する役割を持つ。日常の空間とユーザー体験を前衛的社会問題に変換させる。 (日常の空間とユーザー体験 -> 前衛的社会問題)

###Sカーブは、時間の経過に伴うテクノロジーの進化を表すモデルです。以下の3つの段階で構成され、各段階の説明は次のとおりです。
##第1段階：揺籃期: この段階では、技術開発は着実に進歩しますが、その進展は緩やかです。主として既存の問題解決や現行機能の改善に焦点が当てられます。この期間の終わりには、現在の問題が解決される一方で、新たな問題が発生します。
##第2段階：離陸期: この段階では、テクノロジーは急成長期に入ります。様々な革新的なアイデアが提案され、それらが最終的に組み合わさることで、全く新しい形の技術が生まれます。この期間の終わりには、テクノロジーは大きな発展を遂げますが、同時に新たな問題も引き起こします。
##第3段階：成熟期: この段階では、技術の発展は再び緩やかになります。前期で発生した問題を解決しつつ、テクノロジーはより安定的で成熟した状態へと進化していきます。
"""

AP_MODEL_STRUCTURE = {
    "対象": {
        "前衛的社会問題": "技術や資源のパラダイムによって引き起こされる社会問題", "人々の価値観": "先進的な人々が認識する価値観や理想",
        "社会問題": "社会で認識され解決すべき問題", "技術や資源": "問題解決のために組織化された技術や資源",
        "日常の空間とユーザー体験": "製品・サービスによる物理空間とユーザー体験", "制度": "習慣やビジネスを円滑にする制度や規則"
    },
    "射": {
        "メディア": {"from": "制度", "to": "社会問題", "説明": "制度の欠陥を暴露するメディア"},
        "コミュニティ化": {"from": "前衛的社会問題", "to": "社会問題", "説明": "前衛的問題に取り組むコミュニティ"},
        "文化芸術振興": {"from": "前衛的社会問題", "to": "人々の価値観", "説明": "アートを通した問題の展示・伝達"},
        "標準化": {"from": "制度", "to": "技術や資源", "説明": "制度の標準化による技術・資源化"},
        "コミュニケーション": {"from": "社会問題", "to": "人々の価値観", "説明": "SNS等による問題の伝達"},
        "組織化": {"from": "社会問題", "to": "技術や資源", "説明": "問題解決のための組織形成"},
        "意味付け": {"from": "人々の価値観", "to": "日常の空間とユーザー体験", "説明": "価値観に基づく製品・サービスの使用理由"},
        "製品・サービス": {"from": "技術や資源", "to": "日常の空間とユーザー体験", "説明": "技術を活用した製品・サービス創造"},
        "習慣化": {"from": "人々の価値観", "to": "制度", "説明": "価値観に基づく習慣の制度化"},
        "パラダイム": {"from": "技術や資源", "to": "前衛的社会問題", "説明": "支配的技術による新たな社会問題"},
        "ビジネスエコシステム": {"from": "日常の空間とユーザー体験", "to": "制度", "説明": "ビジネス関係者のネットワーク"},
        "アート(社会批評)": {"from": "日常の空間とユーザー体験", "to": "前衛的社会問題", "説明": "日常への違和感から問題を提示"}
    }
}


# ========== Helper Functions (変更なし) ==========
def parse_json_response(gpt_output: str) -> dict:
    result_str = gpt_output.strip()
    if result_str.startswith("```") and result_str.endswith("```"):
        result_str = re.sub(r'^```[^\n]*\n', '', result_str)
        result_str = re.sub(r'\n```$', '', result_str)
        result_str = result_str.strip()
    try:
        return json.loads(result_str)
    except Exception as e:
        st.error(f"JSON解析エラー: {e}")
        st.error(f"解析しようとした文字列: {result_str}")
        raise e

# ========== Stage 1: Tavily Functions (変更なし) ==========
def generate_question_for_object(product: str, object_name: str, object_description: str) -> str:
    prompt = f"""
{product}について、APモデルの対象「{object_name}」({object_description})に関する自然で完整な質問文を1つ生成してください。
質問は以下の条件を満たしてください：
- 完整な文として自然な日本語
- {product}に関連する具体的内容を調べる質問
- 検索エンジンで良い結果が得られそうな質問
質問のみを出力してください：
"""
    response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}], temperature=0)
    return response.choices[0].message.content.strip()

def generate_question_for_arrow(product: str, arrow_name: str, arrow_info: dict) -> str:
    prompt = f"""
{product}について、APモデルの射「{arrow_name}」に関する自然で完整な質問文を生成してください。
射の詳細：
- 起点：{arrow_info['from']}
- 終点：{arrow_info['to']}
- 説明：{arrow_info['説明']}
質問は以下の条件を満たしてください：
- 完整な文として自然な日本語
- {arrow_info['from']}から{arrow_info['to']}への変換関係を具体的に調べる質問
- {product}における具体的な事例や関係性を発見できる質問
質問のみを出力してください：
"""
    response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}], temperature=0)
    return response.choices[0].message.content.strip()

def search_and_get_answer(question: str) -> str:
    try:
        response = tavily_client.search(query=question, include_answer=True)
        answer = response.get('answer', '')
        if answer: return answer
        results = response.get('results', [])
        return results[0].get('content', "情報が見つかりませんでした") if results else "情報が見つかりませんでした"
    except Exception as e: return f"検索エラー: {str(e)}"

def build_ap_element(product: str, element_type: str, element_name: str, answer: str) -> dict:
    if element_type == "対象":
        prompt = f"""
{product}の{element_name}について、以下の情報からAP要素を構築してください：
情報: {answer}
以下のJSON形式で出力してください：
{{"type": "{element_name}", "definition": "具体的で簡潔な定義（100文字以内）", "example": "この対象に関する具体的な例"}}
"""
    else:
        arrow_info = AP_MODEL_STRUCTURE["射"][element_name]
        prompt = f"""
{product}の{element_name}（{arrow_info['from']} → {arrow_info['to']}）について、以下の情報からAP要素を構築してください：
情報: {answer}
以下のJSON形式で出力してください：
{{"source": "{arrow_info['from']}", "target": "{arrow_info['to']}", "type": "{element_name}", "definition": "具体的な変換関係の説明（100文字以内）", "example": "この射に関する具体的な例"}}
"""
    try:
        response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}], response_format={"type": "json_object"})
        return json.loads(response.choices[0].message.content.strip())
    except Exception: return None

def process_element(product: str, element_type: str, name: str, info: dict):
    try:
        if element_type == "対象":
            question = generate_question_for_object(product, name, info)
        else:
            question = generate_question_for_arrow(product, name, info)
        answer = search_and_get_answer(question)
        if "検索エラー" in answer or not answer:
            return None, None
        element_data = build_ap_element(product, element_type, name, answer)
        if not element_data:
            return None, None
        return {"type": element_type, "name": name, "data": element_data}, f"## {name}\n{answer}"
    except Exception as e:
        st.warning(f"要素「{name}」の処理中にエラーが発生しました: {e}")
        return None, None

def build_stage1_ap_with_tavily(product: str, status_container):
    ap_model = {"nodes": [], "arrows": []}
    all_answers = []
    MAX_WORKERS = 5
    tasks = []
    for name, desc in AP_MODEL_STRUCTURE["対象"].items():
        tasks.append((product, "対象", name, desc))
    for name, info in AP_MODEL_STRUCTURE["射"].items():
        tasks.append((product, "射", name, info))
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_task = {executor.submit(process_element, *task): task for task in tasks}
        for future in concurrent.futures.as_completed(future_to_task):
            task_name = future_to_task[future][2]
            status_container.write(f"  - 要素「{task_name}」を並列処理中...")
            result, answer_text = future.result()
            if result:
                if result["type"] == "対象": ap_model["nodes"].append(result["data"])
                else: ap_model["arrows"].append(result["data"])
            if answer_text: all_answers.append(answer_text)
    
    status_container.write("紹介文を生成中...")
    intro_prompt = f"以下の{product}に関する様々な側面からの情報をもとに、{product}がどのようなものか、100字以内の日本語で簡潔に紹介文を作成してください。\n### 収集された情報:\n{''.join(all_answers)}"
    response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": intro_prompt}], temperature=0)
    introduction = response.choices[0].message.content
    return introduction, ap_model

# ========== Stage 2 & 3: Multi-Agent Functions (変更なし) ==========
def generate_agents(topic: str) -> list:
    prompt = f"""
テーマ「{topic}」について、APモデルの要素生成を行う3つの完全に異なる専門性を持つエージェントを生成してください。
各エージェントは異なる視点と専門知識を持ち、創造的で革新的な未来予測を提供できる必要があります。
以下のJSON形式で出力してください：
{{ "agents": [ {{ "name": "エージェント名", "expertise": "専門分野", "personality": "性格・特徴", "perspective": "独特な視点" }} ] }}
"""
    response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}], response_format={"type": "json_object"})
    result = parse_json_response(response.choices[0].message.content)
    return result["agents"]

def agent_generate_element(agent: dict, topic: str, element_type: str, previous_stage_ap: dict, user_vision: str, context: dict, previous_proposals: list) -> str:
    context_info = ""
    if element_type == "日常の空間とユーザー体験": context_info = f"##新しい技術や資源:\n{context.get('技術や資源', '')}"
    elif element_type == "前衛的社会問題": context_info = f"##新しい技術や資源:\n{context.get('技術や資源', '')}\n##新しい日常の空間とユーザー体験:\n{context.get('日常の空間とユーザー体験', '')}"
    history_info = "\n##あなたの過去の提案（重複を避けてください）:\n" + "".join([f"提案{i+1}: {p}\n" for i, p in enumerate(previous_proposals)]) if previous_proposals else ""
    prompt = f"""
あなたは{agent['name']}として、{agent['expertise']}の専門知識と{agent['personality']}という特徴を持ち、{agent['perspective']}という独特な視点から分析を行います。
##テーマ: {topic}
##前段階のAPモデル:
{json.dumps(previous_stage_ap, ensure_ascii=False, indent=2)}
##ユーザーの未来構想:
{user_vision}
{context_info}
{history_info}
**重要**: 過去の提案と重複しないよう、新しい角度からの提案を行ってください。同じ内容や似たような提案は避け、あなたの専門性を活かした全く新しいアプローチを提示してください。
あなたの専門性と視点から、次段階における「{element_type}」の内容を創造的で革新的に生成してください。Sカーブ理論に基づき、前段階からの発展と新たな可能性を考慮し、あなたならではの独創的なアイデアを**提案内容のテキストのみで、200字以内で回答してください。JSON形式や余計な説明は不要です。**
"""
    response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}])
    return response.choices[0].message.content.strip()

def judge_element_proposals(proposals: list[dict], element_type: str, topic: str) -> dict:
    proposals_text = "".join([f"##提案{i+1} (エージェント: {p['agent_name']}):\n{p['proposal']}\n\n" for i, p in enumerate(proposals)])
    prompt = f"""
以下は「{topic}」の「{element_type}」に関する{len(proposals)}つの提案です。各提案を創造性、実現可能性、Sカーブ理論との整合性、未来的視点の観点から評価し、最も優れた提案を選択してください。
{proposals_text}
以下のJSON形式で出力してください：
{{ "selected_proposal": "選択された提案のエージェント名", "selected_content": "選択された{element_type}の提案内容", "selection_reason": "選択理由（150字以内）", "creativity_score": "創造性評価（1-10）", "feasibility_score": "実現可能性評価（1-10）", "future_vision_score": "未来的視点評価（1-10）" }}
"""
    response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}], response_format={"type": "json_object"})
    return parse_json_response(response.choices[0].message.content)

def final_judge_best_iteration_element(iteration_results: list, element_type: str, topic: str) -> dict:
    prompt = f"""
以下は「{topic}」の「{element_type}」生成における3回の反復結果です。各反復の改善効果を総合的に評価し、最も優れた案を最終選択してください。
##反復1の結果:
{json.dumps(iteration_results[0], ensure_ascii=False, indent=2)}
##反復2の結果:
{json.dumps(iteration_results[1], ensure_ascii=False, indent=2)}
##反復3の結果:
{json.dumps(iteration_results[2], ensure_ascii=False, indent=2)}
以下のJSON形式で出力してください：
{{ "final_selected_iteration": "選択された反復番号（1, 2, 3のいずれか）", "final_selection_reason": "最終選択理由（200字以内）", "final_selected_content": "最終選択された{element_type}の内容" }}
"""
    response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}], response_format={"type": "json_object"})
    return parse_json_response(response.choices[0].message.content)

def generate_single_element_with_iterations(status_container, topic: str, element_type: str, previous_stage_ap: dict, agents: list, user_vision: str, context: dict) -> dict:
    iteration_results = []
    agent_history = {agent['name']: [] for agent in agents}
    for iteration in range(1, 4):
        status_container.write(f"    - 反復 {iteration}/3: {len(agents)}人のエージェントが提案を同時生成中...")
        proposals = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(agents)) as executor:
            future_to_agent = {executor.submit(agent_generate_element, agent, topic, element_type, previous_stage_ap, user_vision, context, agent_history[agent['name']]): agent for agent in agents}
            for future in concurrent.futures.as_completed(future_to_agent):
                agent = future_to_agent[future]
                try:
                    proposal_content = future.result()
                    proposals.append({"agent_name": agent['name'], "proposal": proposal_content})
                    agent_history[agent['name']].append(proposal_content)
                except Exception as exc: st.warning(f"{agent['name']}の提案生成中にエラー: {exc}")
        if not proposals: continue
        status_container.write(f"    - 反復 {iteration}/3: 判定者による評価中...")
        judgment = judge_element_proposals(proposals, element_type, topic)
        iteration_results.append({"iteration_number": iteration, "all_agent_proposals": proposals, "judgment": judgment})
    if not iteration_results: return {"element_type": element_type, "error": "提案が生成されませんでした。"}
    status_container.write(f"  - 「{element_type}」の最終判定中...")
    final_judgment = final_judge_best_iteration_element(iteration_results, element_type, topic)
    return {"element_type": element_type, "iterations": iteration_results, "final_decision": final_judgment}

def build_complete_ap_model(topic: str, previous_ap: dict, new_elements: dict, stage: int, user_vision: str) -> dict:
    prompt = f"""
第{stage}段階のAPモデルを構築してください。
##前段階の情報:
{json.dumps(previous_ap, ensure_ascii=False, indent=2)}
##新たに生成された核心要素:
技術や資源: {new_elements["技術や資源"]}
日常の空間とユーザー体験: {new_elements["日常の空間とユーザー体験"]}
前衛的社会問題: {new_elements["前衛的社会問題"]}
##ユーザーの未来構想:
{user_vision}
**重要**：第{stage}段階では、必ず以下の6個の対象と12個の射すべてを含めてください：
対象: 前衛的社会問題、人々の価値観、社会問題、技術や資源、日常の空間とユーザー体験、制度
射: メディア、コミュニティ化、文化芸術振興、標準化、コミュニケーション、組織化、意味付け、製品・サービス、習慣化、パラダイム、ビジネスエコシステム、アート(社会批評)
新たに生成された3つの要素を中心に、他の要素も第{stage}段階にふさわしい内容で更新し、すべての射の関係性も構築してください。
以下のJSON形式で出力してください：
{{"nodes": [{{"type": "対象名", "definition": "この対象に関する説明", "example": "この対象に関する具体的な例"}}], "arrows": [{{"source": "起点対象", "target": "終点対象", "type": "射名", "definition": "この射に関する説明", "example": "この射に関する具体的な例"}}]}}
"""
    response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}], response_format={"type": "json_object"})
    return parse_json_response(response.choices[0].message.content)

def generate_stage_introduction(topic: str, stage: int, new_elements: dict, user_vision: str) -> str:
    prompt = f"""
第{stage}段階の{topic}について、以下の新たに生成された要素に基づいて紹介文を作成してください。
##生成された要素:
技術や資源: {new_elements["技術や資源"]}
日常の空間とユーザー体験: {new_elements["日常の空間とユーザー体験"]}
前衛的社会問題: {new_elements["前衛的社会問題"]}
##ユーザーの未来構想:
{user_vision}
第{stage}段階の{topic}がどのような状況になっているか、100字以内の日本語で簡潔に紹介文を作成してください。
"""
    response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}], temperature=0)
    return response.choices[0].message.content.strip()

# ========== Story Generation Functions (変更なし) ==========
def generate_outline(theme: str, scene: str, ap_model_history: list) -> str:
    prompt = f"""
あなたはプロのSF作家です。以下の情報に基づき、「{theme}」をテーマにした短編SF小説のあらすじを作成してください。
## 物語の舞台 (Story Setting):
{scene}
## 物語の始まり（Sカーブの第2段階）：
{json.dumps(ap_model_history[1]['ap_model'], ensure_ascii=False, indent=2)}
## 物語の結末（Sカーブの第3段階）：
{json.dumps(ap_model_history[2]['ap_model'], ensure_ascii=False, indent=2)}
## 物語の背景（Sカーブの第1段階）：
{json.dumps(ap_model_history[0]['ap_model'], ensure_ascii=False, indent=2)}
上記の情報に基づき、指定された舞台で繰り広げられる物語の主要なプロット、登場人物、そして中心となる葛藤を含む物語のあらすじを作成してください。あらすじはSF小説のスタイルに沿った、革新的で魅力的なものである必要があります。
"""
    response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}])
    return response.choices[0].message.content

def generate_story(theme: str, outline: str) -> str:
    prompt = f"""
あなたはプロのSF作家です。以下のあらすじに基づき、「{theme}」をテーマにした短編SF小説を執筆してください。
## 物語のあらすじ：
{outline}
このあらすじに沿って、一貫性のある物語を執筆してください。物語は革新的で魅力的、かつSFのスタイルに沿ったものである必要があります。文字数は日本語で1500字程度でお願いします。
"""
    response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}])
    return response.choices[0].message.content

# ========== NEW: UI Functions for Demonstration ==========
def show_visualization(ap_history, height=800):
    """(ユーザー提供のコードに基づく) APモデルの履歴を基に可視化HTMLを生成・表示する"""
    if not ap_history:
        st.warning("可視化するデータがありません。")
        return
    
    # PythonのデータをJSON文字列に変換
    ap_model_data_json = json.dumps(ap_history, ensure_ascii=False)
    
    # HTML, CSS, JavaScriptをf-stringで構築
    html_content = f'''
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>APモデル可視化</title>
    <style>
        body {{ font-family: Arial, sans-serif; background-color: #f5f5f5; margin: 0; padding: 20px; }}
        .vis-wrapper {{ overflow-x: auto; border: 1px solid #ddd; border-radius: 10px; }}
        .visualization {{ position: relative; width: 2200px; height: 700px; background: #fafafa; }}
        .node {{ position: absolute; width: 140px; height: 140px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: bold; text-align: center; cursor: pointer; transition: all 0.3s; box-shadow: 0 4px 12px rgba(0,0,0,0.15); border: 3px solid white; line-height: 1.2; padding: 15px; box-sizing: border-box; }}
        .node:hover {{ transform: scale(1.1); z-index: 100; }}
        .node-前衛的社会問題 {{ background: #ff9999; }}
        .node-人々の価値観 {{ background: #ecba13; }}
        .node-社会問題 {{ background: #ffff99; }}
        .node-技術や資源 {{ background: #99cc99; }}
        .node-日常の空間とユーザー体験 {{ background: #99cccc; }}
        .node-制度 {{ background: #9999ff; }}
        .arrow {{ position: absolute; height: 2px; background: #333; transform-origin: left center; z-index: 1; }}
        .arrow::after {{ content: ''; position: absolute; right: -8px; top: -4px; width: 0; height: 0; border-left: 8px solid #333; border-top: 4px solid transparent; border-bottom: 4px solid transparent; }}
        .arrow-label {{ position: absolute; background: white; padding: 2px 8px; border: 1px solid #ddd; border-radius: 15px; font-size: 10px; white-space: nowrap; transform: translate(-50%, -50%); z-index: 10; }}
        .dotted-arrow {{ border-top: 2px dotted #333; background: transparent; }}
        .dotted-arrow::after {{ border-left-color: #333; }}
        .tooltip {{ position: absolute; background: rgba(0,0,0,0.9); color: white; padding: 12px; border-radius: 8px; font-size: 12px; max-width: 300px; z-index: 1000; pointer-events: none; opacity: 0; transition: opacity 0.3s; line-height: 1.4; }}
        .tooltip.show {{ opacity: 1; }}
    </style>
</head>
<body>
    <div class="vis-wrapper">
        <div class="visualization" id="visualization"></div>
    </div>
    <div class="tooltip" id="tooltip"></div>
    <script>
        const visualization = document.getElementById('visualization');
        const tooltip = document.getElementById('tooltip');
        let allNodes = {{}};
        const apModelData = {ap_model_data_json};

        function getNodePosition(stageIndex, nodeType) {{
            const stageWidth = 700;
            const xOffset = stageIndex * stageWidth;
            if (stageIndex % 2 === 0) {{ 
                switch(nodeType) {{
                    case '制度': return {{ x: xOffset + 355, y: 50 }};
                    case '日常の空間とユーザー体験': return {{ x: xOffset + 180, y: 270 }};
                    case '社会問題': return {{ x: xOffset + 530, y: 270 }};
                    case '技術や資源': return {{ x: xOffset + 50,  y: 500 }};
                    case '前衛的社会問題': return {{ x: xOffset + 355, y: 500 }};
                    case '人々の価値観': return {{ x: xOffset + 660, y: 500 }};
                    default: return null;
                }}
            }} else {{ 
                switch(nodeType) {{
                    case '技術や資源': return {{ x: xOffset + 50,  y: 50 }};
                    case '前衛的社会問題': return {{ x: xOffset + 355, y: 50 }};
                    case '人々の価値観': return {{ x: xOffset + 660, y: 50 }};
                    case '日常の空間とユーザー体験': return {{ x: xOffset + 180, y: 270 }};
                    case '社会問題': return {{ x: xOffset + 530, y: 270 }};
                    case '制度': return {{ x: xOffset + 355, y: 500 }};
                    default: return null;
                }}
            }}
        }}

        function renderAllStages() {{
            visualization.innerHTML = '';
            allNodes = {{}}; 

            apModelData.forEach((stageData, stageIndex) => {{
                if (!stageData.ap_model || !stageData.ap_model.nodes) return;
                stageData.ap_model.nodes.forEach(nodeData => {{
                    const position = getNodePosition(stageIndex, nodeData.type);
                    if (!position) return;
                    const node = document.createElement('div');
                    node.className = `node node-${{nodeData.type}}`;
                    node.style.left = position.x + 'px';
                    node.style.top = position.y + 'px';
                    node.textContent = nodeData.type;
                    const definition = nodeData.definition + (nodeData.example ? `\\n\\n[例] ` + nodeData.example : "");
                    node.dataset.definition = definition.replace(/\\n/g, '<br>');
                    node.dataset.id = `s${{stageData.stage}}-${{nodeData.type}}`;
                    node.addEventListener('mouseenter', showTooltip);
                    node.addEventListener('mouseleave', hideTooltip);
                    visualization.appendChild(node);
                    allNodes[node.dataset.id] = node;
                }});
            }});

            apModelData.forEach((stageData, stageIndex) => {{
                if (!stageData.ap_model || !stageData.ap_model.arrows) return;
                
                const nextStage = apModelData[stageIndex + 1];

                stageData.ap_model.arrows.forEach(arrowData => {{
                    const isLastStage = !nextStage;
                    const arrowType = arrowData.type;
                    const typesToHideInLastStage = ['標準化', '組織化', '意味付け', '習慣化'];

                    if (isLastStage && typesToHideInLastStage.includes(arrowType)) {{
                        return;
                    }}
                    
                    let sourceNode = allNodes[`s${{stageData.stage}}-${{arrowData.source}}`];
                    let targetNode;
                    let isInterStage = false;

                    if (nextStage && (arrowType === '組織化' || arrowType === '標準化')) {{
                        targetNode = allNodes[`s${{nextStage.stage}}-技術や資源`];
                        isInterStage = !!targetNode;
                    }} else if (nextStage && arrowType === '意味付け') {{
                        targetNode = allNodes[`s${{nextStage.stage}}-日常の空間とユーザー体験`];
                        isInterStage = !!targetNode;
                    }} else if (nextStage && arrowType === '習慣化') {{
                        targetNode = allNodes[`s${{nextStage.stage}}-制度`];
                        isInterStage = !!targetNode;
                    }}

                    if (!isInterStage) {{
                        targetNode = allNodes[`s${{stageData.stage}}-${{arrowData.target}}`];
                    }}

                    if (sourceNode && targetNode) {{
                        const isDotted = arrowData.type === 'アート（社会批評）' || arrowData.type === 'アート(社会批評)' || arrowData.type === 'メディア';
                        createArrow(sourceNode, targetNode, arrowData, isDotted);
                    }}
                }});
            }});
        }}

        function createArrow(sourceNode, targetNode, arrowData, isDotted) {{
            const nodeRadius = 70;
            const startPos = {{ x: parseFloat(sourceNode.style.left), y: parseFloat(sourceNode.style.top) }};
            const endPos = {{ x: parseFloat(targetNode.style.left), y: parseFloat(targetNode.style.top) }};
            const dx = (endPos.x + nodeRadius) - (startPos.x + nodeRadius);
            const dy = (endPos.y + nodeRadius) - (startPos.y + nodeRadius);
            const distance = Math.sqrt(dx * dx + dy * dy);
            const angle = Math.atan2(dy, dx) * 180 / Math.PI;
            const adjustedStartX = startPos.x + nodeRadius + (dx / distance) * nodeRadius;
            const adjustedStartY = startPos.y + nodeRadius + (dy / distance) * nodeRadius;
            const adjustedDistance = distance - (nodeRadius * 2);
            const arrow = document.createElement('div');
            arrow.className = isDotted ? 'arrow dotted-arrow' : 'arrow';
            arrow.style.left = adjustedStartX + 'px';
            arrow.style.top = adjustedStartY + 'px';
            arrow.style.width = adjustedDistance + 'px';
            arrow.style.transform = `rotate(${{angle}}deg)`;
            const label = document.createElement('div');
            label.className = 'arrow-label';
            label.textContent = arrowData.type;
            const labelX = adjustedStartX + (dx / distance) * (adjustedDistance / 2);
            const labelY = adjustedStartY + (dy / distance) * (adjustedDistance / 2);
            label.style.left = labelX + 'px';
            label.style.top = labelY + 'px';
            const definition = arrowData.definition + (arrowData.example ? `\\n\\n[例] ` + arrowData.example : "");
            label.dataset.definition = definition.replace(/\\n/g, '<br>');
            label.addEventListener('mouseenter', showTooltip);
            label.addEventListener('mouseleave', hideTooltip);
            visualization.appendChild(arrow);
            visualization.appendChild(label);
        }}

        function showTooltip(event) {{
            const definition = event.target.dataset.definition;
            if (definition) {{
                tooltip.innerHTML = definition;
                tooltip.style.left = (event.pageX + 15) + 'px';
                tooltip.style.top = (event.pageY - 10) + 'px';
                tooltip.classList.add('show');
            }}
        }}

        function hideTooltip() {{
            tooltip.classList.remove('show');
        }}

        renderAllStages();
    </script>
</body>
</html>
'''
    st.components.v1.html(html_content, height=height, scrolling=True)

def show_agent_proposals(element_result):
    """マルチエージェントの提案結果をきれいに表示する"""
    st.markdown(f"#### 🧠 中核要素「{element_result['element_type']}」の生成プロセス")
    for iteration in element_result['iterations']:
        with st.expander(f"反復 {iteration['iteration_number']}/3", expanded=iteration['iteration_number']==1):
            st.markdown("##### 🤖 各エージェントの提案")
            # エージェントの提案が存在するか確認
            if 'all_agent_proposals' in iteration and iteration['all_agent_proposals']:
                cols = st.columns(len(iteration['all_agent_proposals']))
                for i, proposal in enumerate(iteration['all_agent_proposals']):
                    with cols[i]:
                        st.markdown(f"**{proposal.get('agent_name', '不明なエージェント')}**")
                        st.info(proposal.get('proposal', '提案内容なし'))
            else:
                st.write("この反復では提案がありませんでした。")
            
            st.markdown("---")
            st.markdown("##### 🎯 判定結果")
            judgment = iteration.get('judgment', {})
            st.success(f"**選ばれた提案:** {judgment.get('selected_proposal', 'N/A')}")
            st.write(f"**選ばれた内容:** {judgment.get('selected_content', 'N/A')}")
            st.write(f"**選定理由:** {judgment.get('selection_reason', 'N/A')}")
    
    st.markdown("---")
    st.markdown("##### 🏆 最終決定")
    final_decision = element_result.get('final_decision', {})
    st.success(f"**最終的に選択された内容 (反復 {final_decision.get('final_selected_iteration', 'N/A')} の結果):**")
    st.info(f"{final_decision.get('final_selected_content', '最終的な内容はありません')}")
    st.write(f"**最終選定理由:** {final_decision.get('final_selection_reason', 'N/A')}")

# ========== Main UI & State Management (自動実行・高機能可視化版) ==========
st.title("🚀 近未来SF生成器 (自動実行版)")

# --- Session Stateの初期化 ---
if 'process_step' not in st.session_state:
    st.session_state.process_step = 0 # 0:初期, 1-5:処理中, 8:完了
if 'topic' not in st.session_state:
    st.session_state.topic = ""
    st.session_state.scene = ""
    st.session_state.ap_history = []
    st.session_state.descriptions = []
    st.session_state.story = ""
    st.session_state.agents = []
    st.session_state.stage_elements_results = {}

# --- STEP 0: 初期入力画面 ---
if st.session_state.process_step == 0:
    st.markdown("探求したい**テーマ**と物語の**シーン**を入力してください。AIが3段階の未来を予測し、SF小説を生成します。")
    
    topic_input = st.text_input("分析したいテーマを入力してください", placeholder="例：八ツ橋、自動運転、量子コンピュータ")
    scene_input = st.text_area("物語の舞台となるシーンを具体的に記述してください", placeholder="例：夕暮れ時の京都、八ツ橋を売る古民家カフェ")

    if st.button("分析と物語生成を開始 →", type="primary", disabled=not topic_input or not scene_input):
        st.session_state.topic = topic_input
        st.session_state.scene = scene_input
        st.session_state.process_step = 1 # プロセス開始
        st.rerun()

# --- 全自動生成プロセス ---
if 1 <= st.session_state.process_step < 8:
    st.header(f"テーマ: {st.session_state.topic}")
    st.markdown("---")
    
    if st.session_state.process_step == 1:
        with st.status("第1段階：TavilyによるWeb情報収集とAPモデル構築中...", expanded=True) as status:
            intro1, model1 = build_stage1_ap_with_tavily(st.session_state.topic, status)
            st.session_state.descriptions.append(intro1)
            st.session_state.ap_history.append({"stage": 1, "ap_model": model1})
        st.session_state.process_step = 2
        st.rerun()

    if st.session_state.process_step == 2:
        with st.spinner("分析のための専門家AIエージェントを生成中..."):
            st.session_state.agents = generate_agents(st.session_state.topic)
        st.session_state.process_step = 3
        st.rerun()

    if st.session_state.process_step == 3:
        user_vision = f"「{st.session_state.topic}」が技術の進化を通じて、より多くの人々に利益をもたらし、持続可能な形で社会に貢献することを期待します。"
        context = {}
        with st.status("第2段階：Multi-Agentによる未来予測とAPモデル構築中...", expanded=True) as status:
            status.update(label="第2段階 中核要素「技術や資源」を生成中...")
            result1 = generate_single_element_with_iterations(status, st.session_state.topic, "技術や資源", st.session_state.ap_history[0]['ap_model'], st.session_state.agents, user_vision, context)
            st.session_state.stage_elements_results['stage2_elem1'] = result1
            context['技術や資源'] = result1['final_decision']['final_selected_content']

            status.update(label="第2段階 中核要素「日常の空間とユーザー体験」を生成中...")
            result2 = generate_single_element_with_iterations(status, st.session_state.topic, "日常の空間とユーザー体験", st.session_state.ap_history[0]['ap_model'], st.session_state.agents, user_vision, context)
            st.session_state.stage_elements_results['stage2_elem2'] = result2
            context['日常の空間とユーザー体験'] = result2['final_decision']['final_selected_content']
            
            status.update(label="第2段階 中核要素「前衛的社会問題」を生成中...")
            result3 = generate_single_element_with_iterations(status, st.session_state.topic, "前衛的社会問題", st.session_state.ap_history[0]['ap_model'], st.session_state.agents, user_vision, context)
            st.session_state.stage_elements_results['stage2_elem3'] = result3
            context['前衛的社会問題'] = result3['final_decision']['final_selected_content']
            
            status.update(label="第2段階：APモデル全体と紹介文を構築中...")
            model2 = build_complete_ap_model(st.session_state.topic, st.session_state.ap_history[0]['ap_model'], context, 2, user_vision)
            intro2 = generate_stage_introduction(st.session_state.topic, 2, context, user_vision)
            
            st.session_state.descriptions.append(intro2)
            st.session_state.ap_history.append({"stage": 2, "ap_model": model2})
        
        st.session_state.process_step = 4
        st.rerun()

    if st.session_state.process_step == 4:
        user_vision = f"「{st.session_state.topic}」が技術の進化を通じて、より多くの人々に利益をもたらし、持続可能な形で社会に貢献することを期待します。"
        with st.status("第3段階：Multi-Agentによる未来予測とAPモデル構築中...", expanded=True) as status:
            context2 = {}
            new_elements_list = []
            element_sequence = ["技術や資源", "日常の空間とユーザー体験", "前衛的社会問題"]
            for elem_type in element_sequence:
                 status.update(label=f"第3段階 中核要素「{elem_type}」を生成中...")
                 result = generate_single_element_with_iterations(status, st.session_state.topic, elem_type, st.session_state.ap_history[1]['ap_model'], st.session_state.agents, user_vision, context2)
                 final_content = result['final_decision']['final_selected_content']
                 context2[elem_type] = final_content
                 new_elements_list.append(result)
            st.session_state.stage_elements_results['stage3_elements'] = new_elements_list

            status.update(label="第3段階：APモデル全体と紹介文を構築中...")
            model3 = build_complete_ap_model(st.session_state.topic, st.session_state.ap_history[1]['ap_model'], context2, 3, user_vision)
            intro3 = generate_stage_introduction(st.session_state.topic, 3, context2, user_vision)
            
            st.session_state.descriptions.append(intro3)
            st.session_state.ap_history.append({"stage": 3, "ap_model": model3})
        
        st.session_state.process_step = 5
        st.rerun()

    if st.session_state.process_step == 5:
        with st.status("最終段階：SF小説を生成中...", expanded=True):
            st.write("SF小説のあらすじを生成中...")
            outline = generate_outline(st.session_state.topic, st.session_state.scene, st.session_state.ap_history)
            st.write("あらすじからSF短編小説を生成中...")
            story = generate_story(st.session_state.topic, outline)
            st.session_state.story = story
        
        st.success("✅ 全ての生成プロセスが完了しました！")
        st.session_state.process_step = 8
        time.sleep(1) 
        st.rerun()

# --- STEP 8: 最終結果表示 ---
if st.session_state.process_step == 8:
    st.header("🎉 生成結果")
    st.subheader(f"テーマ: {st.session_state.topic}")
    st.markdown(f"**シーン設定:** {st.session_state.scene}")

    st.markdown("### 📚 生成されたSF短編小説")
    st.text_area("SF小説", st.session_state.story, height=400)
    
    with st.expander("📈 3段階の未来予測の要約と生成プロセスを見る"):
        st.markdown(f"**第1段階：揺籃期 (Tavilyによる現実分析)**")
        st.info(st.session_state.descriptions[0])
        st.divider()

        st.markdown(f"**第2段階：離陸期 (Multi-Agentによる発展)**")
        st.info(st.session_state.descriptions[1])
        st.markdown("##### 🤖 第2段階の生成プロセス")
        show_agent_proposals(st.session_state.stage_elements_results['stage2_elem1'])
        show_agent_proposals(st.session_state.stage_elements_results['stage2_elem2'])
        show_agent_proposals(st.session_state.stage_elements_results['stage2_elem3'])
        st.divider()

        st.markdown(f"**第3段階：成熟期 (Multi-Agentによる成熟)**")
        st.info(st.session_state.descriptions[2])
        st.markdown("##### 🤖 第3段階の生成プロセス")
        for result in st.session_state.stage_elements_results['stage3_elements']:
            show_agent_proposals(result)

    st.markdown("---")
    st.subheader("アクション")

    # 可視化機能のボタン
    if st.button("🔬 全ステージのAPモデルを可視化する"):
        st.session_state.show_vis = True
        st.rerun()

    # 可視化表示エリア
    if st.session_state.get('show_vis', False):
        with st.expander("🔬 APモデル可視化（クリックで閉じる）", expanded=True):
            show_visualization(st.session_state.ap_history, height=800)
            if st.button("閉じる"):
                st.session_state.show_vis = False
                st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True) # ダウンロードボタンとの間にスペースを設ける

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="📥 SF小説をダウンロード (.txt)",
            data=st.session_state.story,
            file_name=f"sf_story_{st.session_state.topic}.txt",
            mime="text/plain"
        )
    with col2:
        ap_json = json.dumps(st.session_state.ap_history, ensure_ascii=False, indent=2)
        st.download_button(
            label="📥 APモデル(JSON)をダウンロード",
            data=ap_json,
            file_name=f"ap_model_{st.session_state.topic}.json",
            mime="application/json"
        )
    
    st.markdown("---")
    if st.button("🔄 新しいテーマで再生成"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
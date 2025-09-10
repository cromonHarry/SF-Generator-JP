# =======================================================
# 改良版SF生成器 - デモンストレーション特化版 (2段階・2エージェント・1反復版)
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
def initialize_clients(openai_api_key=None):
    """OpenAIとTavilyクライアントの初期化"""
    try:
        # ユーザー提供のキーがあれば使用、なければsecretsから取得
        if openai_api_key:
            client = OpenAI(api_key=openai_api_key)
        else:
            client = OpenAI(api_key=st.secrets["openai"]["api_key"])
        
        # Tavilyは常にシステムsecretsを使用
        tavily_client = TavilyClient(api_key=st.secrets["tavily"]["api_key"])
        
        return client, tavily_client, None
    except Exception as e:
        return None, None, str(e)

# ========== System Prompt & Constants ==========
SYSTEM_PROMPT = """君はサイエンスフィクションの専門家であり、「アーキオロジカル・プロトタイピング（Archaeological Prototyping, 以下AP）」モデルに基づいて社会を分析します。以下はこのモデルの紹介です。

APは、18の項目(6個の対象と12個の矢)によって構成される社会文化モデル(Sociocultural model)である。要するに、ある課題をテーマとして、社会や文化を18この要素に分割し、そのつながりを論理的に描写したモデルである。

このモデルは、有向グラフとしても考えることができます。6つの対象（前衛的社会問題、人々の価値観、社会問題、技術や資源、日常の空間とユーザー体験、制度）と12の矢（メディア、コミュニティ化、文化芸術振興、標準化、コミュニケーション、組織化、意味付け、製品・サービス、習慣化、パラダイム、ビジネスエコシステム、アート(社会批評)）で1世代の社会文化モデルを構成する。これらの対象と矢のつながりは、以下の定義で示されます。

##対象
1. 前衛的社会問題: 技術や資源のパラダイムによって引き起こされる社会問題や日常生活が営まれる空間やそこでのユーザーの体験に対してアート(社会批評)を介して顕在化される社会問題。
2. 人々の価値観: 文化芸術振興を通して広められる前衛的社会問題や日常のコミュニケーションによって広められる制度で対応できない社会問題に共感する人々のありたい姿。この問題は誰もが認識しているのではなく、ある一部の先進的な/マイノリティの人々のみが認識する。具体的には、マクロの環境問題(気候・生態など)と人文環境問題(倫理・経済・衛生など)が含まれる。
3. 社会問題: 前衛的問題に取り組む先進的なコミュニティによって社会に認識される社会問題やメディアを介して暴露される制度で拘束された社会問題。社会において解決すべき対象として顕在化される。
4. 技術や資源: 日常生活のルーティンを円滑に機能させるために作られた制度のうち、標準化されて過去から制約を受ける技術や資源であり、社会問題を解決すべく組織化された組織(営利・非営利法人、法人格を持たない集団も含み、新規・既存を問わない)が持つ技術や資源。
5. 日常の空間とユーザー体験: 技術や資源を動員して開発された製品・サービスによって構成される物理的空間であり、その空間で製品・サービスに対してある価値観のもとでの意味づけを行い、それらを使用するユーザーの体験。価値観とユーザー体験の関係性は、例えば、「AI エンジニアになりたい」という価値観を持った人々が、PC に対して「プログラミングを学習するためのもの」という意味づけを行い、「プログラミング」という体験を行う、というようなものである。
6. 制度: ある価値観を持った人々が日常的に行う習慣をより円滑に行うために作られる制度や、日常の空間とユーザー体験を構成するビジネスを行う関係者(ビジネスエコシステム)がビジネスをより円滑に行うために作られる制度。具体的には、法律やガイドライン、業界標準、行政指導、モラルが挙げられる。

##矢
1. メディア : 現代の制度的欠陥を顕在化させるメディア。マスメディアやネットメディア等の主要なメディアに加え、情報発信を行う個人も含まれる。制度を社会問題に変換させる。(制度 -> 社会問題)
2. コミュニティ化: 前衛的な問題を認識する人々が集まってできるコミュニティ。公式か非公式かは問わない。前衛的社会問題を社会問題に変換させる。 (前衛的社会問題 -> 社会問題)
3. 文化芸術振興: アート(社会批評)が顕在化させた社会問題を作品として展示し、人々に伝える活動。前衛的社会問題を人々の価値観に変換させる。 (前衛的社会問題 -> 人々の価値観)
4. 標準化 : 制度の中でも、よりり広い関係者に影響を与えるために行われる制度の標準化。制度を新しい技術・資源に変換させる。 (制度 -> 技術・資源)
5. コミュニケーション: 社会問題をより多くの人々に伝えるためのコミュニケーション手段。例えば、近年は SNS を介して行われることが多い。社会問題を人々の価値観に変換させる。 (社会問題 -> 人々の価値観)
6. 組織化 : 社会問題を解決するために形成される組織。法人格の有無や新旧の組織かは問わず 、新しく生まれた社会問題に取り組む全ての組織。社会問題を新しい技術・資源に変換させる。 (社会問題 -> 技術・資源)
7. 意味付け : 人々が価値観に基づいて製品や サービスを使用する理由。人々の価値観を新しい日常の空間とユーザー体験に変換させる。 (人々の価値観 -> 日常の空間とユーザー体験)
8. 製品・サービス: 組織が保有する技術や資源を利用して創造する製品やサービス。技術・資源を日常の空間とユーザー体験に変換させる。 (技術・資源 -> 日常の空間とユーザー体験)
9. 習慣化 : 人々が価値観に基づいて行う習慣。人々の価値観を制度に変換させる。 (人々の価値観 -> 制度)
10. パラダイム : その時代の支配的な技術や資源として、次世代にも影響をもたらすもの。技術・資源を前衛的社会問題に変換させる。 (技術・資源 -> 前衛的社会問題)
11. ビジネスエコシステム : 日常の空間やユーザー体験を維持するために、構成する製品・サービスに関わる関係者が形成するネットワーク 。日常の空間とユーザー体験を制度に変換させる。 (日常の空間とユーザー体験 -> 制度)
12. アート(社会批評): 人々が気づかない問題を、主観的/内発的な視点で捉える人の信念。日常の空間とユーザー体験に違和感を持ち、問題を提示する役割を持つ。日常の空間とユーザー体験を前衛的社会問題に変換させる。 (日常の空間とユーザー体験 -> 前衛的社会問題)

###Sカーブは、時間の経過に伴うテクノロジーの進化を表すモデルです。以下の2つの段階で構成され、各段階の説明は次のとおりです。
##第1段階：醗酵期: この段階では、技術開発は着実に進歩しますが、その進展は緩やかです。主として既存の問題解決や現行機能の改善に焦点が当てられます。この期間の終わりには、現在の問題が解決される一方で、新たな問題が発生します。
##第2段階：離陸期: この段階では、テクノロジーは急成長期に入ります。様々な革新的なアイデアが提案され、それらが最終的に組み合わされることで、全く新しい形の技術が生まれます。この期間の終わりには、テクノロジーは大きな発展を遂げますが、同時に新たな問題も引き起こします。
"""

AP_MODEL_STRUCTURE = {
    "対象": {
        "前衛的社会問題": "技術や資源のパラダイムによって引き起こされる社会問題", 
        "人々の価値観": "先進的な人々が認識する価値観や理想",
        "社会問題": "社会で認識され解決すべき問題", 
        "技術や資源": "問題解決のために組織化された技術や資源",
        "日常の空間とユーザー体験": "製品・サービスによる物理空間とユーザー体験", 
        "制度": "習慣やビジネスを円滑にする制度や規則"
    },
    "矢": {
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

# ========== Helper Functions ==========
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

# ========== Stage 1: Tavily Functions ==========
def generate_question_for_object(client, product: str, object_name: str, object_description: str) -> str:
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

def generate_question_for_arrow(client, product: str, arrow_name: str, arrow_info: dict) -> str:
    prompt = f"""
{product}について、APモデルの矢「{arrow_name}」に関する自然で完整な質問文を生成してください。
矢の詳細：
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

def search_and_get_answer(tavily_client, question: str) -> str:
    try:
        response = tavily_client.search(query=question, include_answer=True)
        answer = response.get('answer', '')
        if answer: return answer
        results = response.get('results', [])
        return results[0].get('content', "情報が見つかりませんでした") if results else "情報が見つかりませんでした"
    except Exception as e: return f"検索エラー: {str(e)}"

def build_ap_element(client, product: str, element_type: str, element_name: str, answer: str) -> dict:
    if element_type == "対象":
        prompt = f"""
{product}の{element_name}について、以下の情報からAP要素を構築してください：
情報: {answer}
以下のJSON形式で出力してください：
{{"type": "{element_name}", "definition": "具体的で簡潔な定義（100文字以内）", "example": "この対象に関する具体的な例"}}
"""
    else:
        arrow_info = AP_MODEL_STRUCTURE["矢"][element_name]
        prompt = f"""
{product}の{element_name}（{arrow_info['from']} → {arrow_info['to']}）について、以下の情報からAP要素を構築してください：
情報: {answer}
以下のJSON形式で出力してください：
{{"source": "{arrow_info['from']}", "target": "{arrow_info['to']}", "type": "{element_name}", "definition": "具体的な変換関係の説明（100文字以内）", "example": "この矢に関する具体的な例"}}
"""
    try:
        response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}], response_format={"type": "json_object"})
        return json.loads(response.choices[0].message.content.strip())
    except Exception: return None

def process_element(client, tavily_client, product: str, element_type: str, name: str, info: dict):
    try:
        if element_type == "対象":
            question = generate_question_for_object(client, product, name, info)
        else:
            question = generate_question_for_arrow(client, product, name, info)
        answer = search_and_get_answer(tavily_client, question)
        if "検索エラー" in answer or not answer:
            return None, None
        element_data = build_ap_element(client, product, element_type, name, answer)
        if not element_data:
            return None, None
        return {"type": element_type, "name": name, "data": element_data}, f"## {name}\n{answer}"
    except Exception as e:
        st.warning(f"要素「{name}」の処理中にエラーが発生しました: {e}")
        return None, None

def build_stage1_ap_with_tavily(client, tavily_client, product: str, status_container):
    ap_model = {"nodes": [], "arrows": []}
    all_answers = []
    MAX_WORKERS = 5
    tasks = []
    for name, desc in AP_MODEL_STRUCTURE["対象"].items():
        tasks.append((product, "対象", name, desc))
    for name, info in AP_MODEL_STRUCTURE["矢"].items():
        tasks.append((product, "矢", name, info))
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_task = {executor.submit(process_element, client, tavily_client, *task): task for task in tasks}
        for future in concurrent.futures.as_completed(future_to_task):
            task_name = future_to_task[future][2]
            status_container.write(f"  - 要素「{task_name}」を検索中...")
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

# ========== Stage 2: Multi-Agent Functions (Modified for 2 agents, 1 iteration) ==========
def generate_agents(client, topic: str) -> list:
    prompt = f"""
テーマ「{topic}」について、APモデルの要素生成を行う2つの完全に異なる専門性を持つエージェントを生成してください。
各エージェントは異なる視点と専門知識を持ち、創造的で革新的な未来予測を提供できる必要があります。
以下のJSON形式で出力してください：
{{ "agents": [ {{ "name": "エージェント名", "expertise": "専門分野", "personality": "性格・特徴", "perspective": "独特な視点" }} ] }}
"""
    response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}], temperature=1.2, response_format={"type": "json_object"})
    result = parse_json_response(response.choices[0].message.content)
    return result["agents"]

def agent_generate_element(client, agent: dict, topic: str, element_type: str, previous_stage_ap: dict, user_vision: str, context: dict) -> str:
    context_info = ""
    if element_type == "日常の空間とユーザー体験": 
        context_info = f"##新しい技術や資源:\n{context.get('技術や資源', '')}"
    elif element_type == "前衛的社会問題": 
        context_info = f"##新しい技術や資源:\n{context.get('技術や資源', '')}\n##新しい日常の空間とユーザー体験:\n{context.get('日常の空間とユーザー体験', '')}"
    
    prompt = f"""
あなたは{agent['name']}として、{agent['expertise']}の専門知識と{agent['personality']}という特徴を持ち、{agent['perspective']}という独特な視点から分析を行います。
##テーマ: {topic}
##前段階のAPモデル:
{json.dumps(previous_stage_ap, ensure_ascii=False, indent=2)}
##ユーザーの未来構想:
{user_vision}
{context_info}
あなたの専門性と視点から、次段階における「{element_type}」の内容を創造的で革新的に生成してください。Sカーブ理論に基づき、前段階からの発展と新たな可能性を考慮し、あなたならではの独創的で素晴らしい想像力があるアイデアを**提案内容のテキストのみで、200字以内で回答してください。JSON形式や余計な説明は不要です。**
"""
    response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}], temperature=1.2)
    return response.choices[0].message.content.strip()

def judge_element_proposals(client, proposals: list[dict], element_type: str, topic: str) -> dict:
    proposals_text = "".join([f"##提案{i+1} (エージェント: {p['agent_name']}):\n{p['proposal']}\n\n" for i, p in enumerate(proposals)])
    prompt = f"""
以下は、「{topic}」の「{element_type}」に関する{len(proposals)}つの提案です。各提案を創造性、未来的視点の観点から評価し、最も想像力がある提案を選択してください。
{proposals_text}
以下のJSON形式で出力してください：
{{ "selected_proposal": "選択された提案のエージェント名", "selected_content": "選択された{element_type}の提案内容", "selection_reason": "選択理由（150字以内）", "creativity_score": "創造性評価（1-10）", "future_vision_score": "未来的視点評価（1-10）" }}
"""
    response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}], temperature=1.2, response_format={"type": "json_object"})
    return parse_json_response(response.choices[0].message.content)

def generate_single_element_with_iterations(client, status_container, topic: str, element_type: str, previous_stage_ap: dict, agents: list, user_vision: str, context: dict) -> dict:
    # 単一反復のみ
    status_container.write(f"    - {len(agents)}人のエージェントが提案を生成中...")
    proposals = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(agents)) as executor:
        future_to_agent = {executor.submit(agent_generate_element, client, agent, topic, element_type, previous_stage_ap, user_vision, context): agent for agent in agents}
        for future in concurrent.futures.as_completed(future_to_agent):
            agent = future_to_agent[future]
            try:
                proposal_content = future.result()
                proposals.append({"agent_name": agent['name'], "proposal": proposal_content})
            except Exception as exc: 
                st.warning(f"{agent['name']}の提案生成中にエラー: {exc}")
    
    if not proposals:
        return {"element_type": element_type, "error": "提案が生成されませんでした。"}
    
    status_container.write(f"    - 提案を評価中...")
    judgment = judge_element_proposals(client, proposals, element_type, topic)
    
    # 単一反復結果を返す
    return {
        "element_type": element_type, 
        "iteration": {"iteration_number": 1, "all_agent_proposals": proposals, "judgment": judgment},
        "final_decision": {"final_selected_content": judgment["selected_content"], "final_selection_reason": judgment["selection_reason"]}
    }

def build_complete_ap_model(client, topic: str, previous_ap: dict, new_elements: dict, stage: int, user_vision: str) -> dict:
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
**重要**：第{stage}段階では、必ず以下の6個の対象と12個の矢すべてを含めてください：
対象: 前衛的社会問題、人々の価値観、社会問題、技術や資源、日常の空間とユーザー体験、制度
矢: メディア、コミュニティ化、文化芸術振興、標準化、コミュニケーション、組織化、意味付け、製品・サービス、習慣化、パラダイム、ビジネスエコシステム、アート(社会批評)
新たに生成された3つの要素を中心に、他の要素も第{stage}段階にふさわしい内容で更新し、すべての矢の関係性も構築してください。
以下のJSON形式で出力してください：
{{"nodes": [{{"type": "対象名", "definition": "この対象に関する説明", "example": "この対象に関する具体的な例"}}], "arrows": [{{"source": "起点対象", "target": "終点対象", "type": "矢名", "definition": "この矢に関する説明", "example": "この矢に関する具体的な例"}}]}}
"""
    response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}], response_format={"type": "json_object"})
    return parse_json_response(response.choices[0].message.content)

def generate_stage_introduction(client, topic: str, stage: int, new_elements: dict, user_vision: str) -> str:
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

# ========== Story Generation Functions (Modified for 2 stages) ==========
def generate_outline(client, theme: str, scene: str, ap_model_history: list) -> str:
    prompt = f"""
あなたはプロのSF作家です。以下の情報に基づき、「{theme}」をテーマにした短編SF小説のあらすじを作成してください。
## 物語の舞台 (Story Setting):
{scene}
## 物語の背景（Sカーブの第1段階）：
{json.dumps(ap_model_history[0]['ap_model'], ensure_ascii=False, indent=2)}
## 物語の発展（Sカーブの第2段階）：
{json.dumps(ap_model_history[1]['ap_model'], ensure_ascii=False, indent=2)}
上記の情報に基づき、指定された舞台で繰り広げられる物語の主要なプロット、登場人物、そして中心となる葛藤を含む物語のあらすじを作成してください。あらすじはSF小説のスタイルに沿った、革新的で魅力的なものである必要があります。物語は第1段階から第2段階への移行に焦点を当ててください。
"""
    response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}])
    return response.choices[0].message.content

def generate_story(client, theme: str, outline: str) -> str:
    prompt = f"""
あなたはプロのSF作家です。以下のあらすじに基づき、「{theme}」をテーマにした短編SF小説を執筆してください。
## 物語のあらすじ：
{outline}
このあらすじに沿って、一貫性のある物語を執筆してください。物語は革新的で魅力的、かつSFのスタイルに沿ったものである必要があります。文字数は日本語で1500字程度でお願いします。
"""
    response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}])
    return response.choices[0].message.content

# ========== UI Functions for Visualization (Modified for 2 stages) ==========
def show_visualization(ap_history, height=750):
    """APモデルの履歴を基に可視化HTMLを生成・表示する"""
    if not ap_history:
        st.warning("可視化するデータがありません。")
        return
    
    html_content = f'''
    <!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><title>APモデル可視化</title><style>
    body{{font-family:sans-serif;background-color:#f0f2f6;margin:0;padding:20px;}}
    .vis-wrapper{{overflow-x:auto;border:1px solid #ddd;border-radius:10px;background:white;padding-top:20px;}}
    .visualization{{position:relative;width:{len(ap_history)*720}px;height:680px;background:#fafafa;}}
    .node{{position:absolute;width:140px;height:140px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:bold;text-align:center;cursor:pointer;transition:all .3s;box-shadow:0 4px 12px rgba(0,0,0,.15);border:3px solid white;line-height:1.2;padding:15px;box-sizing:border-box;}}
    .node:hover{{transform:scale(1.1);z-index:100;}}.node-前衛的社会問題{{background:#ff9999;}}.node-人々の価値観{{background:#ecba13;}}.node-社会問題{{background:#ffff99;}}.node-技術や資源{{background:#99cc99;}}.node-日常の空間とユーザー体験{{background:#99cccc;}}.node-制度{{background:#9999ff;}}
    .arrow{{position:absolute;height:2px;background:#333;transform-origin:left center;z-index:1;}}
    .arrow::after{{content:'';position:absolute;right:-8px;top:-4px;width:0;height:0;border-left:8px solid #333;border-top:4px solid transparent;border-bottom:4px solid transparent;}}
    .arrow-label{{position:absolute;background:white;padding:2px 8px;border:1px solid #ddd;border-radius:15px;font-size:10px;white-space:nowrap;transform:translate(-50%,-50%);z-index:10;}}
    .dotted-arrow{{border-top:2px dotted #333;background:transparent;}}.dotted-arrow::after{{border-left-color:#333;}}
    .tooltip{{position:absolute;background:rgba(0,0,0,.9);color:white;padding:12px;border-radius:8px;font-size:12px;max-width:300px;z-index:1000;pointer-events:none;opacity:0;transition:opacity .3s;line-height:1.4;}}
    .tooltip.show{{opacity:1;}}
    </style></head><body><div class="vis-wrapper"><div class="visualization" id="visualization"></div></div><div class="tooltip" id="tooltip"></div><script>
    const viz=document.getElementById('visualization'),tooltip=document.getElementById('tooltip');let allNodes={{}};const apData={json.dumps(ap_history,ensure_ascii=False)};
    function getPos(s,t){{const w=700,o=s*w;if(s%2===0){{switch(t){{case'制度':return{{x:o+355,y:50}};case'日常の空間とユーザー体験':return{{x:o+180,y:270}};case'社会問題':return{{x:o+530,y:270}};case'技術や資源':return{{x:o+50,y:500}};case'前衛的社会問題':return{{x:o+355,y:500}};case'人々の価値観':return{{x:o+660,y:500}};default:return null}}}}else{{switch(t){{case'技術や資源':return{{x:o+50,y:50}};case'前衛的社会問題':return{{x:o+355,y:50}};case'人々の価値観':return{{x:o+660,y:50}};case'日常の空間とユーザー体験':return{{x:o+180,y:270}};case'社会問題':return{{x:o+530,y:270}};case'制度':return{{x:o+355,y:500}};default:return null}}}}}}
    function render(){{viz.innerHTML='';allNodes={{}};apData.forEach((s,i)=>{{if(!s.ap_model||!s.ap_model.nodes)return;s.ap_model.nodes.forEach(d=>{{const p=getPos(i,d.type);if(!p)return;const n=document.createElement('div');n.className=`node node-${{d.type}}`;n.style.left=p.x+'px';n.style.top=p.y+'px';n.textContent=d.type;const e=d.definition+(d.example?`\\n\\n[例] `+d.example:"");n.dataset.definition=e.replace(/\\n/g,'<br>');n.dataset.id=`s${{s.stage}}-${{d.type}}`;n.addEventListener('mouseenter',showTip);n.addEventListener('mouseleave',hideTip);viz.appendChild(n);allNodes[n.dataset.id]=n}})}});apData.forEach((s,i)=>{{if(!s.ap_model||!s.ap_model.arrows)return;const next=apData[i+1];s.ap_model.arrows.forEach(a=>{{const isLast=!next,type=a.type,hide=isLast&&['標準化','組織化','意味付け','習慣化'].includes(type);if(hide)return;let src=allNodes[`s${{s.stage}}-${{a.source}}`],tgt,isInter=false;if(next&&(type==='組織化'||type==='標準化')){{tgt=allNodes[`s${{next.stage}}-技術や資源`];isInter=!!tgt}}else if(next&&type==='意味付け'){{tgt=allNodes[`s${{next.stage}}-日常の空間とユーザー体験`];isInter=!!tgt}}else if(next&&type==='習慣化'){{tgt=allNodes[`s${{next.stage}}-制度`];isInter=!!tgt}}if(!isInter){{tgt=allNodes[`s${{s.stage}}-${{a.target}}`];}}if(src&&tgt){{const d=type==='アート（社会批評）'||type==='アート(社会批評)'||type==='メディア';createArrow(src,tgt,a,d)}}}})}})}}
    function createArrow(s,t,a,d){{const r=70,p1={{x:parseFloat(s.style.left),y:parseFloat(s.style.top)}},p2={{x:parseFloat(t.style.left),y:parseFloat(t.style.top)}},dx=p2.x+r-(p1.x+r),dy=p2.y+r-(p1.y+r),dist=Math.sqrt(dx*dx+dy*dy),ang=Math.atan2(dy,dx)*180/Math.PI,sx=p1.x+r+dx/dist*r,sy=p1.y+r+dy/dist*r,adjDist=dist-r*2,ar=document.createElement('div');ar.className=d?'arrow dotted-arrow':'arrow';ar.style.left=sx+'px';ar.style.top=sy+'px';ar.style.width=adjDist+'px';ar.style.transform=`rotate(${{ang}}deg)`;const l=document.createElement('div');l.className='arrow-label';l.textContent=a.type;const lx=sx+dx/dist*adjDist/2,ly=sy+dy/dist*adjDist/2;l.style.left=lx+'px';l.style.top=ly+'px';const e=a.definition+(a.example?`\\n\\n[例] `+a.example:"");l.dataset.definition=e.replace(/\\n/g,'<br>');l.addEventListener('mouseenter',showTip);l.addEventListener('mouseleave',hideTip);viz.appendChild(ar);viz.appendChild(l)}}
    function showTip(e){{const d=e.target.dataset.definition;if(d){{tooltip.innerHTML=d;tooltip.style.left=e.pageX+15+'px';tooltip.style.top=e.pageY-10+'px';tooltip.classList.add('show')}}}}
    function hideTip(){{tooltip.classList.remove('show')}}
    render();
    </script></body></html>'''
    st.components.v1.html(html_content, height=height, scrolling=True)

def show_agent_proposals(element_result):
    """マルチエージェントの提案結果をきれいに表示する (Modified for single iteration)"""
    st.markdown(f"#### 🧠「{element_result['element_type']}」の生成プロセス")
    
    # 単一反復表示
    iteration = element_result['iteration']
    st.markdown(f"##### エージェント提案")
    
    st.markdown("###### 🤖 各エージェントの提案")
    cols = st.columns(len(iteration['all_agent_proposals']))
    for i, proposal in enumerate(iteration['all_agent_proposals']):
        with cols[i]:
            st.markdown(f"**{proposal['agent_name']}**")
            st.info(proposal['proposal'])
    
    st.markdown("###### 🎯 判定結果")
    judgment = iteration['judgment']
    st.success(f"**選ばれた提案:** {judgment['selected_proposal']}")
    st.write(f"**選ばれた内容:** {judgment['selected_content']}")
    st.write(f"**選定理由:** {judgment['selection_reason']}")

# ========== API Key Validation Function ==========
def validate_openai_key(api_key: str) -> bool:
    """OpenAI API keyを簡単なテスト呼び出しで検証"""
    try:
        test_client = OpenAI(api_key=api_key)
        # 最小限のテスト呼び出し
        response = test_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hi"}],
        )
        return True
    except Exception:
        return False

# ========== Main UI & State Management ==========
st.title("🚀 近未来SF生成器（デモ版）")

# --- Session Stateの初期化 ---
if 'process_started' not in st.session_state:
    st.session_state.process_started = False
    st.session_state.topic = ""
    st.session_state.scene = ""
    st.session_state.user_api_key = ""
    st.session_state.ap_history = []
    st.session_state.descriptions = []
    st.session_state.story = ""
    st.session_state.agents = []
    st.session_state.stage_elements_results = {'stage2': []}
    st.session_state.client = None
    st.session_state.tavily_client = None

# --- STEP 0: 初期入力画面 ---
if not st.session_state.process_started:
    st.markdown("**OpenAI API キー**、探求したい**テーマ**と物語の**舞台**を入力してください。AIが2段階の未来を予測し、SF小説を最後まで自動で生成します。")
    
    # API Key input
    st.markdown("### 🔑 API設定")
    api_key_input = st.text_input(
        "OpenAI API キーを入力してください", 
        type="password",
        placeholder="sk-...",
        help="あなたのAPIキーはすべてのAI生成に使用されます。永続的に保存されることはありません。"
    )
    
    # API key検証
    key_valid = False
    if api_key_input:
        with st.spinner("APIキーを検証中..."):
            key_valid = validate_openai_key(api_key_input)
        if key_valid:
            st.success("✅ APIキーが有効です！")
        else:
            st.error("❌ 無効なAPIキーです。確認して再試行してください。")
    
    st.markdown("### 📝 コンテンツ設定")
    topic_input = st.text_input("探求したいテーマを入力してください", placeholder="例：八ツ橋、自動運転、量子コンピュータ")
    scene_input = st.text_area("物語の舞台を具体的に記述してください", placeholder="例：夕暮れ時の京都、八ツ橋を売るお店")

    # すべての入力が有効かチェック
    all_inputs_valid = api_key_input and key_valid and topic_input and scene_input
    
    if st.button("APと物語生成開始 →", type="primary", disabled=not all_inputs_valid):
        # ユーザーのAPIキーでクライアントを初期化
        client, tavily_client, error = initialize_clients(api_key_input)
        
        if error:
            st.error(f"❌ クライアントの初期化に失敗しました: {error}")
        else:
            st.session_state.topic = topic_input
            st.session_state.scene = scene_input
            st.session_state.user_api_key = api_key_input
            st.session_state.client = client
            st.session_state.tavily_client = tavily_client
            st.session_state.process_started = True
            st.rerun()

# --- 全自動実行プロセス ---
else:
    # クライアントが初期化されていることを確認
    if not st.session_state.client or not st.session_state.tavily_client:
        client, tavily_client, error = initialize_clients(st.session_state.user_api_key)
        if error:
            st.error(f"❌ クライアント初期化エラー: {error}")
            st.stop()
        st.session_state.client = client
        st.session_state.tavily_client = tavily_client
    
    st.header(f"テーマ: {st.session_state.topic}")
    user_vision = f"「{st.session_state.topic}」が技術の進化を通じて、未来の発展を想像する。"

    # ==================================================================
    # 表示エリア: 常に存在するデータを表示する
    # ==================================================================
    # --- Stage 1 表示 ---
    if len(st.session_state.ap_history) >= 1:
        st.markdown("---")
        st.header("Stage 1: 醗酵期（現状分析）")
        st.info(st.session_state.descriptions[0])
        show_visualization(st.session_state.ap_history[0:1])

    # --- Stage 2 表示 ---
    if st.session_state.agents:
        st.markdown("---")
        st.header("Stage 2: 離陸期（発展予測）")
        st.subheader("🤖 専門家AIエージェントチーム")
        with st.expander("生成されたエージェントを見る", expanded=True):
            cols = st.columns(len(st.session_state.agents))
            for i, agent in enumerate(st.session_state.agents):
                with cols[i]:
                    st.markdown(f"**{agent['name']}**")
                    st.write(f"**専門:** {agent['expertise']}")
                    st.write(f"**性格:** {agent['personality']}")
                    st.write(f"**視点:** {agent['perspective']}")
    
    if st.session_state.stage_elements_results['stage2']:
        for result in st.session_state.stage_elements_results['stage2']:
            show_agent_proposals(result)

    if len(st.session_state.ap_history) >= 2:
        st.info(st.session_state.descriptions[1])
        show_visualization(st.session_state.ap_history)

    # --- 物語 表示 ---
    if st.session_state.story:
        st.markdown("---")
        st.header("🎉 生成結果")
        st.markdown(f"**シーン設定:** {st.session_state.scene}")
        st.markdown("### 📚 生成されたSF短編小説")
        st.text_area("SF小説", st.session_state.story, height=400)
        
        with st.expander("📈 2段階の未来予測の要約を見る"):
            stages_info = ["第1段階：醗酵期", "第2段階：離陸期"]
            for i, stage_name in enumerate(stages_info):
                st.markdown(f"**{stage_name}**")
                st.info(st.session_state.descriptions[i])
    
    # ==================================================================
    # 生成ロジック: データの有無を確認し、なければ生成する
    # ==================================================================
    # --- Stage 1 生成 ---
    if len(st.session_state.ap_history) == 0:
        with st.status("第1段階：TavilyによるWeb情報収集とAPモデル構築中...", expanded=True) as status:
            intro1, model1 = build_stage1_ap_with_tavily(st.session_state.client, st.session_state.tavily_client, st.session_state.topic, status)
            st.session_state.descriptions.append(intro1)
            st.session_state.ap_history.append({"stage": 1, "ap_model": model1})
        st.rerun()
        
    # --- Stage 2 生成 (ステップごと) ---
    elif len(st.session_state.ap_history) == 1:
        # Agent生成
        if not st.session_state.agents:
            with st.spinner("分析のための専門家AIエージェントを生成中..."):
                st.session_state.agents = generate_agents(st.session_state.client, st.session_state.topic)
            st.rerun()
        
        # 要素生成
        s2_results = st.session_state.stage_elements_results['stage2']
        element_sequence = ["技術や資源", "日常の空間とユーザー体験", "前衛的社会問題"]
        if len(s2_results) < len(element_sequence):
            elem_type = element_sequence[len(s2_results)]
            with st.status(f"第2段階「{elem_type}」を生成中...", expanded=True) as status:
                # 前の要素の結果をコンテキストとして渡す
                context = {r['element_type']: r['final_decision']['final_selected_content'] for r in s2_results}
                result = generate_single_element_with_iterations(st.session_state.client, status, st.session_state.topic, elem_type, st.session_state.ap_history[0]['ap_model'], st.session_state.agents, user_vision, context)
                s2_results.append(result)
            st.rerun()

        # APモデル全体の構築
        else:
            with st.status("第2段階：APモデル全体を構築中...", expanded=True) as status:
                context = {r['element_type']: r['final_decision']['final_selected_content'] for r in s2_results}
                status.update(label="第2段階：APモデル全体を構築中...")
                model2 = build_complete_ap_model(st.session_state.client, st.session_state.topic, st.session_state.ap_history[0]['ap_model'], context, 2, user_vision)
                status.update(label="第2段階：紹介文を生成中...")
                intro2 = generate_stage_introduction(st.session_state.client, st.session_state.topic, 2, context, user_vision)
                st.session_state.descriptions.append(intro2)
                st.session_state.ap_history.append({"stage": 2, "ap_model": model2})
            st.rerun()

    # --- 物語 生成 ---
    elif len(st.session_state.ap_history) == 2 and not st.session_state.story:
        with st.spinner("最終段階：SF小説のあらすじを生成中..."):
            outline = generate_outline(st.session_state.client, st.session_state.topic, st.session_state.scene, st.session_state.ap_history)
        with st.spinner("最終段階：あらすじからSF短編小説を生成中..."):
            story = generate_story(st.session_state.client, st.session_state.topic, outline)
            st.session_state.story = story
        st.success("✅ 全ての生成プロセスが完了しました！")
        time.sleep(1)
        st.rerun()
        
    # --- 最終ページのアクションボタン ---
    if st.session_state.story:
        st.markdown("---")
        st.subheader("アクション")
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

    # --- リセットボタン ---
    st.markdown("---")
    if st.button("🔄 新しいテーマで再生成"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
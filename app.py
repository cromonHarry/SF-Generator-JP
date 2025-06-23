# ============================
# 改良版近未来SF生成器 - 日文多轮对话版
# ============================
import streamlit as st
import json
import re
import time
from openai import OpenAI
from tavily import TavilyClient # wikipediaとrequestsの代わりにtavilyを追加

# ========== Multi-page setup ==========
if 'page' not in st.session_state:
    st.session_state.page = "main"

# ========== Visualization Page ==========
if st.session_state.page == "visualization":
    st.set_page_config(page_title="APモデル可視化", layout="wide")
    
    st.title("🔬 APモデル可視化")
    st.markdown("APモデルの3段階の進化を可視化します。")
    
    # Check if AP model data exists
    if 'ap_history' in st.session_state and st.session_state.ap_history:
        # Create the HTML visualization
        html_content = '''
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>APモデル可視化</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f5f5f5;
            margin: 0;
            padding: 20px;
        }
        
        .container {
            max-width: 95vw;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        .vis-wrapper {
            overflow-x: auto;
            border: 1px solid #ddd;
            border-radius: 10px;
        }
        
        .visualization {
            position: relative;
            width: 2200px;
            height: 700px;
            background: #fafafa;
        }
        
        .node {
            position: absolute;
            width: 140px;
            height: 140px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 13px;
            font-weight: bold;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            border: 3px solid white;
            line-height: 1.2;
            padding: 15px;
            box-sizing: border-box;
        }
        
        .node:hover {
            transform: scale(1.1);
            z-index: 100;
        }
        
        /* Node Colors */
        .node-前衛的社会問題 { background: #ff9999; }
        .node-人々の価値観 { background: #ecba13; }
        .node-社会問題 { background: #ffff99; }
        .node-技術や資源 { background: #99cc99; }
        .node-日常の空間とユーザー体験 { background: #99cccc; }
        .node-制度 { background: #9999ff; }
        
        .arrow {
            position: absolute;
            height: 2px;
            background: #333;
            transform-origin: left center;
            z-index: 1;
        }
        
        .arrow::after {
            content: '';
            position: absolute;
            right: -8px;
            top: -4px;
            width: 0;
            height: 0;
            border-left: 8px solid #333;
            border-top: 4px solid transparent;
            border-bottom: 4px solid transparent;
        }
        
        .arrow-label {
            position: absolute;
            background: white;
            padding: 2px 8px;
            border: 1px solid #ddd;
            border-radius: 15px;
            font-size: 10px;
            white-space: nowrap;
            transform: translate(-50%, -50%);
            z-index: 10;
        }
        
        .dotted-arrow {
            border-top: 2px dotted #333;
            background: transparent;
        }
        
        .dotted-arrow::after {
            border-left-color: #333;
        }
        
        .tooltip {
            position: absolute;
            background: rgba(0,0,0,0.9);
            color: white;
            padding: 12px;
            border-radius: 8px;
            font-size: 12px;
            max-width: 300px;
            z-index: 1000;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.3s;
            line-height: 1.4;
        }
        
        .tooltip.show {
            opacity: 1;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 style="text-align: center; margin-bottom: 30px;">APモデル可視化</h1>
        
        <div class="vis-wrapper">
            <div class="visualization" id="visualization">
            </div>
        </div>
        
        <div class="tooltip" id="tooltip"></div>
    </div>

    <script>
        const visualization = document.getElementById('visualization');
        const tooltip = document.getElementById('tooltip');
        let allNodes = {};

        // Load AP model data from session state
        const apModelData = ''' + json.dumps(st.session_state.ap_history, ensure_ascii=False) + ''';

        function getNodePosition(stageIndex, nodeType) {
            const stageWidth = 700;
            const xOffset = stageIndex * stageWidth;
            
            if (stageIndex % 2 === 0) { 
                switch(nodeType) {
                    case '制度':                      return { x: xOffset + 355, y: 50 };
                    case '日常の空間とユーザー体験':  return { x: xOffset + 180, y: 270 };
                    case '社会問題':                  return { x: xOffset + 530, y: 270 };
                    case '技術や資源':              return { x: xOffset + 50,  y: 500 };
                    case '前衛的社会問題':            return { x: xOffset + 355, y: 500 };
                    case '人々の価値観':              return { x: xOffset + 660, y: 500 };
                    default:                        return null;
                }
            } else { 
                switch(nodeType) {
                    case '技術や資源':              return { x: xOffset + 50,  y: 50 };
                    case '前衛的社会問題':            return { x: xOffset + 355, y: 50 };
                    case '人々の価値観':              return { x: xOffset + 660, y: 50 };
                    case '日常の空間とユーザー体験':  return { x: xOffset + 180, y: 270 };
                    case '社会問題':                  return { x: xOffset + 530, y: 270 };
                    case '制度':                      return { x: xOffset + 355, y: 500 };
                    default:                        return null;
                }
            }
        }

        function renderAllStages() {
            visualization.innerHTML = '';
            allNodes = {}; 

            apModelData.forEach((stageData, stageIndex) => {
                stageData.ap_model.nodes.forEach(nodeData => {
                    const position = getNodePosition(stageIndex, nodeData.type);
                    if (!position) return;

                    const node = document.createElement('div');
                    node.className = `node node-${nodeData.type}`;
                    node.style.left = position.x + 'px';
                    node.style.top = position.y + 'px';
                    node.textContent = nodeData.type;
                    node.dataset.definition = nodeData.definition;
                    node.dataset.id = `s${stageData.stage}-${nodeData.type}`;

                    node.addEventListener('mouseenter', showTooltip);
                    node.addEventListener('mouseleave', hideTooltip);

                    visualization.appendChild(node);
                    allNodes[node.dataset.id] = node;
                });
            });

            apModelData.forEach((stageData, stageIndex) => {
                const nextStage = apModelData[stageIndex + 1];

                stageData.ap_model.arrows.forEach(arrowData => {
                    const isLastStage = !nextStage;
                    const arrowType = arrowData.type;
                    const typesToHideInLastStage = ['標準化', '組織化', '意味付け', '習慣化'];

                    if (isLastStage && typesToHideInLastStage.includes(arrowType)) {
                        return;
                    }
                    
                    let sourceNode = allNodes[`s${stageData.stage}-${arrowData.source}`];
                    let targetNode;
                    let isInterStage = false;

                    if (nextStage && (arrowType === '組織化' || arrowType === '標準化')) {
                        targetNode = allNodes[`s${nextStage.stage}-技術や資源`];
                        isInterStage = !!targetNode;
                    } else if (nextStage && arrowType === '意味付け') {
                        targetNode = allNodes[`s${nextStage.stage}-日常の空間とユーザー体験`];
                        isInterStage = !!targetNode;
                    } else if (nextStage && arrowType === '習慣化') {
                        targetNode = allNodes[`s${nextStage.stage}-制度`];
                        isInterStage = !!targetNode;
                    }

                    if (!isInterStage) {
                        targetNode = allNodes[`s${stageData.stage}-${arrowData.target}`];
                    }

                    if (sourceNode && targetNode) {
                        const isDotted = arrowData.type === 'アート（社会批評）' || arrowData.type === 'アート(社会批評)' || arrowData.type === 'メディア';
                        createArrow(sourceNode, targetNode, arrowData, isDotted);
                    }
                });
            });
        }

        function createArrow(sourceNode, targetNode, arrowData, isDotted) {
            const nodeRadius = 70;
            
            const startPos = { x: parseFloat(sourceNode.style.left), y: parseFloat(sourceNode.style.top) };
            const endPos = { x: parseFloat(targetNode.style.left), y: parseFloat(targetNode.style.top) };

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
            arrow.style.transform = `rotate(${angle}deg)`;

            const label = document.createElement('div');
            label.className = 'arrow-label';
            label.textContent = arrowData.type;
            
            const labelX = adjustedStartX + (dx / distance) * (adjustedDistance / 2);
            const labelY = adjustedStartY + (dy / distance) * (adjustedDistance / 2);
            label.style.left = labelX + 'px';
            label.style.top = labelY + 'px';
            
            label.dataset.definition = arrowData.definition;
            label.addEventListener('mouseenter', showTooltip);
            label.addEventListener('mouseleave', hideTooltip);

            visualization.appendChild(arrow);
            visualization.appendChild(label);
        }

        function showTooltip(event) {
            const definition = event.target.dataset.definition;
            if (definition) {
                tooltip.innerHTML = definition;
                tooltip.style.left = (event.pageX + 15) + 'px';
                tooltip.style.top = (event.pageY - 10) + 'px';
                tooltip.classList.add('show');
            }
        }

        function hideTooltip() {
            tooltip.classList.remove('show');
        }

        // Initialize visualization
        renderAllStages();
    </script>
</body>
</html>
        '''
        
        # Display the HTML content
        st.components.v1.html(html_content, height=800, scrolling=True)
        
        # Download options
        st.subheader("ダウンロードオプション")
        col1, col2 = st.columns(2)
        
        with col1:
            ap_json = json.dumps(st.session_state.ap_history, ensure_ascii=False, indent=2)
            st.download_button(
                label="📥 APモデルJSONをダウンロード",
                data=ap_json,
                file_name="ap_model.json",
                mime="application/json"
            )
        
        with col2:
            if 'story' in st.session_state and st.session_state.story:
                st.download_button(
                    label="📥 SF小説をダウンロード",
                    data=st.session_state.story,
                    file_name="sf_story.txt",
                    mime="text/plain"
                )
    
    else:
        st.warning("可視化するAPモデルデータがありません。メインページでAPモデルを生成してください。")
    
    if st.button("⬅ メインページに戻る"):
        st.session_state.page = "main"
        st.rerun()
    st.stop()

# ========== Main Page ==========
# Client Initialization
client = OpenAI(api_key=st.secrets["openai"]["api_key"])
tavily_client = TavilyClient(api_key=st.secrets["tavily"]["api_key"])


# System prompt in Japanese
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

# APモデルの基本構造（Tavilyベース構築用）
AP_MODEL_STRUCTURE = {
    "対象": {
        "前衛的社会問題": "技術や資源のパラダイムによって引き起こされる社会問題",
        "人々の価値観": "先進的な人々が認識する価値観や理想",
        "社会問題": "社会で認識され解決すべき問題", 
        "技術や資源": "問題解決のために組織化された技術や資源",
        "日常の空間とユーザー体験": "製品・サービスによる物理空間とユーザー体験",
        "制度": "習慣やビジネスを円滑にする制度や規則"
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

# Initialize session state
if 'conversation_step' not in st.session_state:
    st.session_state.conversation_step = 0
if 'user_inputs' not in st.session_state:
    st.session_state.user_inputs = {}
if 'selected_topic' not in st.session_state:
    st.session_state.selected_topic = None
if 'generated_suggestions' not in st.session_state:
    st.session_state.generated_suggestions = []
if 'ap_history' not in st.session_state:
    st.session_state.ap_history = []
if 'descriptions' not in st.session_state:
    st.session_state.descriptions = []
if 'story' not in st.session_state:
    st.session_state.story = ""
if 'generating' not in st.session_state:
    st.session_state.generating = False

# Helper functions
def parse_json_response(gpt_output: str) -> dict:
    result_str = gpt_output.strip()
    if result_str.startswith("```") and result_str.endswith("```"):
        result_str = re.sub(r'^```[^\n]*\n', '', result_str)
        result_str = re.sub(r'\n```$', '', result_str)
        result_str = result_str.strip()
    
    try:
        return json.loads(result_str)
    except Exception as e:
        raise e

def generate_suggestions(topic: str, reason: str) -> list[str]:
    """LLMで改善案を生成"""
    user_prompt = f"""
テーマ「{topic}」について、ユーザーは現状に満足しておらず、その理由を「{reason}」と述べています。
この状況を改善するための可能な発展方向を5つ、それぞれ１０字以内で簡潔に生成してください。
出力は "suggestions" というキーを持つJSONオブジェクトにしてください。
{{
    "suggestions": ["提案1", "提案2", "提案3", "提案4", "提案5"]
}}
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": user_prompt}],
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        return result.get("suggestions", [])
    except Exception:
        return ["AIによる提案の生成に失敗しました。手動で入力してください。"]

# --- New Tavily-based functions ---

def generate_question_for_object(product: str, object_name: str, object_description: str) -> str:
    """AP対象用の自然な質問文を生成"""
    prompt = f"""
{product}について、APモデルの対象「{object_name}」({object_description})に関する自然で完整な質問文を1つ生成してください。
質問は以下の条件を満たしてください：
- 完整な文として自然な日本語
- {product}に関連する具体的内容を調べる質問
- 検索エンジンで良い結果が得られそうな質問
質問のみを出力してください：
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return response.choices[0].message.content.strip()

def generate_question_for_arrow(product: str, arrow_name: str, arrow_info: dict) -> str:
    """AP射用の自然な質問文を生成"""
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
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return response.choices[0].message.content.strip()

def search_and_get_answer(question: str) -> str:
    """Tavilyで質問し、答えを取得"""
    try:
        response = tavily_client.search(query=question, include_answer=True)
        answer = response.get('answer', '')
        if answer:
            return answer
        else:
            results = response.get('results', [])
            return results[0].get('content', "情報が見つかりませんでした") if results else "情報が見つかりませんでした"
    except Exception as e:
        return f"検索エラー: {str(e)}"

def build_ap_element(product: str, element_type: str, element_name: str, answer: str) -> dict:
    """回答からAP要素を構築"""
    if element_type == "対象":
        prompt = f"""
{product}の{element_name}について、以下の情報からAP要素を構築してください：
情報: {answer}
以下のJSON形式で出力してください：
{{
  "type": "{element_name}",
  "definition": "具体的で簡潔な定義（100文字以内）",
  "reference": "情報源の要約（50文字以内）"
}}
"""
    else:  # 射
        arrow_info = AP_MODEL_STRUCTURE["射"][element_name]
        prompt = f"""
{product}の{element_name}（{arrow_info['from']} → {arrow_info['to']}）について、以下の情報からAP要素を構築してください：
情報: {answer}
以下のJSON形式で出力してください：
{{
  "source": "{arrow_info['from']}",
  "target": "{arrow_info['to']}",
  "type": "{element_name}",
  "definition": "具体的な変換関係の説明（100文字以内）",
  "reference": "情報源の要約（50文字以内）"
}}
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content.strip())
    except Exception:
        return None

def build_stage1_ap_with_tavily(product: str, progress_bar):
    """Tavilyを使って第1段階のAPモデルと紹介文を構築"""
    ap_model = {"nodes": [], "arrows": []}
    all_answers = []
    
    total_elements = len(AP_MODEL_STRUCTURE["対象"]) + len(AP_MODEL_STRUCTURE["射"])
    processed_elements = 0
    base_progress = 0.1

    # 対象 (Nodes)
    for obj_name, obj_desc in AP_MODEL_STRUCTURE["対象"].items():
        question = generate_question_for_object(product, obj_name, obj_desc)
        answer = search_and_get_answer(question)
        if answer and "検索エラー" not in answer:
            all_answers.append(f"## {obj_name}\n{answer}")
            element = build_ap_element(product, "対象", obj_name, answer)
            if element: ap_model["nodes"].append(element)
        processed_elements += 1
        progress_bar.progress(base_progress + (0.3 * (processed_elements / total_elements)), text=f"第1段階：{obj_name}をWebで調査中...")
        time.sleep(1) 

    # 射 (Arrows)
    for arrow_name, arrow_info in AP_MODEL_STRUCTURE["射"].items():
        question = generate_question_for_arrow(product, arrow_name, arrow_info)
        answer = search_and_get_answer(question)
        if answer and "検索エラー" not in answer:
            all_answers.append(f"## {arrow_name}\n{answer}")
            element = build_ap_element(product, "射", arrow_name, answer)
            if element: ap_model["arrows"].append(element)
        processed_elements += 1
        progress_bar.progress(base_progress + (0.3 * (processed_elements / total_elements)), text=f"第1段階：{arrow_name}をWebで調査中...")
        time.sleep(1)

    # 紹介文を生成
    intro_prompt = f"""
以下の{product}に関する様々な側面からの情報をもとに、{product}がどのようなものか、100字以内の日本語で簡潔に紹介文を作成してください。
### 収集された情報:\n{''.join(all_answers)}
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": intro_prompt}],
        temperature=0
    )
    introduction = response.choices[0].message.content

    return introduction, ap_model

# --- End of new functions ---

def update_to_next_stage(product: str, ap_model: list[dict], description: list[str], imagination: str, stage: int):
    """次段階への更新内容を生成"""
    temp = f"""
今は{product}に関するAPモデルを次のSカーブ段階に更新してください。以下はAPモデルの情報です：
"""
    for i in range(len(ap_model)):
        temp += f"##第{i+1}段階のAPモデル:\n{ap_model[i]}\n"
    for j in range(len(description)):
        temp += f"##第{j+1}段階の{product}の説明:\n{description[j]}\n"
    if stage == 2:
        temp += f"##これは第{stage}段階の{product}に関するユーザーの構想です：\n{imagination}\n"
        
    temp += f"""
Sカーブに基づき、第{stage}段階における新しい対象「技術や資源」と「日常の空間とユーザー体験」を分析し、対象内容を出力してください。
そして、第{stage}段階における{product}の構想を分析し、{product}の紹介を出力してください。100字日本語以内。

以下のJSON形式で出力してください：
{{"introduction": "第{stage}段階の{product}の100字以内の紹介", 
"tech_resources": "第{stage}段階技術や資源の具体的内容", 
"daily_experience": "第{stage}段階日常の空間とユーザー体験の具体的内容"}}
"""
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": temp}
        ],
        response_format={"type": "json_object"}
    )
    
    try:
        result = parse_json_response(response.choices[0].message.content)
        return result["introduction"], result["tech_resources"], result["daily_experience"]
    except Exception as e:
        return f"第{stage}段階の{product}の発展", "技術や資源の内容", "日常の空間とユーザー体験の内容"

def update_ap_model(product: str, ap_model: list[dict], description: list[str], tech_resources: str, daily_experience: str, stage: int) -> dict:
    """第2、3段階の完全なAPモデルを構築（必ず6対象+12射）"""
    user_prompt = f"""
これから第{stage}Sカーブ段階のAPモデルを構築してください。

##前段階の情報:
第{stage-1}段階の{product}の説明: {description[stage-2]}
第{stage-1}段階のAPモデル: {ap_model[stage-2]}

##現段階の情報:
構想：{description[stage-1]}
技術や資源：{tech_resources}
日常の空間とユーザー体験：{daily_experience}

**重要**：第{stage}段階では、必ず以下の6個の対象と12個の射すべてを含めてください：

対象: 前衛的社会問題、人々の価値観、社会問題、技術や資源、日常の空間とユーザー体験、制度
射: メディア、コミュニティ化、文化芸術振興、標準化、コミュニケーション、組織化、意味付け、製品・サービス、習慣化、パラダイム、ビジネスエコシステム、アート(社会批評)

以下のJSON形式で出力してください：
{{"nodes": [{{"type": "対象名", "definition": "この対象に関する説明"}}], "arrows": [{{"source": "起点対象", "target": "終点対象", "type": "射名", "definition": "この射に関する説明"}}]}}
"""
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"}
    )
    
    try:
        result = parse_json_response(response.choices[0].message.content)
        return result
    except Exception as e:
        return {"nodes": [], "arrows": []}

def generate_story(product: str, ap_model: list[dict], description: list[str]) -> str:
    """SF短編小説を生成"""
    user_prompt = f"""
以下は{product}に関するAPモデルの情報です：
"""
    for i in range(len(ap_model)):
        user_prompt += f"""
##第{i+1}段階のAPモデル:
{ap_model[i]}
##第{i+1}段階の{product}の説明:
{description[i]}

"""
    user_prompt += f"""
それでは{product}をテーマとしてAPモデルの内容を基づき、近未来短編SF小説を生成してください。**重要**: 文字数は日本語1000字程度で。
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
    )

    return response.choices[0].message.content

# Main UI
st.title("🚀 近未来SF生成器")
st.markdown("APモデルに基づいて3段階の進化タイムラインとSF小説を生成するアプリケーションです。")

# Multi-step conversation interface
if st.session_state.conversation_step == 0:
    st.markdown("あなたの興味のある事柄についてAPモデルを構築し、SF短編小説を生成します。")
    
    interest = st.text_input("どのようなことに興味がありますか？", 
                            placeholder="例：食べ物、技術、文化など",
                            key="interest_input")
    
    if st.button("次へ進む", disabled=not interest):
        st.session_state.user_inputs['interest'] = interest
        st.session_state.selected_topic = interest # トピックを直接設定
        st.session_state.conversation_step = 2 # Wikipedia選択をスキップして評価へ
        st.rerun()

# Step 1 (Wikipedia selection) is now removed.

elif st.session_state.conversation_step == 2:
    st.markdown(f"「{st.session_state.selected_topic}」の現在の発展状況について、あなたの評価を教えてください。")
    
    score = st.slider(
        "現状について、10点満点で採点してください。",
        min_value=1,
        max_value=10,
        value=5,
        help="1点 = 非常に不満, 10点 = 非常に満足"
    )
    
    if st.button("次へ進む"):
        st.session_state.user_inputs['score'] = score
        st.session_state.conversation_step = 3
        st.rerun()

elif st.session_state.conversation_step == 3:
    st.markdown(f"「{st.session_state.selected_topic}」の現状評価で、満点にしなかった主な理由は何ですか？具体的であるほど、より良い提案が得られます。")
    
    reason = st.text_area(
        "評価が満点ではない理由を教えてください。",
        placeholder="例：コストが高い、特定のユーザーしか利用できない、環境への影響が懸念されるなど",
        key="reason_input"
    )
    
    if st.button("改善案の生成に進む", disabled=not reason):
        st.session_state.user_inputs['reason'] = reason
        st.session_state.conversation_step = 4
        st.rerun()

elif st.session_state.conversation_step == 4:
    st.markdown("ご指摘いただいた問題点に基づき、AIが以下の改善案を生成しました。未来の構想の参考にするものを選択してください。（複数選択可）")
    
    if not st.session_state.generated_suggestions:
        with st.spinner("AIが改善案を生成中..."):
            suggestions = generate_suggestions(
                st.session_state.selected_topic,
                st.session_state.user_inputs['reason']
            )
            st.session_state.generated_suggestions = suggestions

    # --- ここからが変更箇所 ---
    st.markdown("**改善案を選択してください:**")
    options = st.session_state.generated_suggestions
    selected_options = [] # 選択された項目を格納する空のリストを準備

    # enumerateを使い、各選択肢にユニークなキーを割り当てる
    for i, suggestion in enumerate(options):
        # 各提案に対してチェックボックスを作成
        if st.checkbox(suggestion, key=f"suggestion_cb_{i}"):
            # チェックされた場合、その提案をリストに追加
            selected_options.append(suggestion)
    # --- ここまでが変更箇所 ---
    
    custom_option = st.text_input("その他、独自の改善案があれば入力してください:")

    if st.button("次へ進む", disabled=not (selected_options or custom_option)):
        final_suggestions = selected_options
        if custom_option:
            final_suggestions.append(custom_option)
        st.session_state.user_inputs['selected_suggestions'] = final_suggestions
        st.session_state.conversation_step = 5
        st.rerun()

elif st.session_state.conversation_step == 5:
    st.markdown("選択した改善案を踏まえ、未来にどのような姿になってほしいか、あなたの構想を具体的に記述してください。")
    
    vision = st.text_area(
        "未来の構想を教えてください。",
        placeholder="例：誰もが手頃な価格で利用できるようになり、持続可能なエネルギーで動作することで、私たちの生活をより豊かにしてほしい。",
        key="vision_input"
    )
    
    if st.button("次へ進む", disabled=not vision):
        st.session_state.user_inputs['vision'] = vision
        st.session_state.conversation_step = 6
        st.rerun()

elif st.session_state.conversation_step == 6:
    st.subheader("入力内容の確認")
    st.markdown("以下の内容でAPモデルとSF小説を構築します。よろしければ生成を開始してください。")
    
    st.markdown(f"**分析するテーマ:**")
    st.info(st.session_state.selected_topic)
    
    st.markdown(f"**現状の評価:**")
    st.info(f"{st.session_state.user_inputs['score']} / 10点")

    st.markdown(f"**問題点:**")
    st.info(st.session_state.user_inputs['reason'])

    st.markdown(f"**選択した改善案:**")
    st.info("\n".join([f"- {s}" for s in st.session_state.user_inputs['selected_suggestions']]))

    st.markdown(f"**未来の構想:**")
    st.info(st.session_state.user_inputs['vision'])
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("APモデルとSF小説を生成", type="primary"):
            st.session_state.conversation_step = 7
            st.rerun()
    with col2:
        if st.button("最初からやり直し"):
            # Reset all states
            keys_to_reset = [
                'conversation_step', 'user_inputs', 
                'selected_topic', 'ap_history', 
                'descriptions', 'story', 'generating', 'generated_suggestions'
            ]
            for key in keys_to_reset:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

elif st.session_state.conversation_step == 7:
    if not st.session_state.generating:
        st.session_state.generating = True
        
        imagination = f"""
【現状評価】: {st.session_state.user_inputs['score']}点
【問題点】: {st.session_state.user_inputs['reason']}
【選択された改善案】: {', '.join(st.session_state.user_inputs['selected_suggestions'])}
【未来構想】: {st.session_state.user_inputs['vision']}
"""
        
        progress_bar = st.progress(0, text="生成プロセスを開始します...")
        ap_history = []
        descriptions = []
        
        try:
            # Stage 1: Tavily-based analysis
            progress_bar.progress(0.1, text="第1段階：Web情報に基づくAPモデルを構築中...")
            introduction, ap_model = build_stage1_ap_with_tavily(st.session_state.selected_topic, progress_bar)
            descriptions.append(introduction)
            ap_history.append({"stage": 1, "ap_model": ap_model})
            
            # Stage 2: Future evolution
            progress_bar.progress(0.4, text="第2段階：未来展望（離陸期）のシナリオを生成中...")
            introduction2, tech_resources2, daily_experience2 = update_to_next_stage(
                st.session_state.selected_topic, ap_history, descriptions, imagination, 2
            )
            descriptions.append(introduction2)
            progress_bar.progress(0.55, text="第2段階：未来展望（離陸期）のAPモデルを構築中...")
            ap_model2 = update_ap_model(st.session_state.selected_topic, ap_history, descriptions, tech_resources2, daily_experience2, 2)
            ap_history.append({"stage": 2, "ap_model": ap_model2})
            
            # Stage 3: Maturity stage
            progress_bar.progress(0.7, text="第3段階：未来展望（成熟期）のシナリオを生成中...")
            introduction3, tech_resources3, daily_experience3 = update_to_next_stage(
                st.session_state.selected_topic, ap_history, descriptions, imagination, 3
            )
            descriptions.append(introduction3)
            progress_bar.progress(0.85, text="第3段階：未来展望（成熟期）のAPモデルを構築中...")
            ap_model3 = update_ap_model(st.session_state.selected_topic, ap_history, descriptions, tech_resources3, daily_experience3, 3)
            ap_history.append({"stage": 3, "ap_model": ap_model3})
            
            # Generate story
            progress_bar.progress(0.9, text="最終段階：SF短編小説を生成中...")
            story = generate_story(st.session_state.selected_topic, ap_history, descriptions)
            
            # Store results
            st.session_state.ap_history = ap_history
            st.session_state.descriptions = descriptions
            st.session_state.story = story
            st.session_state.generating = False
            
            progress_bar.progress(1.0, text="✅ 生成完了！")
            time.sleep(1)
            progress_bar.empty()
            
            st.session_state.conversation_step = 8
            st.rerun()
            
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")
            st.session_state.generating = False

elif st.session_state.conversation_step == 8:
    st.subheader("🎉 生成結果")
    
    st.markdown("### 📈 進化段階")
    stages = ["第1段階：揺籃期", "第2段階：離陸期", "第3段階：成熟期"]
    
    for i, stage_name in enumerate(stages):
        with st.expander(stage_name):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**説明:**")
                st.markdown(st.session_state.descriptions[i])
            with col2:
                st.markdown("**APモデル要素数:**")
                model = st.session_state.ap_history[i]["ap_model"]
                st.markdown(f"- 対象数: {len(model.get('nodes', []))}/6")
                st.markdown(f"- 射数: {len(model.get('arrows', []))}/12")
    
    st.markdown("### 📚 生成されたSF短編小説")
    with st.expander("SF小説を表示", expanded=True):
        st.markdown(st.session_state.story)
    
    st.markdown("---")
    st.subheader("アクション")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔎 APモデルを可視化", type="primary"):
            st.session_state.page = "visualization"
            st.rerun()
    
    with col2:
        st.download_button(
            label="📥 SF小説をダウンロード",
            data=st.session_state.story,
            file_name="sf_story.txt",
            mime="text/plain"
        )
    
    with col3:
        user_interaction_data = {
            "selected_topic": st.session_state.selected_topic,
            "inputs": {
                "score": st.session_state.user_inputs.get('score'),
                "reason": st.session_state.user_inputs.get('reason'),
                "selected_suggestions": st.session_state.user_inputs.get('selected_suggestions'),
                "future_vision": st.session_state.user_inputs.get('vision')
            }
        }
        user_interaction_json = json.dumps(user_interaction_data, ensure_ascii=False, indent=2)
        st.download_button(
            label="📥 ユーザー入力をダウンロード",
            data=user_interaction_json,
            file_name="user_interaction.json",
            mime="application/json"
        )

    st.markdown("---")
    if st.button("🔄 新しい物語を生成"):
        keys_to_reset = [
            'conversation_step', 'user_inputs',
            'selected_topic', 'ap_history', 
            'descriptions', 'story', 'generating', 'generated_suggestions'
        ]
        for key in keys_to_reset:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

# Sidebar information
with st.sidebar:
    st.header("📖 APモデルについて")
    st.markdown("""
    **アーキオロジカル・プロトタイピング（AP）モデル**は、社会文化を18の要素（6つの対象と12の射）で分析するモデルです。
    
    **Sカーブ進化モデル**:
    - **第1段階（揺籃期）**: 既存問題の解決と改善
    - **第2段階（離陸期）**: 急速な技術発展
    - **第3段階（成熟期）**: 安定した成熟状態
    """)
    
    if st.session_state.conversation_step > 0:
        st.markdown("---")
        st.markdown("**現在の進行状況:**")
        
        steps = [
            "興味の入力",      # 0
            # "テーマ選択" is removed, but we keep numbering for logic simplicity
            "現状評価",        # 2
            "問題点入力",      # 3
            "改善案選択",      # 4
            "未来構想",        # 5
            "内容確認",        # 6
            "モデルと小説生成",# 7
            "結果表示"         # 8
        ]
        
        # A map to correctly associate step number with display text
        step_map = {0: "興味の入力", 2: "現状評価", 3: "問題点入力", 4: "改善案選択", 5: "未来構想", 6: "内容確認", 7: "モデルと小説生成", 8: "結果表示"}
        
        current_step = st.session_state.conversation_step

        for step_num, step_name in step_map.items():
            if step_num < current_step:
                st.markdown(f"✅ {step_name}")
            elif step_num == current_step:
                st.markdown(f"➡️ **{step_name}**")
            else:
                st.markdown(f"⭕ {step_name}")


st.sidebar.markdown("---")
st.sidebar.markdown("Made by Zhang Menghan using Streamlit")
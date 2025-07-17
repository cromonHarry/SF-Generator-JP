# 🚀 近未来SF生成器

**Streamlitベースのアプリケーション**で、現実世界の製品とユーザー体験に基づいて、**Sカーブモデル**と**アーキオロジカル・プロトタイピング（AP）モデル**に基づく**3段階発展タイムライン**と**SF短編小説**を生成します。

## ✨ 新機能（改良版）

- **多段階対話式インターフェース**による直感的な入力体験
- **Tavily自動検索**による現実的なデータ基盤
- **未来展望**に基づくAPモデル進化
- **インタラクティブ可視化**によるAPモデル表示
- **日本語完全対応**

## 🔍 主な機能

### 📝 段階的入力プロセス
1. **興味のある事柄**の入力
2. **Tavily検索結果**からテーマ選択
3. **未来の発展方向**選択（技術革新・体験向上・環境保護）
4. **未来のビジョン**記述
5. **個人的なシナリオ**記述

### 🎯 自動生成コンテンツ
- **3段階技術進化タイムライン**（Sカーブモデル基盤）
  - 第1段階：揺籃期（現実のWikipediaデータ基盤）
  - 第2段階：離陸期（ユーザーの未来展望基盤）
  - 第3段階：成熟期（発展プロセス完成）
- **社会文化背景変化**（APモデル基盤）
- **SF短編小説**（1000字程度）

### 📊 可視化機能
- **APモデルインタラクティブ可視化**
- **6つの対象**と**12の射**の関係性表示
- **段階間の進化**可視化

### 💾 ダウンロード機能
- APモデルデータ（`ap_model.json`）
- 段階別説明（`description.json`）
- SF短編小説（`sf_story.txt`）

## 📦 インストール

1. リポジトリをクローン:
   ```bash
   git clone https://github.com/yourusername/sf-generator-jp.git
   cd sf-generator-jp
   ```

2. 依存関係をインストール:
   ```bash
   pip install -r requirements.txt
   ```

3. OpenAI APIキーを環境変数として追加:
   ```bash
   export OPENAI_API_KEY=your-api-key
   ```

4. アプリを実行:
   ```bash
   streamlit run app.py
   ```

## 🌐 Streamlit Cloudでの使用

アプリはStreamlit Cloudでも利用可能です：
[https://sf-generator-jp.streamlit.app/](https://sf-generator-jp.streamlit.app/)

### Secrets設定
Streamlit Cloudのプロジェクト設定で以下を追加:
```toml
[openai]
api_key = "your-openai-api-key-here"
```

## 🧠 使用モデル

- **OpenAI GPT-4o** - テキスト生成・分析
- **Tavily API** - 現実データ取得

## 📊 APモデルについて

**アーキオロジカル・プロトタイピング（AP）モデル**は18の要素で社会文化を分析するモデルです：

[デザインにおける考古学のレジリエンスモデル : アーキオロジカル・プロトタイピングの可能性](https://www.ritsumei.ac.jp/research/rcds/file/2023/7_rcds_2_nakamura_goto.pdf)

## 📈 Sカーブモデル

### 3段階の技術進化
1. **第1段階：揺籃期** - 既存問題の解決と改善
2. **第2段階：離陸期** - 急速な技術発展
3. **第3段階：成熟期** - 安定した成熟状態

## 🧪 使用例

1. **興味**: スマートフォン
2. **発展方向**: 技術革新
3. **未来ビジョン**: より直感的で環境に優しい通信デバイス
4. **個人シナリオ**: 私は新しい技術を使って家族とのコミュニケーションを深めたい
➡️ 未来の影響を想像したオリジナル小説を生成

## 💻 技術的な特徴

### フロントエンド
- **Streamlit** - インタラクティブWebアプリ
- **HTML/CSS/JavaScript** - カスタム可視化

### バックエンド
- **Python** - 主要プログラミング言語
- **OpenAI API** - AI生成
- **Tavily API** - データ取得

### データ処理
- **JSON** - データ保存・交換
- **Session State** - アプリケーション状態管理

## 🔧 技術要件

- Python 3.12
- streamlit==1.45.0
- openai==1.77.0
- pillow==10.2.0
- networkx==3.2.1
- matplotlib==3.9.2
- pandas==2.2.2
- wikipedia==1.4.0
- tavily-python==0.7.7


## 🤝 貢献

プルリクエストやイシューの報告を歓迎します！

## 📄 謝辞

- [Streamlit](https://streamlit.io/) - Webアプリフレームワーク
- [OpenAI](https://openai.com/) - AI生成エンジン
- [Wikipedia](https://www.wikipedia.org/) - データソース
- [Sカーブモデル](https://www.the-waves.org/2022/03/13/innovation-s-curve-episodic-innovation-evolution/) - 技術進化理論

## 📜 ライセンス

MIT License

## 🔗 関連リンク

- [ライブデモ](https://sf-generator-jp.streamlit.app/)
- [プロジェクトリポジトリ](https://github.com/cromonharry/sf-generator-jp)
- [問題報告](https://github.com/cromonharry/sf-generator-jp/issues)

---

**Made by Zhang Menghan using Streamlit**

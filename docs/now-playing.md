# Now Playing (YouTube Music履歴連携)

## 目的
README の `Now Playing` を Spotify カードから切り替え、YouTube Music の**最近再生履歴**を自前SVGとして安定表示するための仕組みです。

## 仕組み
1. `ytmusicapi` で YouTube Music 履歴を取得
2. `scripts/generate-now-playing.py` が `assets/now-playing.svg` を生成
3. GitHub Actions が定期実行で SVG を更新
4. README は生成済みSVGのみ表示（READMEからAPIは直接呼ばない）

## ytmusicapi を使う理由
- Python で扱いやすく、履歴取得機能（`get_history()`）がある
- GitHub Actions でバッチ更新しやすい
- README埋め込み制約（外部JS/iframe不可）に適した静的SVG運用ができる

## リスク（非公式API依存）
- `ytmusicapi` は YouTube Music の公式公開APIではないため、仕様変更で壊れる可能性があります
- 認証ヘッダー形式が将来変わる可能性があります
- YouTube Music 側の履歴設定やアカウント状態で取得結果が変わることがあります

## Secrets に必要な値
- `YTMUSIC_AUTH_JSON_BASE64`
  - `ytmusicapi` の認証JSON（例: `browser.json` / `headers_auth.json` 相当）を base64 で格納

## 認証情報の作り方
1. ローカルで `pip install ytmusicapi`
2. `YTMusic.setup(filepath="browser.json")` を実行し、ブラウザヘッダーから認証JSONを作成
3. `base64 -w 0 browser.json`（macOSは `base64 browser.json | tr -d '\n'`）で1行base64化
4. GitHub リポジトリの Secrets に `YTMUSIC_AUTH_JSON_BASE64` として保存

## ローカル実行方法
```bash
pip install -r requirements-now-playing.txt
mkdir -p .secrets
# 例: 既存の認証JSONを配置
cp /path/to/browser.json .secrets/ytmusic-auth.json
python scripts/generate-now-playing.py
```

## GitHub Actionsでの更新
- workflow: `.github/workflows/update-now-playing.yml`
- トリガー:
  - 6時間おきの schedule
  - 手動実行 (`workflow_dispatch`)
- 差分があるときだけ `assets/now-playing.svg` をコミット

## 失敗時の挙動
- 取得失敗時:
  - 前回 `assets/now-playing.svg` があれば維持
  - 前回ファイルが無ければ fallback SVG を生成
- 履歴0件時:
  - `No recent YouTube Music history` を表示

## よくあるトラブル
- Secret未設定: 認証に失敗し、前回SVG維持またはfallback表示
- base64不正: decode失敗で更新不可
- 認証ファイル不正: `YTMusic(...)` 初期化失敗
- 履歴が空: 履歴設定オフ、または履歴が十分に存在しない
- YouTube本体履歴が混ざる: スクリプト側で音楽アイテム優先選別

## セキュリティ注意
- 認証情報は**絶対にコミットしない**（`.secrets/` はgit管理外）
- GitHub Actionsログに認証情報を出さない
- 例外メッセージやSVGに認証データを含めない
- PR from fork では Secrets が使えない前提で運用する
- この表示は「現在再生中」ではなく「最近再生履歴」を扱う

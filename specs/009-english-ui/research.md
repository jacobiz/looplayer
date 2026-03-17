# Research: 英語 UI 対応

**Feature**: `009-english-ui`
**Date**: 2026-03-16

---

## 1. i18n 実装方式の選択

**Decision**: Python dict ベースの `t(key)` 関数（`looplayer/i18n.py` 新規作成）

**Rationale**:
- 翻訳対象が約 50 件と小規模。Qt の QTranslator + lupdate + lrelease ツールチェーンは過剰。
- Python の `gettext` は `.po`/`.mo` ファイルのビルドステップが必要で、PyInstaller バンドル時の複雑さが増す。
- シンプルな Python dict であれば追加ライブラリなし、ビルドステップなし、PyInstaller との相性も問題なし。
- 憲法 II（シンプルさ）・III（過度な抽象化の禁止）に完全準拠。

**Alternatives considered**:
- **Qt QTranslator + .ts/.qm**: 外部ツール（`pylupdate6`, `lrelease`）が必要。CI での自動化が複雑。本規模には過剰。
- **Python gettext**: `.po`/`.mo` ビルドステップが必要。PyInstaller バンドル時にデータファイルの同梱設定が必要になり、複雑さが増す。
- **Qt の `self.tr()`**: QObject サブクラスでのみ使用可能。モジュールレベルの文字列には使えない。

---

## 2. ロケール検出方式

**Decision**: `QLocale.system().language()` を `looplayer/i18n.py` モジュール読み込み時に一度だけ評価し、モジュールレベル変数 `_lang` に保存する

```python
from PyQt6.QtCore import QLocale

_lang: str  # "ja" または "en"

def _detect_lang() -> str:
    if QLocale.system().language() == QLocale.Language.Japanese:
        return "ja"
    return "en"

_lang = _detect_lang()
```

**Rationale**:
- `QLocale.system()` は Windows レジストリ・macOS CFLocale・Linux `LANG` 環境変数を統一的に参照する。プラットフォーム差異を PyQt6 が吸収する。
- モジュール読み込み時に一度だけ評価することで FR-006（起動時に決定）を自然に満たす。
- テスト時は `i18n._lang = "en"` で差し替え可能（monkeypatch）。

**Alternatives considered**:
- `locale.getlocale()` (Python 標準): Windows での挙動が不安定。PyQt6 の QLocale の方が信頼性が高い。
- `os.environ.get("LANG")`: macOS/Linux のみ。Windows 非対応。

---

## 3. 文字列キー設計

**Decision**: ドット区切りの階層キー（例: `"menu.file"`, `"btn.play"`, `"msg.file_not_found"`）

**Rationale**:
- フラットなキーより意図が明確で補完が効きやすい。
- 衝突リスクが低い。
- 辞書の構造はフラット（ネストしない）— ネストは過剰抽象化（憲法 III）。

**Alternatives considered**:
- 日本語テキストをキーにする（例: `t("ファイル")` → `"File"`）: キーが壊れやすく、日本語環境でも `t()` を呼ぶ必要が生じて冗長。

---

## 4. テスト戦略

**Decision**: `monkeypatch` で `looplayer.i18n._lang` を差し替えてテスト

```python
def test_t_returns_english(monkeypatch):
    import looplayer.i18n as i18n
    monkeypatch.setattr(i18n, "_lang", "en")
    assert i18n.t("menu.file") == "File"

def test_t_returns_japanese(monkeypatch):
    import looplayer.i18n as i18n
    monkeypatch.setattr(i18n, "_lang", "ja")
    assert i18n.t("menu.file") == "ファイル(&F)"
```

**Rationale**:
- QLocale を呼ばずに完全なユニットテストが可能。
- QApplication を起動しなくてよいため高速。
- 未登録キーのフォールバック挙動（キー文字列をそのまま返す）もテスト可能。

---

## 5. 既存コードへの影響範囲

翻訳対象ファイルと文字列数（概算）:

| ファイル | 翻訳文字列数 |
|----------|-------------|
| `looplayer/player.py` | 約 40 件 |
| `looplayer/widgets/bookmark_panel.py` | 約 6 件 |
| `looplayer/widgets/bookmark_row.py` | 約 5 件 |
| 合計 | 約 51 件 |

---

## NEEDS CLARIFICATION 解決済み

すべての技術的不確実性は本 research.md で解消された。

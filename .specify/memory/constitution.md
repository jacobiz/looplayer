<!--
SYNC IMPACT REPORT
==================
Version change: [TEMPLATE] → 1.0.0 (initial ratification)

Modified principles:
  [PRINCIPLE_1_NAME] → I. テストファースト
  [PRINCIPLE_2_NAME] → II. シンプルさ重視
  [PRINCIPLE_3_NAME] → III. 過度な抽象化の禁止
  [PRINCIPLE_4_NAME] → IV. 日本語コミュニケーション
  [PRINCIPLE_5_NAME] → (removed — 4 principles sufficient)

Added sections: (none beyond template structure)
Removed sections: [SECTION_2_NAME], [SECTION_3_NAME] merged into Development Workflow

Templates reviewed:
  ✅ .specify/templates/plan-template.md — Constitution Check section compatible
  ✅ .specify/templates/spec-template.md — test-first mandate reflected in User Scenarios section
  ✅ .specify/templates/tasks-template.md — test-before-implementation note already present

Deferred items: (none)
-->

# Video Player Constitution

## Core Principles

### I. テストファースト (NON-NEGOTIABLE)

実装前にテストを書くことが必須。手順は以下の通り:

1. テストを書く
2. テストが **失敗する** ことを確認する
3. 最小限のコードで **通過させる**
4. リファクタリング

- テストなしの実装コードは原則マージしない
- ユーザーストーリー単位で独立してテスト可能な設計にすること
- 統合テストはモックではなく実際の依存を使う
  (モックによるテスト通過が本番バグを隠蔽した過去事例に基づく)

### II. シンプルさ重視

- YAGNI: 今必要でない機能は作らない
- 最もシンプルな実装が常に第一候補
- 複雑さを導入する場合は、その必然性を `plan.md` の Complexity Tracking に記録すること
- 3行の重複コードは早まった抽象化より優る

### III. 過度な抽象化の禁止

- 1箇所だけで使うヘルパー・ユーティリティクラスは作らない
- 「将来の拡張」を理由にした抽象レイヤーは認めない
- 直接的なコードが読めるなら、ラッパーは不要
- Repository パターン・Factory・Manager 等のパターンは、
  具体的な問題が存在する場合のみ使用可（Complexity Tracking に記録必須）

### IV. 日本語コミュニケーション

- AIへの応答・仕様書・コメント・コミットメッセージは日本語で記述する
- UIラベルは日本語（既存コードの慣習に従う）
- エラーメッセージはユーザー向けは日本語、ログ・例外メッセージは英語可

## Development Workflow

- フィーチャーブランチは `###-feature-name` 形式
- 各ユーザーストーリーは独立して実装・テスト・デモ可能な単位とする
- チェックポイントごとにテストをパスさせてからコミットする
- `plan.md` の Complexity Tracking を使って意図的な複雑さを正当化する

## Governance

この憲法はすべての他の慣習・ガイドラインより優先される。

改定手順:
1. 改定案を PR に記載する
2. バージョンをセマンティックバージョニングに従って上げる
   - MAJOR: 原則の削除・再定義（後方非互換）
   - MINOR: 原則の追加・大幅な拡張
   - PATCH: 表現の明確化・誤字修正
3. `LAST_AMENDED_DATE` を更新する
4. 依存テンプレートの整合性を確認する

すべての PR レビューで憲法遵守を確認すること。
複雑さの正当化なき違反は差し戻す。

**Version**: 1.0.0 | **Ratified**: 2026-03-15 | **Last Amended**: 2026-03-15

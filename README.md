# videocc

動画字幕の多言語切り替えの PoC。1 枚の HTML で、同じ MP4 に ja と en の WebVTT を `<track>` で添え、プレイヤーの描画方式ごとの見え方を比べる。

公開ページ: https://go-surgeons.github.io/videocc/

元の調査は marsimik の `docs/plans/2026-11-02-video-subtitles-research.md` で、この PoC はその 9 章「静的な VTT を 1 本置いて実機で確かめる」に当たる。使い捨ての検証用で、製品コードではない。

## 構成

- `index.html` がページ本体。Video.js 8.24.1 を CDN から読む（marsimik の importmap と同じ版）。
- `media/sample.mp4` は ffmpeg で生成した 60 秒のテストパターン。中央の時計が再生位置を示す。
- `subs/ja.vtt` と `subs/en.vtt` は同じ時刻の cue を持つ。
- `verify.mjs` はローカルで配信し、headless Chrome で各バリアントの状態とスクリーンショットを取る。

## 使い方

ページの設定は URL のクエリに載る。`?variant=vjs&lang=ja&zoom=200&t=12` のように組んで、実機の Safari や iPhone に送れる。

- `variant`: `vjs`（Video.js 既定）、`vjsNoNative`（`nativeTextTracks: false`）、`native`（ブラウザ標準の `<video controls>`）
- `lang`: `ja`、`en`、`off`
- `zoom`: 100〜200。ds 画面の拡大 transform を内側の `<video>` にかける
- `playsinline=1`: `<video>` に `playsinline` を付ける
- `t`: 開始位置（秒）

## 検証

```
node verify.mjs shots
```

Chrome のパスは環境変数 `CHROME` で変えられる。公開ページに対して撮るときは第 2 引数にベース URL を渡す。

# videocc

動画字幕の多言語切り替えの PoC。1 枚の HTML で、同じ MP4 に ja と en の WebVTT を `<track>` で添え、プレイヤーの描画方式ごとの見え方を比べる。

公開ページ: https://go-surgeons.github.io/videocc/

元の調査は marsimik の `docs/plans/2026-11-02-video-subtitles-research.md` で、この PoC はその 9 章「静的な VTT を 1 本置いて実機で確かめる」に当たる。使い捨ての検証用で、製品コードではない。

## 構成

- `index.html` がページ本体。Video.js 8.24.1 を CDN から読む（marsimik の importmap と同じ版）。
- `media/emics.mp4` は go-surgeons.com の教材「EMI ノットプッシャー EMICS150、150C の使い方」(11 分 15 秒、無音)を 640x480 の H.264 に変換したもの。4:20〜9:05 の実演には焼き込み字幕がある。
- `subs/ja.vtt` と `subs/en.vtt` は `make_subs.py` の表から生成する。動画が無音なので、cue はスライドと焼き込み字幕を 10 秒刻みのフレームから文字起こししたもので、時刻は ±5 秒の目安。字幕を直すときは `make_subs.py` を編集して再実行する。
- `verify.mjs` はローカルで配信し、headless Chrome で各バリアントの状態とスクリーンショットを取る。配信は Range 対応の自前サーバーで行う。Range を返さないサーバー(`python3 -m http.server` など)だと Chrome が動画をシーク不可と扱い、`t` の指定が効かない。

## 使い方

ページの設定は URL のクエリに載る。`?variant=vjs&lang=ja&zoom=200&t=12` のように組んで、実機の Safari や iPhone に送れる。

- `variant`: `vjs`（Video.js 既定）、`vjsNoNative`（`nativeTextTracks: false`）、`native`（ブラウザ標準の `<video controls>`）
- `lang`: `ja`、`en`、`off`
- `zoom`: 100〜200。ds 画面の拡大 transform を内側の `<video>` にかける。4:3 の動画を 16:9 の枠で cover にする ds の初期倍率は 133% に当たる
- `playsinline=1`: `<video>` に `playsinline` を付ける
- `t`: 開始位置（秒）

ページ下部の QR コードは、そのときの設定を含んだ URL を指す。

## 検証

```
node verify.mjs shots
```

Chrome のパスは環境変数 `CHROME` で変えられる。公開ページに対して撮るときは第 2 引数にベース URL を渡す。

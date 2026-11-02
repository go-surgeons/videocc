#!/usr/bin/env python3
"""subs/ja.vtt と subs/en.vtt を 1 つの表から生成する。

動画 media/emics.mp4(「EMI ノットプッシャー EMICS150, 150C の使い方」)は無音なので、
cue はスライドと焼き込み字幕の文字起こし。時刻は 10 秒刻みのフレーム目視で決めたので
±5 秒の誤差がある。4:20〜9:05 は焼き込み字幕のある実演で、二重表示の確認に使う。

使い方: python3 make_subs.py
"""
from pathlib import Path

CUES = [
    # (開始, 終了, ja, en)
    ("0:00.5", "0:07.5", "EMI ノットプッシャー\nEMICS150、150C の使い方", "How to use the EMI knot pusher\nEMICS150 and 150C"),
    ("0:07.7", "0:09.3", "名古屋第一赤十字病院 伊藤敏明", "Toshiaki Ito, Japanese Red Cross\nNagoya Daiichi Hospital"),
    ("0:09.5", "0:14.0", "EMICS 150 の特徴\n引き上げる際に隣接する糸や腱索を\n巻き込みにくい円形ヘッド", "Features of the EMICS 150\nA round head that avoids catching nearby\nsutures or chordae when lifted"),
    ("0:14.2", "0:19.5", "糸を損傷しにくいピン型スーチャーキャッチャー\n糸が外れにくい深溝、抵抗が少ない鏡面加工溝", "A pin-type suture catcher that spares the thread\nA deep, mirror-polished groove with low friction"),
    ("0:20.0", "0:29.5", "右利きの場合の糸の持ち方\nクロスして持たない方が混乱しにくい", "Holding the threads (right-handed)\nNot crossing them causes less confusion"),
    ("0:30.0", "0:34.5", "ループを作る\n① 左手ワンハンドで一回ループを作る", "Make a loop\n1. Make one loop one-handed with the left hand"),
    ("0:34.7", "0:39.5", "② 助手に渡し、軽く牽引してもらう\nこの糸が以後「軸糸」となる", "2. Hand it to the assistant for gentle traction\nThis thread becomes the \"axis thread\""),
    ("0:40.0", "0:45.0", "Knot pusher に糸をかける\nSuture catcher の溝に糸をはめる", "Load the thread on the knot pusher\nSeat the thread in the suture catcher groove"),
    ("0:45.2", "0:49.5", "左示指をノットに添える\n右手の糸は助手が牽引している", "Rest the left index finger on the knot\nThe assistant keeps traction on the right thread"),
    ("0:50.0", "0:56.0", "Knot pusher を時計回りに反転", "Rotate the knot pusher clockwise"),
    ("0:56.5", "1:02.5", "Step 1\nノットプッシャーを降ろす前に\n軸糸を拇指、示指でつまむ", "Step 1\nBefore lowering the knot pusher,\npinch the axis thread with thumb and index"),
    ("1:02.7", "1:09.5", "両方の糸に均等にテンションをかけ\nノットプッシャーの溝にしっかりはめる\n助手は軽く持つだけ", "Apply even tension to both threads\nand seat them firmly in the groove\nThe assistant only holds lightly"),
    ("1:10.0", "1:15.0", "Step 2\n手首を橈側に返すと非軸糸が軽くたるむ", "Step 2\nTilting the wrist radially slackens\nthe non-axis thread slightly"),
    ("1:15.2", "1:19.5", "この状態でノットプッシャーを降ろすと\nスムーズに降りる (Tilting wrist technique)", "Lowering the knot pusher in this state\nslides smoothly (tilting wrist technique)"),
    ("1:20.0", "1:29.5", "Step 3\n手首を戻す。ノットプッシャーを押す", "Step 3\nReturn the wrist. Push the knot pusher"),
    ("1:30.0", "1:39.5", "戻す\n助手は軽く牽引を続ける", "Return\nThe assistant keeps gentle traction"),
    ("1:40.0", "1:49.5", "2 回目ループ\n左手ワンハンドで最初と同じ方向で\nループを作る(女結び)", "Second loop\nMake a loop one-handed in the same direction\nas the first (granny knot)"),
    ("1:50.0", "1:59.5", "Step 1 繰り返し\nノットプッシャーを降ろす前に\n軸糸を指でつまむ", "Repeat step 1\nPinch the axis thread with your fingers\nbefore lowering the knot pusher"),
    ("2:00.0", "2:05.0", "二回目の結紮では軸糸を拇指、示指で\nつまみ強く牽引する", "On the second throw, pinch the axis thread\nwith thumb and index and pull firmly"),
    ("2:05.2", "2:09.5", "手首を橈側に返して軸糸を引いて締める\nslip knot technique の応用", "Tilt the wrist radially and pull the axis thread\nto tighten. An application of the slip knot technique"),
    ("2:10.0", "2:39.5", "Slip knot technique の原理", "The principle of the slip knot technique"),
    ("2:40.0", "2:49.5", "3 回目、左手ワンハンドで\n最初と反対の方法でループを作る(男結び)", "Third throw: make a loop one-handed\nthe opposite way from the first (square knot)"),
    ("2:50.0", "2:59.5", "Step 2\n手首を橈側に返すと非軸糸が軽くたるむ", "Step 2\nTilting the wrist radially slackens\nthe non-axis thread slightly"),
    ("3:00.0", "3:09.5", "糸を締めるのは誰の力?\n助手の牽引力に頼らず、術者が両糸を\n左手で持って自分で締める", "Whose force tightens the knot?\nNot the assistant's traction. The surgeon holds\nboth threads in the left hand and tightens"),
    ("3:10.0", "3:19.5", "ノットプッシャーを押し付ける力を\nカウンタートラクションとして、\n組織が引っ張られて切れるのを防ぐ", "Use the pushing force of the knot pusher\nas counter-traction so the tissue\nis not pulled and torn"),
    ("3:20.0", "3:29.5", "4 回目以降の締め方\n軸糸の牽引を左糸よりやや弱くし、\n左手首を軽く尺側に tilt して均等に締める", "Tightening from the fourth throw on\nPull the axis thread slightly less than the left,\ntilt the left wrist ulnarly and tighten evenly"),
    ("3:30.0", "3:39.5", "Pitfall\n軸糸に巻きついただけの結紮にならない様にする", "Pitfall\nAvoid a throw that merely wraps around\nthe axis thread"),
    ("3:40.0", "3:49.5", "Pitfall\n左手の糸を強く引きすぎると結節が Lock して降りない\n大文字 Y はダメ", "Pitfall\nPulling the left thread too hard locks the knot\nNo capital \"Y\""),
    ("3:50.0", "3:59.5", "結紮の作り方と牽引の仕方\n1〜3 回目は軸糸を強く引き、\n4〜6 回目は左糸を強く引く", "How to form and pull each throw\nPull the axis thread hard on throws 1 to 3,\nthe left thread on throws 4 to 6"),
    ("4:00.0", "4:04.5", "まとめ 1 ノットをスムーズに送るためには\n助手の唯一の仕事は、軸糸が軽く張る\n一定の力で引き続けること", "Summary 1: sending the knot smoothly\nThe assistant's only job is steady, light\ntraction on the axis thread"),
    ("4:04.7", "4:09.5", "術者は 2 本の糸を左手で持ち、溝にかけて\n均等にテンションをかけ、左手を橈側に返して\n非軸糸を緩めてから押す", "The surgeon holds both threads in the left hand,\nseats them, applies even tension, tilts the wrist\nto slacken the non-axis thread, then pushes"),
    ("4:10.0", "4:14.5", "まとめ 2 強固な結紮を作るためには\n軸糸の根本にノットを作る\n2 回目女結びで軸糸を強く引いて締めこむ", "Summary 2: making a firm knot\nForm the knot at the base of the axis thread\nOn the second throw (granny), pull the axis thread hard"),
    ("4:14.7", "4:19.5", "2 本の糸を左手で持ち術者が締め加減を調節\n4 回目以降は左手首の角度で左糸も十分牽引する", "The surgeon controls the tightening with both threads\nFrom the fourth throw, angle the left wrist\nto pull the left thread too"),
    ("4:20.0", "4:44.5", "EMICS150 使い方 ½ 速ビデオ", "How to use the EMICS150 (half speed)"),
    ("4:45.0", "4:49.5", "右糸を助手に渡し、「軸糸」とします", "Hand the right thread to the assistant\nas the axis thread"),
    ("4:50.0", "4:59.5", "ノットプッシャーのピンに糸をかけます", "Load the thread on the knot pusher pin"),
    ("5:00.0", "5:04.5", "右 180 度回転", "Rotate 180 degrees to the right"),
    ("5:05.0", "5:09.5", "軸糸を左拇指示指でつまみ、\n左右溝に糸をしっかりかけます", "Pinch the axis thread with the left thumb and index\nand seat the threads firmly in both grooves"),
    ("5:10.0", "5:14.5", "ノットプッシャーを降ろします", "Lower the knot pusher"),
    ("5:15.0", "5:19.5", "同方向に 2 回目ノットを作り", "Make the second throw in the same direction"),
    ("5:20.0", "5:29.5", "左手首を橈側に返しながら締めこみます", "Tighten while tilting the left wrist radially"),
    ("5:30.0", "5:39.5", "手首を軽く橈側に返します", "Tilt the wrist slightly radially"),
    ("6:00.0", "6:09.5", "手首を返して、ノットを降ろします", "Tilt the wrist and lower the knot"),
    ("7:20.0", "7:24.5", "取っ手を離しています", "The handle is released"),
    ("7:25.0", "7:29.5", "自重だけで降りていきます", "It slides down under its own weight"),
    ("8:05.0", "8:09.5", "手首の返しで、非軸糸が極わずかゆるみます", "Tilting the wrist slackens the non-axis thread\nvery slightly"),
    ("8:10.0", "8:14.5", "極端にやりすぎると、糸が溝から外れます", "Overdoing it lets the thread slip out of the groove"),
    ("9:06.0", "9:14.5", "Tilting wrist technique が\nノットプッシャーの「困った」を解決", "The tilting wrist technique solves\nthe knot pusher's common troubles"),
    ("9:14.7", "9:19.5", "糸が溝から外れてしまう\n→ 最初に溝にはめてから送るため、外れにくい", "The thread slips out of the groove\nSeating it first before pushing keeps it in"),
    ("9:19.7", "9:24.0", "糸が引っかかってノットを降ろしにくい\n→ 手首の返しで非軸糸に丁度良い緩みが生じ抵抗が減る", "The thread catches and the knot is hard to lower\nThe wrist tilt gives the non-axis thread just enough slack"),
    ("9:24.2", "9:28.5", "助手に軸糸を引っ張られて対側が短くなってしまう\n→ 最初から軸糸を術者がコントロールする", "The assistant pulls the axis thread and shortens the other side\nThe surgeon controls the axis thread from the start"),
    ("9:29.0", "9:39.5", "EMICS-150C の構造\n閉鎖、ピン型スーチャーキャッチャーを持つ\n小型円形ヘッド", "Structure of the EMICS-150C\nA small round head with a closed,\npin-type suture catcher"),
    ("9:40.0", "9:49.5", "suture catcher に糸を通す", "Pass the thread through the suture catcher"),
    ("9:50.0", "9:59.5", "Step 1\nノットプッシャーを降ろす前に軸糸を指でつまむ\n助手は軽く持つだけ", "Step 1\nPinch the axis thread before lowering the pusher\nThe assistant only holds lightly"),
    ("10:00.0", "10:09.5", "Step 2\n手首を橈側に返すと非軸糸が軽くたるむ", "Step 2\nTilting the wrist radially slackens\nthe non-axis thread slightly"),
    ("10:10.0", "10:19.5", "Step 3\n手首の返しを戻す\nバランス良く糸を牽引して締めこむ。ノットプッシャーを押す", "Step 3\nReturn the wrist\nPull both threads in balance and push the knot pusher"),
    ("10:20.0", "10:25.5", "Pitfall and trouble shooting\n滑りやすい柔軟な糸 ○\n緩みにくい摩擦の大きい糸 △", "Pitfalls and troubleshooting\nSlippery, supple thread: good\nHigh-friction thread that resists loosening: caution"),
    ("10:25.7", "10:29.5", "緩んだままロックしてしまったとき\n⇒ 軸糸を変えて締めてみる", "If the knot locks while still loose,\nswitch the axis thread and tighten again"),
    ("10:30.0", "10:39.5", "Loose knot を避ける", "Avoid a loose knot"),
    ("10:40.0", "10:48.0", "手首をしっかり橈側に返すと軸糸が牽引され\n自然とノットが締めこまれる\nKnot pusher を強く押し付ける", "A firm radial wrist tilt pulls the axis thread\nand tightens the knot naturally\nPress the knot pusher firmly"),
    ("10:49.0", "10:56.0", "軸糸がどちらか、必ず意識して結紮する\n創に向かって糸を牽引した時に、\n浅い方、近い方が軸糸", "Always know which thread is the axis\nWhen pulling toward the wound,\nthe shallower, nearer thread is the axis"),
    ("10:57.0", "11:07.5", "軸糸を決める原理\n手前にある A の糸と奥から出る B の糸、\n軸糸は A", "How to choose the axis thread\nBetween thread A in front and thread B from behind,\nthe axis thread is A"),
    ("11:08.0", "11:14.0", "(終わり)", "(End)"),
]

NOTE = {
    "ja": "日本語トラック。スライドと焼き込み字幕の文字起こし。時刻は目視で ±5 秒。",
    "en": "English track. Translated from the slides and burned-in captions. Timings are approximate.",
}


def timestamp(value: str) -> str:
    minutes, seconds = value.split(":")
    return f"00:{int(minutes):02d}:{float(seconds):06.3f}"


def render(lang: str, index: int) -> str:
    lines = ["WEBVTT", "", f"NOTE {NOTE[lang]}", ""]
    for number, cue in enumerate(CUES, start=1):
        lines += [str(number), f"{timestamp(cue[0])} --> {timestamp(cue[1])}", cue[index], ""]
    return "\n".join(lines)


def main() -> None:
    out = Path(__file__).parent / "subs"
    (out / "ja.vtt").write_text(render("ja", 2), encoding="utf-8")
    (out / "en.vtt").write_text(render("en", 3), encoding="utf-8")
    for a, b in zip(CUES, CUES[1:]):
        assert timestamp(a[1]) <= timestamp(b[0]), f"cue が重なっている: {a[0]} と {b[0]}"
    print(f"{len(CUES)} cues -> subs/ja.vtt, subs/en.vtt")


if __name__ == "__main__":
    main()

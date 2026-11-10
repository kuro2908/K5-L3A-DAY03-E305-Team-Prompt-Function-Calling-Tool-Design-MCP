"""Streamlit UI for the Research Agent (Day 03 Lab v2).

Run from `starter_v0/`:

    streamlit run app.py

This reuses the exact tool-loop logic from `chat.py` (run_model_tool_loop,
trim_history, write_transcript) so a conversation run from this UI produces
the same `transcripts/*.transcript.json` shape that `chat.py` and the report
expect. No tool-calling or grading logic is duplicated here — this file is
only presentation + session state around the existing agent loop.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import streamlit as st

from chat import ROOT, now_iso, run_model_tool_loop, safe_slug, trim_history, write_transcript
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

ARTIFACTS_DIR = ROOT / "artifacts"
TRANSCRIPTS_DIR = ROOT / "transcripts"
PROVIDERS = ["openai"]
HISTORY_WINDOW = 5
MAX_TOOL_ROUNDS = 4

st.set_page_config(page_title="Research Agent", page_icon="🔎", layout="wide")


def init_state() -> None:
    defaults = {
        "configured": False,
        "history": [],
        "turns": [],
        "turn_index": 0,
        "transcript_id": None,
        "transcript_path": None,
        "artifact_version": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


init_state()

st.title("🔎 Research Agent — demo UI")
st.caption("Chat UI cho research agent của nhóm. Dùng để demo Team showdown và sinh transcript JSON cho báo cáo.")

with st.sidebar:
    st.header("Cấu hình")
    provider_name = st.selectbox("Provider", PROVIDERS, index=0)
    version_label = st.text_input("Version label (vd: v3)", value="v3")

    apply_clicked = st.button("▶️ Áp dụng cấu hình / Bắt đầu phiên mới", use_container_width=True)
    reset_clicked = st.button("🗑️ Xoá hội thoại (giữ cấu hình)", use_container_width=True)

    st.divider()
    st.caption(
        "Deploy nhanh để team khác dùng thử:\n\n"
        "```\nstreamlit run app.py\ncloudflared tunnel --url http://localhost:8501\n```\n"
        "Dán link `trycloudflare.com` vào REPORT.md Phần A."
    )

if apply_clicked:
    try:
        # Fixed, non-user-editable paths: this app is exposed publicly via a tunnel,
        # so these must never come from free-text input (arbitrary file read risk).
        sp_path = ARTIFACTS_DIR / "system_prompt.md"
        tl_path = ARTIFACTS_DIR / "tools.yaml"
        system_prompt_text = sp_path.read_text(encoding="utf-8")
        declarations = load_tool_declarations(tl_path)
        openai_tools = to_openai_tools(declarations)
        provider = make_provider(provider_name)
        selected_model = getattr(provider, "default_model", None)
        artifact_version = build_artifact_version(version_label.strip() or "v0", sp_path, tl_path)

        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
        transcript_id = "_".join([safe_slug(version_label or "v0"), safe_slug(provider_name), timestamp])
        transcript_path = TRANSCRIPTS_DIR / f"{transcript_id}.transcript.json"

        st.session_state.update({
            "configured": True,
            "history": [],
            "turns": [],
            "turn_index": 0,
            "transcript_id": transcript_id,
            "transcript_path": str(transcript_path),
            "artifact_version": artifact_version.artifact_version,
            "_provider": provider,
            "_provider_name": provider_name,
            "_model": selected_model,
            "_system_prompt": system_prompt_text,
            "_system_prompt_path": str(sp_path),
            "_tools_path": str(tl_path),
            "_openai_tools": openai_tools,
            "_history_window": HISTORY_WINDOW,
            "_max_tool_rounds": MAX_TOOL_ROUNDS,
            "_artifact_version_dict": artifact_version_dict(artifact_version),
        })
        st.success(f"Đã khởi tạo phiên. artifact_version = {artifact_version.artifact_version}")
    except Exception as exc:
        st.session_state["configured"] = False
        st.error(f"Lỗi khởi tạo: {type(exc).__name__}: {exc}")

if reset_clicked and st.session_state.get("configured"):
    st.session_state["history"] = []
    st.session_state["turns"] = []
    st.session_state["turn_index"] = 0
    st.rerun()

if not st.session_state.get("configured"):
    st.info("Điền cấu hình ở sidebar rồi bấm **Áp dụng cấu hình** để bắt đầu.")
    st.stop()

st.caption(
    f"provider=`{st.session_state['_provider_name']}` · model=`{st.session_state['_model']}` · "
    f"artifact_version=`{st.session_state['artifact_version']}` · "
    f"transcript=`{st.session_state['transcript_path']}`"
)


def render_tool_events(events: list[dict]) -> None:
    if not events:
        return
    with st.expander(f"🔧 {len(events)} tool call(s)"):
        for event in events:
            st.markdown(f"**{event.get('tool')}**")
            st.json(event.get("args", {}))
            st.json(event.get("result", {}))


for turn in st.session_state["turns"]:
    with st.chat_message("user"):
        st.write(turn["user"])
    with st.chat_message("assistant"):
        st.write(turn.get("assistant_text") or "")
        render_tool_events(turn.get("tool_events") or [])
        if turn.get("status") == "waiting_for_user":
            st.info("Agent đang chờ bạn trả lời (clarify).")
        elif turn.get("status") == "provider_error":
            st.error(turn.get("error", "provider_error"))
        elif turn.get("status") == "max_tool_rounds":
            st.warning("Agent dừng vì chạm giới hạn số vòng gọi tool.")

user_text = st.chat_input("Nhập yêu cầu (vd: 'Tweet mới nhất của Sam Altman là gì?')")

if user_text:
    with st.chat_message("user"):
        st.write(user_text)

    history = st.session_state["history"]
    messages = [
        {"role": "system", "content": st.session_state["_system_prompt"]},
        *trim_history(history, st.session_state["_history_window"]),
        {"role": "user", "content": user_text},
    ]

    st.session_state["turn_index"] += 1
    turn_record: dict = {
        "turn_index": st.session_state["turn_index"],
        "started_at": now_iso(),
        "user": user_text,
        "status": "started",
        "assistant_text": None,
        "rounds": [],
        "tool_events": [],
    }

    with st.chat_message("assistant"):
        with st.spinner("Agent đang xử lý..."):
            try:
                result = run_model_tool_loop(
                    provider=st.session_state["_provider"],
                    messages=messages,
                    tools=st.session_state["_openai_tools"],
                    model=st.session_state["_model"],
                    max_tool_rounds=st.session_state["_max_tool_rounds"],
                )
                turn_record.update(result)
                assistant_text = result["assistant_text"]
                history.append({"role": "user", "content": user_text})
                history.append({"role": "assistant", "content": assistant_text})
            except Exception as exc:
                assistant_text = f"Lỗi: {type(exc).__name__}: {exc}"
                turn_record.update({"status": "provider_error", "error": assistant_text})

        st.write(assistant_text)
        render_tool_events(turn_record.get("tool_events") or [])
        if turn_record.get("status") == "waiting_for_user":
            st.info("Agent đang chờ bạn trả lời (clarify) — nhập câu trả lời ở ô chat bên dưới.")
        elif turn_record.get("status") == "provider_error":
            st.error(turn_record.get("error"))
        elif turn_record.get("status") == "max_tool_rounds":
            st.warning("Agent dừng vì chạm giới hạn số vòng gọi tool.")

    turn_record["ended_at"] = now_iso()
    st.session_state["turns"].append(turn_record)
    st.session_state["history"] = history

    transcript = {
        "transcript_id": st.session_state["transcript_id"],
        **st.session_state["_artifact_version_dict"],
        "provider": st.session_state["_provider_name"],
        "model": st.session_state["_model"],
        "system_prompt": st.session_state["_system_prompt_path"],
        "tools": st.session_state["_tools_path"],
        "history_window": st.session_state["_history_window"],
        "max_tool_rounds": st.session_state["_max_tool_rounds"],
        "created_at": st.session_state["turns"][0]["started_at"],
        "turns": st.session_state["turns"],
    }
    write_transcript(Path(st.session_state["transcript_path"]), transcript)

st.divider()
if st.session_state.get("turns"):
    transcript_text = json.dumps(
        {
            "transcript_id": st.session_state["transcript_id"],
            **st.session_state["_artifact_version_dict"],
            "provider": st.session_state["_provider_name"],
            "model": st.session_state["_model"],
            "turns": st.session_state["turns"],
        },
        ensure_ascii=False,
        indent=2,
        default=str,
    )
    st.download_button(
        "⬇️ Tải transcript JSON",
        data=transcript_text,
        file_name=f"{st.session_state['transcript_id']}.transcript.json",
        mime="application/json",
    )
    st.caption(f"Transcript cũng được tự lưu tại: `{st.session_state['transcript_path']}`")
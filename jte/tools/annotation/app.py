from typing import List, Tuple
from dataclasses import dataclass

import streamlit as st
from ja_timex import TimexParser
from ja_timex.tag import TIMEX

from counter import Counter

TYPES = ["DATE", "TIME", "DURATION", "SET"]


def timex3_highlight(text: str, timexes: List[TIMEX]) -> str:
    for timex in timexes[::-1]:
        start, end = timex.span
        text = text[:start] + " **" + text[start:end] + "** " + text[end:]
    return text


@dataclass
class EmptyTIMEX:
    tid: str = ""
    type: str = ""
    value: str = ""
    text: str = ""
    span: Tuple[int, int] = (0, 0)

    def to_tag(self):
        return f"<TIMEX3 text={self.text}>"


@dataclass
class Storage:
    text: str
    timexes: List[TIMEX]


def add_empty_timex(new_timex_text=""):
    new_timex_text = new_timex_text.strip()

    if new_timex_text in st.session_state.results[st.session_state.counter.index].text:
        start_i = st.session_state.results[st.session_state.counter.index].text.index(new_timex_text)
        end_id = start_i + len(new_timex_text)

        new_timex = EmptyTIMEX(text=new_timex_text, span=(start_i, end_id))
        st.session_state.results[st.session_state.counter.index].timexes.append(new_timex)
    else:
        st.session_state.results[st.session_state.counter.index].timexes.append(
            EmptyTIMEX(
                text=new_timex_text,
            )
        )


def type_select_box(value, key):
    if value:
        return st.selectbox("TIMEX3 types", TYPES, index=TYPES.index(value), key=key, help="ほげほげ")
    else:
        return st.selectbox("TIMEX3 types", TYPES, key=key)


# initialize
if "counter" not in st.session_state:
    st.session_state.counter = Counter()
if "results" not in st.session_state:
    st.session_state.results = {}

timex_parser = TimexParser()

st.sidebar.header("TIMEX3 Annotator")
st.sidebar.text_area("input texts", "", key="input_texts")

if st.session_state["input_texts"]:
    texts = [t for t in st.session_state["input_texts"].split("\n") if t]

    if st.session_state.counter.total is None:
        st.session_state.counter.set_total(len(texts))

    target_text = st.text_area("Correct here if needed", texts[st.session_state.counter.index], key="input_texts")
    timexes = timex_parser.parse(target_text)

    if not st.session_state.results.get(st.session_state.counter.index):
        st.session_state.results[st.session_state.counter.index] = Storage(text=target_text, timexes=timexes)
    elif st.session_state.results[st.session_state.counter.index].text != target_text:
        st.session_state.results[st.session_state.counter.index] = Storage(text=target_text, timexes=timexes)

    highlighted_text = timex3_highlight(target_text, timexes)
    st.sidebar.subheader("Highlighted Text")
    st.sidebar.write(highlighted_text)

    st.subheader("TIMEX3 Tags")
    for i, timex in enumerate(st.session_state.results[st.session_state.counter.index].timexes):
        with st.expander(f"# {i}: " + timex.to_tag()):
            type_select_box(timex.type, key=f"type_{i}")
            st.text_input("value", timex.value, key=f"value_{i}")
            if timex.freq:
                st.text_input("freq", timex.freq, key=f"freq_{i}")
            st.text_input("text", timex.text, key=f"text_{i}")
            st.text_input("span", timex.span, key=f"span_{i}")
            if timex.mod:
                st.text_input("mod", timex.mod, key=f"mod_{i}")
            if timex.quant:
                st.text_input("quant", timex.quant, key=f"quant_{i}")
            st.checkbox("Delete", key=f"delete_{i}")

    st.subheader("Add New TIMEX Tag")
    new_timex_text = st.text_input("text", "")
    st.button("add", on_click=add_empty_timex, args=(new_timex_text,))

    st.subheader("Export TIMEX Tags")
    if st.button("Done!"):
        st.write("export")
        st.write(st.session_state.results[st.session_state.counter.index].text)
        for i, timex in enumerate(st.session_state.results[st.session_state.counter.index].timexes):
            st.write(st.session_state[f"type_{i}"])
            st.write(st.session_state[f"value_{i}"])
            st.write(st.session_state[f"text_{i}"])
            st.write(st.session_state[f"delete_{i}"])


# next and previous
st.subheader("Move to Next Text")
col1, col2 = st.columns(2)
with col1:
    if st.button("< Previous"):
        st.session_state.counter.previous()
with col2:
    if st.button("Next >"):
        st.session_state.counter.next()

# debug
st.sidebar.write(st.session_state.counter.index)

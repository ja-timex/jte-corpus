import json
from typing import List, Tuple
from dataclasses import dataclass

import streamlit as st
from ja_timex import TimexParser
from ja_timex.tag import TIMEX

from counter import Counter

TYPES = ["DATE", "TIME", "DURATION", "SET"]


def timex3_highlight(text: str, timexes: List[TIMEX]) -> str:
    for timex in timexes[::-1]:
        start, end = timex.raw_span
        text = text[:start] + " **" + text[start:end] + "** " + text[end:]
    return text


@dataclass
class EmptyTIMEX:
    tid: str = ""
    type: str = ""
    value: str = ""
    text: str = ""
    freq: str = ""
    quant: str = ""
    mod: str = ""
    range_start: bool = False
    range_end: bool = False
    raw_span: Tuple[int, int] = (0, 0)

    def to_tag(self):
        attributes = []
        if self.tid:
            attributes.append(f'tid="{self.tid}"')
        attributes += [f'type="{self.type}"', f'value="{self.value}"']
        if self.freq:
            attributes.append(f'freq="{self.freq}"')
        if self.quant:
            attributes.append(f'quant="{self.quant}"')
        if self.mod:
            attributes.append(f'mod="{self.mod}"')
        attributes_text = " ".join(attributes)
        tag = f"<TIMEX3 {attributes_text}>{self.text}</TIMEX3>"
        return tag


@dataclass
class Storage:
    text: str
    timexes: List[TIMEX]


def add_empty_timex(new_timex_text=""):
    new_timex_text = new_timex_text.strip()

    if new_timex_text in st.session_state.results[st.session_state.counter.index].text:
        start_i = st.session_state.results[st.session_state.counter.index].text.index(new_timex_text)
        end_id = start_i + len(new_timex_text)

        new_timex = EmptyTIMEX(text=new_timex_text, raw_span=(start_i, end_id))
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
if "input_json" not in st.session_state:
    st.session_state.input_json = []


timex_parser = TimexParser()

st.sidebar.header("TIMEX3 Annotator")
json_file = st.sidebar.file_uploader("Upload json")


if json_file is not None:
    # next and previous
    col1, col2 = st.columns(2)
    with col1:
        if st.button("< Previous"):
            st.session_state.counter.previous()
    with col2:
        if st.button("Next >"):
            st.session_state.counter.next()

    st.session_state.input_json = json.loads(json_file.read())
    texts = [t["body"] for t in st.session_state.input_json if t]

    if st.session_state.counter.total is None:
        st.session_state.counter.set_total(len(texts))

    st.subheader("1. Check and correct if needed")
    st.write(st.session_state.input_json[st.session_state.counter.index]["url"])

    target_text = st.text_area("Input Text", texts[st.session_state.counter.index], key="input_texts")
    timexes = timex_parser.parse(target_text)

    if not st.session_state.results.get(st.session_state.counter.index):
        st.session_state.results[st.session_state.counter.index] = Storage(text=target_text, timexes=timexes)
    elif st.session_state.results[st.session_state.counter.index].text != target_text:
        st.session_state.results[st.session_state.counter.index] = Storage(text=target_text, timexes=timexes)

    highlighted_text = timex3_highlight(target_text, timexes)
    st.sidebar.subheader("Highlighted Text")
    st.sidebar.write(highlighted_text)

    st.subheader("2. Check TIMEX Tags")
    for i, timex in enumerate(st.session_state.results[st.session_state.counter.index].timexes):
        with st.expander(f"# {i}: " + timex.to_tag()):
            type_select_box(timex.type, key=f"type_{i}")
            value_col1, value_col2 = st.columns(2)
            with value_col1:
                st.text_input("value_from_surface", timex.value, key=f"vfs_{i}")
            with value_col2:
                st.text_input("value", timex.value, key=f"value_{i}")
            if timex.freq:
                st.text_input("freq", timex.freq, key=f"freq_{i}")
            st.text_input("text", timex.text, key=f"text_{i}")
            span_col1, span_col2 = st.columns(2)
            with span_col1:
                st.text_input("span_start", timex.raw_span[0], key=f"span_start_{i}")
            with span_col2:
                st.text_input("span_end", timex.raw_span[1], key=f"span_end_{i}")
            if timex.mod:
                st.text_input("mod", timex.mod, key=f"mod_{i}")
            if timex.quant:
                st.text_input("quant", timex.quant, key=f"quant_{i}")
            range_col1, range_col2 = st.columns(2)
            with range_col1:
                st.checkbox("range_start", timex.range_start, key=f"range_start_{i}")
            with range_col2:
                st.checkbox("range_end", timex.range_end, key=f"range_end_{i}")
            st.markdown("---")
            st.checkbox("DELETE", key=f"delete_{i}")

    st.subheader("3. Add New TIMEX Tag")
    new_timex_text = st.text_input("Temporal expression from text", "")
    st.button("add", on_click=add_empty_timex, args=(new_timex_text,))

    st.subheader("4. Export the TIMEX Tags")
    if st.button("Done!"):
        st.write("export")
        st.write(st.session_state.results[st.session_state.counter.index].text)
        for i, timex in enumerate(st.session_state.results[st.session_state.counter.index].timexes):
            st.write(timex.to_tag())

        export_dict = {}
        export_dict["text"] = st.session_state.results[st.session_state.counter.index].text
        export_dict["timexes"] = []

        n_total_timexes = len(st.session_state.results[st.session_state.counter.index].timexes)
        export_timexes = []
        for i in range(n_total_timexes):
            if st.session_state.get(f"delete_{i}"):
                continue

            export_timex = {
                "tid": "",  # fill it later
                "type": st.session_state.get(f"type_{i}", ""),
                "value": st.session_state.get(f"value_{i}", ""),
                "valueFromSurface": st.session_state.get(f"vfs_{i}", ""),
                "text": st.session_state.get(f"text_{i}", ""),
                "freq": st.session_state.get(f"freq_{i}", ""),
                "quant": st.session_state.get(f"quant_{i}", ""),
                "mod": st.session_state.get(f"mod_{i}", ""),
                "span": (int(st.session_state.get(f"span_start_{i}")), int(st.session_state.get(f"span_end_{i}"))),
            }
            export_timexes.append(export_timex)

        export_timexes = sorted(export_timexes, key=lambda x: x["span"][0])
        for i, t in enumerate(export_timexes):
            t["tid"] = f"t{i}"
        export_dict["timexes"] = export_timexes

        st.write(export_dict)

        file_name = st.session_state.input_json[st.session_state.counter.index]["sha1"]
        with open(f"data/output/wikinews/{file_name}.json", "w") as f:
            json.dump(export_dict, f, ensure_ascii=False, indent=4)


# debug
st.sidebar.write(st.session_state.counter.index)

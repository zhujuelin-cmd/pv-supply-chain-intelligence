import streamlit as st

from ui_components import PAGES, setup_page


def main() -> None:
    setup_page()
    with st.sidebar:
        st.markdown("## 光伏研究终端")
        page = st.radio("导航", list(PAGES), label_visibility="collapsed")
        st.divider()
        st.caption("实时数据：扶摇 API + iFinD MCP")
        st.caption("公开快照兜底：2026-10-27")
        st.caption("研究辅助工具，不构成投资建议")
    PAGES[page]()


if __name__ == "__main__":
    main()

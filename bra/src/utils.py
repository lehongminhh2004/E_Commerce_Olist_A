import streamlit as st


def kpi_card(label: str, value, help_text: str | None = None, format_str: str | None = None):
    """
    Hiển thị một KPI đơn giản.
    """
    with st.container():
        st.caption(label)
        if value is None:
            st.markdown("**–**")
        else:
            if format_str:
                st.markdown(f"**{format_str.format(value)}**")
            else:
                st.markdown(f"**{value}**")
        if help_text:
            st.caption(help_text)

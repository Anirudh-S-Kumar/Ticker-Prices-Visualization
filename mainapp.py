from data_gathering import extendTicker
import streamlit as st
import plotly.graph_objs as objs
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import cufflinks as cf
import pandas as pd
import re

st.set_page_config(page_title="Ticker Prices Visualization",
                  page_icon=".\\resources\\pageicon.png")

layout = objs.Layout(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)'
)

def epoch_time(s):
    s = int(s.group(0))
    temp = (datetime.utcfromtimestamp(s).strftime('%b %d %Y'))
    return (temp)


def mysplit(s):
    tail = s.lstrip('0123456789\.')
    head = s[:len(s) - len(tail)]
    return head, tail



def period_morph(period):
    d = {"m" : "minute", "h" : "hour", "d" : "day", "wk" : "week", "mo" : "month", "y" : "year", "ytd" : "Year to date", "max" : "Max"}

    period_number, period_time = mysplit(period)
    if not period_number:
        return d[period_time]
    
    return f"{period_number} {d[period_time]}"




with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


st.title("Ticker Prices Visualization")

st.markdown("""
Made in [`Python`](https://www.python.org/) using
[`pandas`](https://pandas.pydata.org/docs/ "The most popular data analysis library"),
[`cufflinks`](https://github.com/santosjorge/cufflinks "Intergrates plotly and pandas to make plotting graphs really easy"),
[`streamlit`](https://docs.streamlit.io/ "Makes building good looking websites for data visualization using python, a piece of cake"),
[`yahooquery`](https://yahooquery.dpguthrie.com/ "Alternative to the popular yahoo finance api")
[`plotly`](https://plotly.com/python/ "For graphing"),
[`python_dateutil`](https://pypi.org/project/python-dateutil/ "Powerful extension to standard datetime module in python")

""")


tickerin = st.text_input(label="Search",
                         placeholder="eg. Apple, Bitcoin, etc.",
                         help="Enter whatever asset you want to search for here")

def start_end():
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date",
                                value=date.today() - relativedelta(years=3),
                                min_value=date(1990, 1, 1),
                                max_value=date.today(),
                                help="Enter the start date from which you want to view price results")


    with col2:
        end_date = st.date_input("End Date",
                                value=date.today(),
                                min_value=date(1990, 1, 1),
                                max_value=date(2025, 12, 31),
                                help="Enter the end date till which you want to view price results")
    return start_date, end_date

def period():
    period = st.select_slider(label="Period",
                            options=['1d', '5d', '7d', '60d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max'],
                                value="1y",
                                format_func=period_morph,
                                help="Time period for which you want to see ticker prices",
                                )
    return period



option1, option2 = st.columns(2)
ENABLE_STARTEND = False
ENABLE_PERIOD = False


option = st.selectbox("Time Frame Method", options=["Start Date/End Date", "Period"],
             help="""Determine how you want to input the time period for the ticker""")



if option == "Start Date/End Date":
    ENABLE_PERIOD = False
    ENABLE_STARTEND = True
    period = "1y"
else:
    ENABLE_PERIOD = True
    ENABLE_STARTEND = False
    start_date, end_date = None, None

if ENABLE_STARTEND:
    start_date, end_date = start_end()

if ENABLE_PERIOD:
    period = period()





interval = st.select_slider(label="Interval",
                            options=['1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo'],
                            value="1d",
                            format_func=period_morph,
                            help="Time between ticker prices",
                            )


# writing info
def write_columns(ticker):
    col1, col2 = st.columns([1, 3])

    with col1:
        try:
            logo_url = ticker.get_info()[-1]
            assert logo_url != None
            logo = f"""<div class="circular_image">
                        <img src={logo_url} />
                    </div>"""
            st.markdown(logo, unsafe_allow_html=True)
        except AssertionError:
            pass

    with col2:
        name, quote = ticker.get_info()[0], ticker.get_info()[1]
        st.markdown(f"""## {name} ({ticker.symbol})""")
        st.caption(f"{quote}")

    try:
        summary = ticker.get_info()[2]
        assert summary != None
        st.write(summary)
    except AssertionError:
        pass


# data pre-processing
def pre_processing(ticker):


    try:
        if bool(start_date) & bool(end_date):
            assert start_date < end_date, "Error: Start date is greater than end date"

        tickerhist = ticker.history(start=start_date, end=end_date, period=period, interval=interval)
        assert isinstance(tickerhist, pd.DataFrame), "tickerhist not a dataframe"          

        # assert 
        tickerhist = tickerhist.droplevel(level=0)

        if "adjclose" in tickerhist.axes[-1].values:
            tickerhist = tickerhist.drop(columns=["adjclose"])

        tickerhist = tickerhist.drop(columns=["volume"])
        tickerhist = tickerhist[["open", "high", "low", "close"]]
        return tickerhist

    except AssertionError as e:
        if str(e) == "Error: Start date is greater than end date":
            st.error(e)


        if str(e) == "tickerhist not a dataframe":
            temp = tickerhist[ticker.symbol]
            p1 = re.compile(r"^Data doesn't exist for startDate = \d+, endDate = \d+")
            p2 = re.compile(r"^(\w+) data not available for startTime=(\d+) and endTime=(\d+)")
            
            if p1.match(temp):
                p3 = re.compile(r"\d+")
                matches = p3.sub(repl=epoch_time, string=temp)
                matches = matches.replace(",", " to")
                matches = matches.replace("startDate = ", "")
                matches = matches.replace("endDate = ", "")
                st.error(f"Error: {matches}. Consider changing the time frame")

            if p2.match(temp):
                st.error("Error: Time interval too small. Consider increasing it to a higher value or simply 1 day")

        return pd.DataFrame()


# plotting the graph
def plotting(tickerhist):
    st.markdown("### Ticker Prices")
    qf = cf.QuantFig(tickerhist,
                     title=f"{ticker.name} Price Chart",
                     legend='top',
                     name='prices',
                     #  rangeslider=True,
                     theme="solar"
                     )

    fig = qf.iplot(asFigure=True)
    st.plotly_chart(fig)


try:
    ticker = extendTicker(tickerin)
    write_columns(ticker)
    try:
        
        tickerhist = pre_processing(ticker)
        if not tickerhist.empty:
            plotting(tickerhist)
    except AttributeError:
        st.error(
            "Error: Looks like the company has no available data. Did you set the time period properly?")

except KeyError:
    if tickerin:
        st.error(
            "Error: Looks like the search query does not exist. Did you type it properly? ")

footer = """
<div class="footer">
<p>Developed with ❤ by
<a style='display: block; text-align: center;
'href="https://github.com/Anirudh-S-Kumar" target="_blank">Anirudh</a></p>
</div>
"""
st.markdown(footer, unsafe_allow_html=True)

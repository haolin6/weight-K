import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
from datetime import datetime

# === 1. 页面配置 ===
st.set_page_config(page_title="我的体重K线", page_icon="📉")
st.title("📉 体重 K 线记录仪")

# 数据文件路径
FILE_PATH = 'my_weight_data.csv'


# === 2. 数据处理函数 ===
def load_data():
    if not os.path.exists(FILE_PATH):
        # 如果文件不存在，创建一个空的带表头的CSV
        df = pd.DataFrame(columns=['Date', 'Weight'])
        df.to_csv(FILE_PATH, index=False)
        return df

    df = pd.read_csv(FILE_PATH, parse_dates=['Date'])
    df.sort_values('Date', inplace=True)
    return df


def save_data(date, weight):
    df = load_data()
    # 检查该日期是否已存在，如果存在则更新，不存在则追加
    # 将日期转为 Timestamp 进行比较
    date_ts = pd.Timestamp(date)

    if date_ts in df['Date'].values:
        df.loc[df['Date'] == date_ts, 'Weight'] = weight
        st.success(f"已更新 {date} 的体重为 {weight} kg")
    else:
        new_row = pd.DataFrame({'Date': [date_ts], 'Weight': [weight]})
        df = pd.concat([df, new_row], ignore_index=True)
        st.success(f"已添加 {date} 的体重：{weight} kg")

    df.to_csv(FILE_PATH, index=False)


# === 3. 侧边栏：数据录入 ===
with st.sidebar:
    st.header("📝 每日打卡")
    input_date = st.date_input("选择日期", datetime.today())
    input_weight = st.number_input("今日体重 (kg)", min_value=30.0, max_value=200.0, step=0.1, format="%.1f")

    if st.button("提交 / 更新"):
        save_data(input_date, input_weight)
        # 强制刷新页面以显示最新数据
        st.rerun()

# === 4. 主界面：显示图表 ===
df = load_data()

if df.empty:
    st.info("👈 请在侧边栏输入你的第一个体重数据！")
else:
    # --- 这里复用之前的画图逻辑 ---
    # 1. 按7天分组
    start_date = df['Date'].iloc[0]
    df['Week_ID'] = (df['Date'] - start_date).dt.days // 7

    ohlc = df.groupby('Week_ID').agg({
        'Weight': ['first', 'max', 'min', 'last'],
        'Date': 'last'
    })
    ohlc.columns = ['Open', 'High', 'Low', 'Close', 'Date']
    ohlc.set_index('Date', inplace=True)

    # 2. 绘图
    st.subheader("📊 周 K 线走势图")

    # 使用 matplotlib
    fig, ax = plt.subplots(figsize=(10, 6))

    up_color = '#ff5252'
    down_color = '#2e7d32'
    width = 4

    for date, row in ohlc.iterrows():
        open_p, close_p = row['Open'], row['Close']
        high_p, low_p = row['High'], row['Low']

        if close_p < open_p:
            color = down_color
            body_bottom = close_p
            height = open_p - close_p
        else:
            color = up_color
            body_bottom = open_p
            height = close_p - open_p

        if height == 0: height = 0.05

        ax.plot([date, date], [low_p, high_p], color='black', linewidth=1, zorder=1)
        ax.bar(date, height, bottom=body_bottom, width=width, color=color, zorder=2)

    ax.set_ylabel('Weight (kg)')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
    plt.xticks(rotation=45)
    plt.grid(True, linestyle='--', alpha=0.5)

    # 3. 将图表展示在网页上
    st.pyplot(fig)

    # 显示最近的数据表格
    with st.expander("查看详细数据记录"):
        st.dataframe(df.sort_values('Date', ascending=False), use_container_width=True)
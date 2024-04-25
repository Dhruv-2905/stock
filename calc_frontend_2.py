import streamlit as st
from streamlit_extras.stylable_container import stylable_container
import json
import datetime
from os import getcwd, chdir, path

st.markdown("""
    <style>
        .header-text {
            color: #009688;
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .input-container {
            background-color: #f0f0f0;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .input-label {
            font-size: 18px;
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }
        .output-container {
            background-color: #fafafa;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .output-label {
            font-size: 18px;
            font-weight: bold;
            color: #009688;
            margin-bottom: 5px;
        }

        .transaction-container {
            border: 2px solid #009688;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 30px;
            background-color: #f0f0f0;
            animation: spin 10s linear infinite;
            box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.1);
        }
        .column-style {
            background-color: lightblue;
            border: 1px solid blue;
            padding: 10px;
            border-radius: 5px;
        }
    </style>
""", unsafe_allow_html=True)

class BrokerageCalculator:
    def __init__(self, buyPrice, sellPrice, qty):
        chdir(path.dirname(path.abspath(__file__)))
        self.buyPrice = float(buyPrice)
        self.sellPrice = float(sellPrice)
        self.qty = int(qty)
        self.turnover = (self.buyPrice * self.qty) + (self.sellPrice * self.qty)
        self.avgPrice = self.turnover / (self.qty * 2)
        self.order: str = ""
        directory = getcwd()
        self.journalFile = directory + "/journal.json"

    def _getMaxBrokerage(self, brokerage: float) -> float:
        return 40.0 if brokerage > 40.0 else brokerage

    def _getRiskRewardRatio(self, orderType: str, secondLeg: str) -> float:
        secondLeg = float(secondLeg)
        reward: float = 0.0
        risk: float = 0.0
        if orderType.lower() != 'b' and orderType.lower() != 's':
            st.error("Invalid order type.")
        if orderType.lower() == "b":
            risk = self.buyPrice - secondLeg
            reward = self.sellPrice - self.buyPrice
        else:
            risk = secondLeg - self.sellPrice
            reward = self.sellPrice - self.buyPrice

        return reward / risk

    def addOrder(self, orderType: str, secondLeg: str) -> None:
        ratio = self._getRiskRewardRatio(orderType, secondLeg)
        if ratio == 0.0:
            st.error("Something went wrong. Use -h for usage.")
        st.write(f"Reward:Risk ratio: {ratio}")
        now = datetime.datetime.now()
        date = now.strftime("%d-%m-%Y")
        time = now.strftime("%H:%M:%S")

        data = {
                "orderType": self.order,
                "position": orderType.lower(),
                "ratio": ratio,
                "time": time,
                "result": "P" if self.netProfit > 0 else "L",
                "netPL": self.netProfit,
                "quantity": self.qty
                }
        try:
            f = open(self.journalFile, "r")
            jsonD = json.load(f)
            if date not in jsonD:
                jsonD[date] = []
            f.close()
        except FileNotFoundError:
            jsonD = {}
            jsonD[date] = []
            pass

        f = open(self.journalFile, "w")
        jsonD[date].append(data)
        json.dump(jsonD, f, indent=4)

    def intradayEquity(self) -> None:
        self.order = "Intraday"
        brokerage = self.turnover * 0.0002
        brokerage = self._getMaxBrokerage(brokerage)
        sttCharges = self.qty * self.avgPrice * 0.00025
        sebiCharges = self.turnover * 0.000002
        stampCharges = self.qty * self.avgPrice * 0.00003
        exchangeCharges = self.turnover * 0.0000325

        totalCharges = brokerage + sttCharges + sebiCharges + stampCharges + exchangeCharges
        gst = totalCharges * 0.18
        self.netProfit = ((self.sellPrice - self.buyPrice) * self.qty) - (totalCharges + gst)
        pointsToBreakeven = (totalCharges + gst) / self.qty
        st.write(f"Total charges: {(totalCharges + gst)}")
        st.write(f"Points to break even: {pointsToBreakeven}")
        st.write(f"Net profit: {self.netProfit}")

    def deliveryEquity(self, days: int = 0, isCashPlus: bool = False) -> None:
        self.order = "Delivery"
        brokerage = self.turnover * 0.002
        brokerage = self._getMaxBrokerage(brokerage)
        sttCharges = self.qty * self.avgPrice * 0.00025
        sebiCharges = self.turnover * 0.000002
        stampCharges = self.qty * self.avgPrice * 0.00003
        exchangeCharges = self.turnover * 0.0000325
        if isCashPlus:
            self.order = "Delivery (Cash+)"
            interest = (self.turnover * 0.00025) * days
        else:
            interest = 0

        totalCharges = brokerage + sttCharges + sebiCharges + stampCharges + exchangeCharges + interest

        gst = totalCharges * 0.18

        self.netProfit = ((self.sellPrice - self.buyPrice) * self.qty) - (totalCharges + gst)
        pointsToBreakeven = (totalCharges + gst) / self.qty

        st.write(f"Total charges: {(totalCharges + gst)}")
        st.write(f"Points to break even: {pointsToBreakeven}")
        if isCashPlus:
            st.write(f"Total interest for {days} days: {interest}")
        st.write(f"Net profit: {self.netProfit}")

    def options(self) -> None:
        self.order = "Options"
        brokerage = 40.0
        sttCharges = self.qty * self.avgPrice * 0.0005
        sebiCharges = self.turnover * 0.000002
        stampCharges = self.qty * self.avgPrice * 0.00003
        exchangeCharges = self.turnover * 0.00053

        totalCharges = brokerage + sttCharges + sebiCharges + stampCharges + exchangeCharges
        gst = totalCharges * 0.18

        self.netProfit = ((self.sellPrice - self.buyPrice) * self.qty) - (totalCharges + gst)
        pointsToBreakeven = (totalCharges + gst) / self.qty

        st.write(f"Total charges: {(totalCharges + gst)}")
        st.write(f"Points to break even: {pointsToBreakeven}")
        st.write(f"Net profit: {self.netProfit}")

def main():
    st.title("Brokerage Calculator")

    # with st.container():
    #     st.markdown("<div class='transaction-container'>", unsafe_allow_html=True)
    #     with st.columns(4):
    #         with st.expander("Intraday"):
    #             buy_price_1 = st.number_input("Enter Buy Price", key="buy_price_1")
    #             sell_price_1 = st.number_input("Enter Sell Price", key="sell_price_1")
    #             qty_1 = st.number_input("Enter Quantity", step=1, value=1, key="qty_1")
    #             calc_1 = BrokerageCalculator(buy_price_1, sell_price_1, qty_1)
    #             calc_1.intradayEquity()
    #         with st.expander("Delivery"):
    #             buy_price_2 = st.number_input("Enter Buy Price", key="buy_price_2")
    #             sell_price_2 = st.number_input("Enter Sell Price", key="sell_price_2")
    #             qty_2 = st.number_input("Enter Quantity", step=1, value=1, key="qty_2")
    #             calc_2 = BrokerageCalculator(buy_price_2, sell_price_2, qty_2)
    #             calc_2.deliveryEquity()
    #         with st.expander("Delivery (Cash+)"):
    #             buy_price_3 = st.number_input("Enter Buy Price", key="buy_price_3")
    #             sell_price_3 = st.number_input("Enter Sell Price", key="sell_price_3")
    #             qty_3 = st.number_input("Enter Quantity", step=1, value=1, key="qty_3")
    #             days_3 = st.number_input("Enter Number of Days", step=1, value=1, key="days_3")
    #             calc_3 = BrokerageCalculator(buy_price_3, sell_price_3, qty_3)
    #             calc_3.deliveryEquity(days=days_3, isCashPlus=True)
    #         with st.expander("Options"):
    #             buy_price_4 = st.number_input("Enter Buy Price", key="buy_price_4")
    #             sell_price_4 = st.number_input("Enter Sell Price", key="sell_price_4")
    #             qty_4 = st.number_input("Enter Quantity", step=1, value=1, key="qty_4")
    #             calc_4 = BrokerageCalculator(buy_price_4, sell_price_4, qty_4)
    #             calc_4.options()
    #     st.markdown("</div>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)

    # with col1:
    #     st.markdown("<div class='transaction-container'>", unsafe_allow_html=True)
    #     with st.expander("Intraday"):
    #         buy_price_1 = st.number_input("Enter Buy Price", key="buy_price_1")
    #         sell_price_1 = st.number_input("Enter Sell Price", key="sell_price_1")
    #         qty_1 = st.number_input("Enter Quantity", step=1, value=1, key="qty_1")
    #         # Add your calculation logic here
    #     st.markdown("</div>", unsafe_allow_html=True)

    # with col2:
    #     st.markdown("<div class='transaction-container'>", unsafe_allow_html=True)
    #     with st.expander("Delivery"):
    #         buy_price_2 = st.number_input("Enter Buy Price", key="buy_price_2")
    #         sell_price_2 = st.number_input("Enter Sell Price", key="sell_price_2")
    #         qty_2 = st.number_input("Enter Quantity", step=1, value=1, key="qty_2")
    #         # Add your calculation logic here
    #     st.markdown("</div>", unsafe_allow_html=True)

    # with col3:
    #     st.markdown("<div class='transaction-container'>", unsafe_allow_html=True)
    #     with st.expander("Delivery (Cash+)"):
    #         buy_price_3 = st.number_input("Enter Buy Price", key="buy_price_3")
    #         sell_price_3 = st.number_input("Enter Sell Price", key="sell_price_3")
    #         qty_3 = st.number_input("Enter Quantity", step=1, value=1, key="qty_3")
    #         # Add your calculation logic here
    #     st.markdown("</div>", unsafe_allow_html=True)

    # with col4:
    #     st.markdown("<div class='transaction-container'>", unsafe_allow_html=True)
    #     with st.expander("Options"):
    #         buy_price_4 = st.number_input("Enter Buy Price", key="buy_price_4")
    #         sell_price_4 = st.number_input("Enter Sell Price", key="sell_price_4")
    #         qty_4 = st.number_input("Enter Quantity", step=1, value=1, key="qty_4")
    #         # Add your calculation logic here
    #     st.markdown("</div>", unsafe_allow_html=True)
    
    
    
    
    
    with col1:
        with stylable_container(
            key='column1',
            css_styles=""" 
            {
                
                border: 0.25px solid #009688;
                border-radius: 10px;
                padding: 0px;
                margin-bottom: 30px;
                background-color: #f0f0f0;
                animation: spin 10s linear infinite;
                box-shadow: 4px 4px 10px rgba(0, 0, 0, 0.1);
            }
            """,
            ):
            with st.expander("Intraday", expanded=False,):
                buy_price_1 = st.number_input("Enter Buy Price", key="buy_price_1")
                sell_price_1 = st.number_input("Enter Sell Price", key="sell_price_1")
                qty_1 = st.number_input("Enter Quantity", step=1, value=1, key="qty_1")
                if st.button("Calculate 1", key="calculate_1"):
                    calc_1 = BrokerageCalculator(buy_price_1, sell_price_1, qty_1)
                    calc_1.intradayEquity()

    with col2:
        #st.markdown("<div class='transaction-container'>", unsafe_allow_html=True)
        with st.expander("Delivery"):
            buy_price_2 = st.number_input("Enter Buy Price", key="buy_price_2")
            sell_price_2 = st.number_input("Enter Sell Price", key="sell_price_2")
            qty_2 = st.number_input("Enter Quantity", step=1, value=1, key="qty_2")
            if st.button("Calculate 2", key="calculate_2"):
                calc_2 = BrokerageCalculator(buy_price_2,sell_price_2,qty_2)
                calc_2.deliveryEquity()
        st.markdown("</div>", unsafe_allow_html=True)

    with col3:
        #st.markdown("<div class='transaction-container'>", unsafe_allow_html=True)
        with st.expander("Delivery (Cash+)"):
            buy_price_3 = st.number_input("Enter Buy Price", key="buy_price_3")
            sell_price_3 = st.number_input("Enter Sell Price", key="sell_price_3")
            qty_3 = st.number_input("Enter Quantity", step=1, value=1, key="qty_3")
            days_3 = st.number_input("Enter Number of Days", step=1, value=1, key="days_3")
            if st.button("Calculate 3", key="calculate_3"):
                calc_3 = BrokerageCalculator(buy_price_3, sell_price_3, qty_3)
                calc_3.deliveryEquity(days= days_3, isCashPlus=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col4:
        #st.markdown("<div class='transaction-container'>", unsafe_allow_html=True)
        with st.expander("Options"):

            buy_price_4 = st.number_input("Enter Buy Price", key="buy_price_4")
            sell_price_4 = st.number_input("Enter Sell Price", key="sell_price_4")
            qty_4 = st.number_input("Enter Quantity", step=1, value=1, key="qty_4")
            if st.button("Calculate 4", key="calculate_4"):
                calc_4 = BrokerageCalculator(buy_price_4, sell_price_4, qty_4)
                calc_4.options()
                
        st.markdown("</div>", unsafe_allow_html=True)
    
    
    
    

    # with st.expander("Intraday", expanded=False):
    #     st.markdown("<div class='transaction-container'>", unsafe_allow_html=True)
    #     buy_price_1 = st.number_input("Enter Buy Price", key="buy_price_1")
    #     sell_price_1 = st.number_input("Enter Sell Price", key="sell_price_1")
    #     qty_1 = st.number_input("Enter Quantity", step=1, value=1, key="qty_1")
    #     if st.button("Calculate 1", key="calculate_1"):
    #         calc_1 = BrokerageCalculator(buy_price_1, sell_price_1, qty_1)
    #         calc_1.intradayEquity()
    #     st.markdown("</div>", unsafe_allow_html=True)

    # with st.expander("Delivery", expanded=False):
    #     st.markdown("<div class='transaction-column'>", unsafe_allow_html=True)
    #     buy_price_2 = st.number_input("Enter Buy Price", key="buy_price_2")
    #     sell_price_2 = st.number_input("Enter Sell Price", key="sell_price_2")
    #     qty_2 = st.number_input("Enter Quantity", step=1, value=1, key="qty_2")
    #     if st.button("Calculate 2", key="calculate_2"):
    #         st.write("Calculate delivery logic here")
    #     st.markdown("</div>", unsafe_allow_html=True)

    # with st.expander("Delivery (Cash+)", expanded=False):
    #     st.markdown("<div class='transaction-column'>", unsafe_allow_html=True)
    #     buy_price_3 = st.number_input("Enter Buy Price", key="buy_price_3")
    #     sell_price_3 = st.number_input("Enter Sell Price", key="sell_price_3")
    #     qty_3 = st.number_input("Enter Quantity", step=1, value=1, key="qty_3")
    #     if st.button("Calculate 3", key="calculate_3"):
    #         st.write("Calculate delivery (Cash+) logic here")
    #     st.markdown("</div>", unsafe_allow_html=True)

    # with st.expander("Options", expanded=False):
    #     st.markdown("<div class='transaction-column'>", unsafe_allow_html=True)
    #     buy_price_4 = st.number_input("Enter Buy Price", key="buy_price_4")
    #     sell_price_4 = st.number_input("Enter Sell Price", key="sell_price_4")
    #     qty_4 = st.number_input("Enter Quantity", step=1, value=1, key="qty_4")
    #     if st.button("Calculate 4", key="calculate_4"):
    #         calc_4 = BrokerageCalculator(buy_price_4, sell_price_4, qty_4)
    #         calc_4.options()
    #     st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
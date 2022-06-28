from flask import Flask, Response, request
from chat_downloader import ChatDownloader
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.utils import ChromeType
from bs4 import BeautifulSoup
from currency_converter_with_rate import currency
import google_currency
import wsgiserver
import time
import json
app = Flask(__name__)


def convert(currenc, amount):
    converted = False
    while(converted == False):
        converting = google_currency.convert(currenc,'usd',float(amount))
        newDict = json.loads(converting)
        if (newDict['converted']):
            newDict['previous_amount'] = amount
            newDict['amount'] = float(newDict['amount'])
            return newDict

@app.route('/superchats')
def catch_all():
    id = request.args['id']

    url = 'https://www.youtube.com/watch?v=' + id
    try:
        chat = ChatDownloader().get_chat(url, message_types=['paid_message', "paid_sticker"])
    except:
        return {"superChatsTotal": 0, "superChats": [], "totalAmount": 0, "status": False}
    count = 0
    total = []
    totalconverted = []
    totalAmount = 0

    for message in chat:                        # iterate over messages
        count += 1
        total.append(message['money'])

    for tot in total:
        converted = convert(tot['currency'],tot['amount'])
        totalAmount += converted["amount"]
        totalconverted.append(converted) 
    return {"superChatsTotal": count, "superChats": totalconverted, "totalAmount": round(totalAmount,2), "status": True}

@app.route('/superthanks')
def ScrapComment():
    start_time = time.time()
    id = request.args['id']

    url = 'https://www.youtube.com/watch?v=' + id
    option = webdriver.ChromeOptions()
    option.add_argument("--no-sandbox"); 
    option.add_argument("--headless");
    option.add_argument("disable-infobars"); 
    option.add_argument("--disable-extensions");
    option.add_argument("--remote-debugging-port=9222"); 
    option.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install(), options=option)
    driver.set_window_size(1080, 768)
    driver.get(url)
    prev_h = 0
    while True:
        height = driver.execute_script("""
                function getActualHeight() {
                    return Math.max(
                        Math.max(document.body.scrollHeight,
                                 document.documentElement.scrollHeight),
                        Math.max(document.body.offsetHeight,
                                 document.documentElement.offsetHeight),
                        Math.max(document.body.clientHeight,
                                 document.documentElement.clientHeight)
                    );
                }
                return getActualHeight();
            """)
        driver.execute_script(f"window.scrollTo({prev_h},{prev_h + 200})")
        # fix the time sleep value according to your network connection
        time.sleep(0.2)
        prev_h += 200
        if prev_h >= height:
            break
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()
    title_text_div = soup.select_one('#container h1')
    title = title_text_div and title_text_div.text
    comment_div = soup.select(
        "#content #paid-comment-chip #comment-chip-container #comment-chip-price")
    comment_list = [x.get_text() for x in comment_div if len(x.text) > 1]

    totalAmount = 0
    total = []
    print(comment_list)
    for comment in comment_list:
        splited = comment.split()
    
        if(len(splited) == 2):
            converted = convert(splited[0], splited[1])
            totalAmount += converted["amount"]
            total.append(converted)
            continue

        if(splited[0].startswith('$')):
            amount = splited[0].strip('$')
            converted = convert('USD', amount)
            totalAmount += converted["amount"]
            total.append(converted)
            continue

        splitted_twice = comment.split("$")
        currenc = splitted_twice[0].split()[0]
        amount = splitted_twice[1].split()[0]
        if(currenc == 'CA'):
            converted = convert("CAD", amount)
            totalAmount += converted["amount"]
            total.append(converted)
            continue
        elif(currenc == 'A'):
            currenc = 'AUD'
        elif(currenc == 'R'):
            currenc = 'BRL'
        elif(currenc == 'MX'):
            currenc = 'MXN'
        elif(currenc == 'HK'):
            currenc = 'HKD'
        converted = convert(currenc, amount)
        totalAmount += converted["amount"]
        total.append(converted)
    print("--- %s seconds ---" % (time.time() - start_time))
    return {"superThanksTotal": len(comment_list), "superThanks": total, "totalAmount": totalAmount}

@app.route('/')
def index():
    return {"test": "hello"}

if __name__ == "__main__":
    # Setting debug to True enables debug output. This line should be
    # removed before deploying a production app.
    server = wsgiserver.WSGIServer(app, host='0.0.0.0',port=5001)
    server.start()
    # app.run(debug=True)

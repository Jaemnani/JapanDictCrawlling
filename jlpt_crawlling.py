from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import numpy as np

AllClassFlag = True
# chrome headless mode
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")

if AllClassFlag:
    total_data = np.array([["japanese", "Hanmoon", "Level", "Mean"]])
else:
    total_data = np.array([["japanese", "Hanmoon", "Level", "Class", "Mean"]])
category = ["noun", "verb", "adjective", "adverb", "measurement", "phrases", "conjunction", "numeral", "pronoun", "interjection" ]
level = ["1","2","3","4","5"]
page = 1


for lIdx, lVal in enumerate(level):
    
    for cIdx, cVal in enumerate(category):
        page = 1
        while True:
            # open chrome driver
            driver = webdriver.Chrome(options=chrome_options)

            # url = "https://ja.dict.naver.com/#/jlpt/list?level=1&part=allClass&page=1"
            if AllClassFlag:
                url = "https://ja.dict.naver.com/#/jlpt/list?level="+lVal+"&part=allClass&page="+str(page)
            else:
                url = "https://ja.dict.naver.com/#/jlpt/list?level="+lVal+"&part="+cVal+"&page="+str(page)
            driver.get(url)

            tmp = driver.find_element(By.CSS_SELECTOR, '#my_jlpt_list_template')
            page_text = tmp.text
            page_source = page_text.split("\n")

            char_count = len(page_source)//3
            print(lVal,"lev, [", cVal," ]", page,"page, cnt :", char_count)
            # print(page_source)
            if char_count == 0:
                break
            levels = np.array( [lVal] * char_count )
            page += 1
            # jp = page_source[0::3]
            try:
                jp = []
                anounce = []
                for jv in page_source[0::3]:
                    if " " in jv:
                        jp.append(jv.split(" ")[0])
                        anounce.append(jv.split(" ")[1].replace("[","").replace("]",""))
                    else:
                        jp.append(jv)
                        anounce.append("")
                jp = np.array(jp)
                anounce = np.array(anounce)

                # jp = np.array( [a.split(" ") for a in page_source[0::3]] )
                # anounce = np.array( [a.replace("]","").replace("[", "") for a in list(jp[:, 1])] )
                # jp = jp[:,0]
                
                # jp_anounce = [a.split(" ") for a in jp]
                means = page_source[2::3]

                if AllClassFlag:
                    mean = np.array(means)
                    page_result = np.concatenate([jp, anounce, levels, mean]).reshape(4,-1).T
                else:
                    classes = []
                    mean = []
                    for m in means:
                        for i, c in enumerate(m):
                            if c == " ":
                                first_space_index = i
                                classes.append(m[:i])
                                mean.append(m[i+1:])
                                break
                    classes = np.array(classes)
                    mean = np.array(mean)
                    page_result = np.concatenate([jp, anounce, levels, classes, mean]).reshape(5,-1).T
                total_data = np.concatenate([total_data, page_result])
                print(page_result )
            except Exception as e:
                print(e)
                print("ERROR ERROR !!!!")
        if AllClassFlag:
            break
    #         break
    #     break
    # break
driver.quit()
import pandas as pd
df = pd.DataFrame(total_data)
df.to_excel("./naver_jlpt_words_allclass.xlsx", index=False)

print("done")


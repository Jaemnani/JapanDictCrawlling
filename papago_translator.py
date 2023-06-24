import os
import sys
import urllib.request
import numpy as np
import pandas as pd
from tqdm import tqdm
from time import time
from time import sleep

excel_file = pd.read_excel("c:/Users/Jaemoon/Synology_Jaemnani/SynologyDrive/study/software/naver_jlpt_words.xlsx")
hiragana = excel_file[0]
hanmoon = excel_file[1]
level = excel_file[2]
classes = excel_file[3]
means = excel_file[4]
means_np = means.to_numpy()[1:]

set_hiragana = hiragana[1:].to_numpy()
set_mean = means[1:].to_numpy()

client_id = "xxxx" # 개발자센터에서 발급받은 Client ID 값
client_secret = "xxxx" # 개발자센터에서 발급받은 Client Secret 값

total_targets = np.array(["ja", "ko", "en","zh-CN","zh-TW","es","fr","de","ru","pt","it","vi","th","id","hi"])
targets = ["zh-CN","zh-TW","es","fr","de","ru","pt","it","vi","th","id","hi"]

save_path = "allclass_translator.xlsx"
save_file = pd.read_excel(save_path)


source_file_length = len(excel_file) -1
save_file_length = len(save_file)
if save_file_length > 1:
    total_targets = save_file.to_numpy()
    seq = save_file_length
    set_hiragana = set_hiragana[seq:]
    set_mean = set_mean[seq:]
else :
    seq = 0

# 한국어 = ko # 영어 = en # 일본어 = ja # 중국어(간체) = zh-CN # 중국어(번체) = zh_TW # 스페인어 = es
# 프랑스어 = fr # 독일어 = de # 러시아어 = ru # 포르투갈어 = pt # 이탈리아어 = it # 베트남어 = vi
# 태국어 = th # 인도네시아어 = id # 힌디어 = hi
url = "https://openapi.naver.com/v1/papago/n2mt"
request = urllib.request.Request(url)
request.add_header("X-Naver-Client-Id",client_id)
request.add_header("X-Naver-Client-Secret",client_secret)

for i, m in enumerate(tqdm(means_np[seq:])):
    encText = urllib.parse.quote( m )
    # print("target is ", m)
    data = "source=ko&target=en&text=" + encText
    try:
        response = urllib.request.urlopen(request, data=data.encode("utf-8"))
        rescode = response.getcode()
        result = []
        result.append(set_hiragana[i])
        result.append(set_mean[i])

        if(rescode == 200):
            response_body = response.read()
            # print(response_body.decode('utf-8'))
            en_result = response_body.decode("utf-8").split("translatedText\":\"")[1].split("\",\"")[0]
            result.append(en_result)
            encText = urllib.parse.quote(en_result)
            for t in targets:
                data = "source=en&target="+t+"&text=" + encText
                response = urllib.request.urlopen(request, data=data.encode("utf-8"))
                rescode = response.getcode()
            
                if(rescode==200):
                    response_body = response.read()
                    sub_res = response_body.decode("utf-8").split("translatedText\":\"")[1].split("\",\"")[0]
                    result.append(sub_res)            
                else:
                    result.append("")
        else:
            print("pass")
            result = ["","","","","","","","","","","","","","",""]
    except:
        print("API Linit OVER? ", i,"th word")
        break
    total_targets = np.vstack((total_targets, np.array(result)))    
    sleep(1)
    # print(result)

if total_targets.ndim > 1:
    df = pd.DataFrame(total_targets)
    df.to_excel("./allclass_translator.xlsx", index=False)
    # df.to_excel("./allclass_translator"+str(int(time()))+".xlsx", index=False)
else:
    print("didnt append datas.")
print("done")
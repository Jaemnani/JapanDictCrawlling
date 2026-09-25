"""네이버 JLPT 목록 페이지 구조를 자동으로 조사해서 naver_site_info.json 으로 저장.

  python discover_naver.py

크롤러를 다시 짜는 데 필요한 정보(품사 필터별 part= 값, 목록 데이터를 받아오는 API 주소와 응답 샘플,
목록 항목 HTML)를 모은다. 로그인 정보·쿠키는 저장하지 않는다.
"""
import json
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

URL = "https://ja.dict.naver.com/#/jlpt/list?level=1&part=allClass&page=1"
LIST_SELECTOR = "#my_jlpt_list_template"
OUT = "naver_site_info.json"


def wait_list(driver, timeout=15):
    WebDriverWait(driver, timeout).until(
        lambda d: d.find_elements(By.CSS_SELECTOR, LIST_SELECTOR)
        and d.find_element(By.CSS_SELECTOR, LIST_SELECTOR).text.strip()
    )
    time.sleep(1)


def api_calls(driver):
    """performance 로그에서 XHR/Fetch 요청 URL 과 응답 앞부분을 뽑는다."""
    calls = []
    for entry in driver.get_log("performance"):
        msg = json.loads(entry["message"])["message"]
        if msg.get("method") != "Network.responseReceived":
            continue
        params = msg["params"]
        if params.get("type") not in ("XHR", "Fetch"):
            continue
        url = params["response"]["url"]
        try:
            body = driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": params["requestId"]})["body"]
        except Exception as e:  # 응답이 이미 버려진 경우 등
            body = f"<본문 없음: {e.__class__.__name__}>"
        calls.append({"url": url, "body_head": body[:3000]})
    return calls


def main():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    driver = webdriver.Chrome(options=opts)
    info = {}
    try:
        driver.get(URL)
        wait_list(driver)

        info["list_text_head"] = driver.find_element(By.CSS_SELECTOR, LIST_SELECTOR).text[:1500]
        info["list_html_head"] = driver.find_element(By.CSS_SELECTOR, LIST_SELECTOR).get_attribute("outerHTML")[:6000]
        info["api_calls_page1"] = api_calls(driver)

        radios = []
        for r in driver.find_elements(By.CSS_SELECTOR, "input[type=radio]"):
            label = driver.execute_script(
                "const r=arguments[0]; const l=r.closest('label') || (r.id && document.querySelector(`label[for='${r.id}']`)) || r.parentElement;"
                "return l ? l.innerText.trim() : '';", r)
            radios.append({"name": r.get_attribute("name"), "value": r.get_attribute("value"),
                           "id": r.get_attribute("id"), "label": label})
        info["radios"] = radios

        # 품사 필터를 하나씩 눌러서 바뀐 URL 기록 (SPA 가 다시 그릴 수 있으니 매번 새로 찾는다)
        parts = []
        for i, r in enumerate(radios):
            if not r["label"] or r["label"].endswith("급"):
                continue
            try:
                el = driver.find_elements(By.CSS_SELECTOR, "input[type=radio]")[i]
                driver.execute_script("arguments[0].click();", el)
                time.sleep(2)
                parts.append({"label": r["label"], "url": driver.current_url})
            except Exception as e:
                parts.append({"label": r["label"], "error": repr(e)[:200]})
        info["part_urls"] = parts
        info["api_calls_after_clicks"] = [c["url"] for c in api_calls(driver)]
    except Exception as e:
        info["error"] = repr(e)[:500]
    finally:
        driver.quit()

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)
    print(f"{OUT} 저장 완료. 이 파일을 채팅에 첨부하거나 내용을 붙여넣어 주세요.")


if __name__ == "__main__":
    main()

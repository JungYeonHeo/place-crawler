from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import requests
import pandas as pd
import time
from openpyxl import Workbook

# 드라이버 생성
options = Options()
options.add_experimental_option('detach', True)
options.add_experimental_option('excludeSwitches', ['enable-logging'])
driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
driver.get(url='https://map.kakao.com/?nil_profile=title&nil_src=local')
time.sleep(1)

last_page = 34
place_base_link = 'https://place.map.kakao.com/main/v/'
search_type_list = ['카페', '식당', '술집']
gu_list = ['강남구','서대문구','은평구','종로구','중구','용산구','성동구','광진구',
          '동대문구','성북구','강북구','도봉구','노원구','중랑구','강동구','송파구',
          '마포구','서초구','관악구','동작구','영등포구','금천구','구로구','양천구','강서구']

for type in search_type_list:
  file_name = f'카카오맵_서울_{type}.xlsx'
  workbook = pd.ExcelWriter(file_name, engine='openpyxl') 
  workbook.book.create_sheet("")  
  workbook.close()
  
  for gu in gu_list:
    try:
      # 장소 검색
      search_keyword = f'서울 {gu} {type}'
      search_box = driver.find_element(By.XPATH, '//*[@id="search.keyword.query"]')
      search_box.clear()
      search_box.send_keys(search_keyword) 
      search_box.send_keys(Keys.RETURN)
      time.sleep(3)
      
      # 장소명 -(으)로 재검색 클릭
      research = driver.find_element(By.XPATH, '//*[@id="info.searchHeader.message"]/div/div[2]/a')
      driver.execute_script('arguments[0].click();', research)
      time.sleep(3) 

      # 장소 더보기 링크 클릭
      more = driver.find_element(By.XPATH, '//*[@id="info.search.place.more"]')
      driver.execute_script('arguments[0].click();', more)
      time.sleep(3) 

      # 데이터 수집
      df_list = []    
      page = 1
      
      while True:
        print(f'==== {search_keyword} page.{page} 수집 ====')
        place_list = driver.find_elements(By.XPATH, '//*[@id="info.search.place.list"]/li')
        for place in place_list: 
          # 장소 상세보기 링크
          place_detail_link = place.find_element(By.CSS_SELECTOR, 'div.info_item > div.contact.clickArea > a.moreview').get_attribute('href')
          
          # 실제 링크 
          place_id = place_detail_link.split('/')[-1]
          place_api_link = f'{place_base_link}{place_id}'
          
          response = requests.get(place_api_link)
          place_info = response.json()
          
          if place_info['isExist'] == False:
            print(f'==== 링크 에러: {place_api_link} ====')
            continue
          
          df = pd.json_normalize(place_info['basicInfo']) 
          df_list.append(df)
          print(df)
          
        if page % 5 == 0:
          print('==== next 버튼 ====')
          page_next_btn = driver.find_element(By.XPATH, '//*[@id="info.search.page.next"]')
          driver.execute_script('arguments[0].click();', page_next_btn)
          time.sleep(3)
        
        if page == last_page: # TODO: next 버튼 비활성화면 종료하기로 수정
          print(f'==== {page} page 수집완료 ====')
          break
        
        page += 1
        page_btn = driver.find_element(By.XPATH, f'//*[@id="info.search.page.no{page % 5 or 5}"]')
        driver.execute_script('arguments[0].click();', page_btn)
        time.sleep(3)
          
      # df -> excel 저장
      with pd.ExcelWriter(file_name, engine='openpyxl', mode='a') as writer: 
        pd.concat(df_list, ignore_index=True).to_excel(writer, sheet_name=gu, index=False)
        
    except Exception as e:
      print(e)
      pass
